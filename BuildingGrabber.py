
import json
import math
import sys
import time
from functools import partial
from pathlib import Path

import click

import geojson
import requests
from pyproj import Proj, transform
from shapely.geometry import (LineString, MultiPoint, MultiPolygon, Point,
                              mapping, shape)
from shapely.ops import transform

class BuildingGrabber:
    def __init__(self, api_key, radius=50):
        self.api_key = api_key
        self.radius = radius

    def estimate(self, in_file):
        start = time.time()

        in_file_path = Path('/data/').joinpath(in_file)

        points = self.get_points(in_file_path)
        points = self.filter_quadratic(points, self.by_distance)

        building_ids = self.get_building_ids(points, self.api_key)

        print(f"Total number of buildings returned: {len(building_ids)}")
        
        elapsed = time.time() - start
        print(f"Elapsed time: {elapsed:.2f}s")
        
    def extract(self, in_file, out_file, footprint_type, attribute):
        start = time.time()

        in_file_path = Path('/data/').joinpath(in_file)
        out_file_path = Path('/data/').joinpath(out_file)

        points = self.get_points(in_file_path)
        points = self.filter_quadratic(points, self.by_distance)

        building_ids = self.get_building_ids(points, self.api_key)

        building_features = self.get_building_footprints(building_ids, self.api_key, footprint_type == '2d', attribute)

        fc = geojson.FeatureCollection(building_features)
        gj = geojson.dumps(fc) 
        print(f"Writing {out_file}")
        with open(out_file_path, 'w') as outfile:
            outfile.write(gj)
        elapsed = time.time() - start
        print(f"Elapsed time: {elapsed:.2f}s")
    

    def get_points(self, in_file):
        with open(in_file) as gj_file:
            gj = geojson.load(gj_file)

        return self.get_query_points_from_geojson_features(gj.features)

    def get_building_ids(self, points, api_key):
        buildings = []
        counter = 1
        print(f"Total Filtered Points: {len(points)}")
        for point in points:
            print(f"{counter} out of {len(points)} points processed.", end='\r', flush=True)
            counter += 1
            for building_id in self.get_building_ids_for_point(point, api_key):
                if building_id not in buildings:
                    buildings.append(building_id)
        return buildings

    def get_points_between_points(self, origin_points):
        x = Point(origin_points[0])
        y = Point(origin_points[1])
        mod_radius = self.radius / 100000
        dist = x.distance(y)

        if dist > mod_radius:
            num = math.ceil(dist/mod_radius)
            interpPoints = [(1/num) * i for i in range(num)]
            out_points = [LineString([x,y]).interpolate(j, True) for j in interpPoints]
            out_points.append(y)
            return out_points
        else:
            return [x,y]
        
    #It all seems to work without projecting back and forth.
    #I'm 99.999% sure the source GeoJson I'm using is in WGS84
    #And I *know* what Buildings API returns is GDA 94
    #But when I pull it down and drop it into anything they both line up.
    def reproject_wgs84_gda94(self, point):
        project = partial(
            transform,
            Proj(init='epsg:4326'), # source coordinate system
            Proj(init='epsg:4283')) # destination coordinate system
        return transform(project, point) 

    def get_building_ids_for_point(self, point, api_key):
        url = "https://api.psma.com.au/beta/v1/buildings/"
        headers = {'authorization': api_key}
        params = {
            'latLong' : f'{point.y},{point.x}',
            'radius' : str(self.radius),
            'perPage' : '20'
        }
        response = requests.request("GET", url, headers=headers, params=params)
        data = json.loads(response.text)['data']
        return [x['buildingId'] for x in data]

    def get_building_footprints(self, building_ids, key, is_2d_footprint, attributes):
        building_features = []
        counter = 1
        print(f"Total Buildings: {len(building_ids)}")
        for building_id in building_ids:
            print(f"Loaded {counter} out of {len(building_ids)} building footprints.", end='\r', flush=True)
            counter += 1
            building_footprint, b_attributes = self.get_building_footprint(building_id, key, is_2d_footprint, attributes)
            building_features.append(geojson.Feature(building_id,building_footprint,b_attributes))
        return building_features

    def get_building_footprint(self, buildingId, api_key, get_2d=True, attributes=[]):
        if get_2d:
            footprint_type = 'footprint2d'
        else:
            footprint_type = 'footprint3d'

        attributes = list(attributes)
        attributes.append(footprint_type)

        formatted_attribures = ",".join(attributes)
        url = f"https://api.psma.com.au/beta/v1/buildings/{buildingId}/"
        headers = {'authorization': api_key}
        params = {
            'include' : formatted_attribures
        }
        response = requests.request("GET", url, headers=headers, params=params)
        json_response = json.loads(response.text)

        returned_attributes = {}
        for attrib in attributes[:-1]:
            returned_attributes[attrib] = json_response[attrib]
        footprint = json_response[footprint_type]
        return shape(footprint), returned_attributes

    def get_query_points_from_geojson_features(self, features):
        points = []
        for feature in features:
            geom = feature['geometry']
            if geom.type == "Point":
                points.append(Point(geom.coordinates))
            elif geom.type == "MultiPoint":
                for point in geom.coordinates:
                    points.append(Point(point))
            elif geom.type == "LineString":
                line = geom.coordinates
                for p in self.densify_point_array(line):
                    points.append(p)
            elif geom.type == "MultiLineString":
                for line in geom.coordinates:
                    for p in self.densify_point_array(line):
                        points.append(p)
            elif geom.type == "Polygon":
                print("Currently Polygon only grabs buildings around the boarder defined by the polygon. It also does not take into account holes.")
                poly_border = geom.coordinates[0]
                for p in self.densify_point_array(poly_border):
                    points.append(p)
            elif geom.type == "MultiPolygon":
                print("Currently MultiPolygon only grabs buildings around the boarder defined by the polygons. It also does not take into account holes.")
                for geom in geom.coordinates:
                    poly_border = geom[0]
                    for p in self.densify_point_array(poly_border):
                        points.append(p)
            else:
                print(f"Geometry type {geom.type} not implemented yet")
                
        return points

    def densify_point_array(self, point_array):
        points = []
        for first,last in zip(point_array,point_array[1:]):
            [points.append(p) for p in self.get_points_between_points((first,last))]
        return points

    def filter_quadratic(self, data,condition):
        result = []
        count = 0
        print(f"Total Points Generated: {len(data)}")
        for element in data:
            count += 1
            if count%500 == 0:
                print(f"Compared: {count}")
                print(f"Saved: {len(result)}")
            if all(condition(element,other) for other in result):
                result.append(element)
        return result

    def by_distance(self, xs: Point, ys: Point):
        return xs.distance(ys) > 0.00015


import json
import math
import os
import sys
import time
from functools import partial

import click

import geojson
import pyproj
import requests
import shapely
from pyproj import Proj, transform
from shapely.geometry import (LineString, MultiPoint, MultiPolygon, Point,
                              mapping, shape)
from shapely.ops import transform

api_key = ''

@click.command(
    help='Takes a geojson file and returns a new geojson file with all the building footprints'
)
@click.option("--key", "-k",
    help='Your PSMA API key'
)
@click.option("--in_file", "-i",
    help='The input hgeojson file'
)
def estimate(key, in_file):
    start = time.time()

    api_key = key    

    points = get_points(in_file)
    points = filter_quadratic(points, by_distance)

    building_ids = get_building_ids(points)

    print(f"Total number of buildings returned: {len(building_ids)}")
    
    elapsed = time.time() - start
    print(f"Elapsed time: {elapsed}")
    
@click.command(
    help='Takes a geojson file and returns a new geojson file with all the building footprints'
)
@click.option("--key", "-k",
    help='Your PSMA API key',
    required=True
)
@click.option("--in_file", "-i",
    help='The input geojson file',
    required=True
)
@click.option("--out_file", "-o",
    help='The output geojson file',
    required=True
)
@click.option('--footprint_type', '-ft', 
    type=click.Choice(['2d', '3d']),
    help='Do you want the 2D or 3D footprint',
    required=True)
@click.option('--attribute', '-a', 
    help='Any other building attributes that you want to grab',
    multiple=True)
def run(key, in_file, out_file, footprint_type, attribute):
    start = time.time()

    api_key = key    

    points = get_points(in_file)
    points = filter_quadratic(points, by_distance)

    building_ids = get_building_ids(points)

    building_features = []
    counter = 1
    print(f"Total BuildingFootprints: {len(building_ids)}")
    for building_id in building_ids:
        # print(f"{counter} - {len(building_ids)}")
        counter += 1
        building_footprint, b_attributes = get_building_footprint(building_id, footprint_type == '2d', attribute)
        f = geojson.Feature(building_id,building_footprint,b_attributes)
        building_features.append(f)

    fc = geojson.FeatureCollection(building_features)
    gj = geojson.dumps(fc) 
    with open(out_file, 'w') as outfile:
        outfile.write(gj)
    elapsed = time.time() - start
    print(f"Elapsed time: {elapsed}")

def get_points(in_file):
    with open(in_file) as gj_file:
        gj = geojson.load(gj_file)

    return get_query_points_from_geojson_features(gj.features)

def get_building_ids(points):
    buildings = []
    counter = 1
    print(f"Total Points: {len(points)}")
    for point in points:
        print(f"{counter} - {len(points)}")
        counter += 1
        for building_id in get_building_ids_for_point(point):
            if building_id not in buildings:
                buildings.append(building_id)
    return buildings

def get_ponts_between_points(origin_points, radius=100):
    x = Point(origin_points[0])
    y = Point(origin_points[1])
    mod_radius = radius / 100000
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
def reproject_wgs84_gda94(point):
    project = partial(
        pyproj.transform,
        pyproj.Proj(init='epsg:4326'), # source coordinate system
        pyproj.Proj(init='epsg:4283')) # destination coordinate system
    return transform(project, point) 

def get_building_ids_for_point(point):
    url = "https://api.psma.com.au/beta/v1/buildings/"
    headers = {'authorization': api_key}
    params = {
        'latLong' : f'{point.y},{point.x}',
        'radius' : '100',
        'perPage' : '20'
    }
    response = requests.request("GET", url, headers=headers, params=params)
    data = json.loads(response.text)['data']
    return [x['buildingId'] for x in data]


def get_building_footprint(buildingId, get_2d=True, attributes=[]):
    if get_2d:
        footprint_type = 'footprint2d'
    else:
        footprint_type = 'footprint3d'

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

def get_query_points_from_geojson_features(features):
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
            for first,last in zip(line,line[1:]):
                [points.append(p) for p in get_ponts_between_points((first,last))]
        elif geom.type == "MultiLineString":
            for line in geom.coordinates:
                for first,last in zip(line,line[1:]):
                    [points.append(p) for p in get_ponts_between_points((first,last))]
        elif geom.type == "Polygon":
            print("Currently Polygon only grabs buildings around the boarder defined by the polygon. It also does not take into account holes.")
            poly_border = geom.coordinates[0]
            for first,last in zip(poly_border,poly_border[1:]):
                [points.append(p) for p in get_ponts_between_points((first,last))]
        elif geom.type == "MultiPolygon":
            print("Currently MultiPolygon only grabs buildings around the boarder defined by the polygons. It also does not take into account holes.")
            for geom in geom.coordinates:
                poly_border = geom[0]
                for first,last in zip(poly_border,poly_border[1:]):
                    [points.append(p) for p in get_ponts_between_points((first,last))]
        else:
            print(f"Geometry type {geom.type} not implemented yet")
            
    return points

def filter_quadratic(data,condition):
    result = []
    count = 0
    print(f"Total: {len(data)}")
    for element in data:
        count += 1
        if count%500 == 0:
            print(f"Compared: {count}")
            print(f"Saved: {len(result)}")
        if all(condition(element,other) for other in result):
            result.append(element)
    return result

def by_distance(xs: Point, ys: Point):
    return xs.distance(ys) > 0.00015


@click.group()
def cli():
    pass
    
cli.add_command(estimate)
cli.add_command(run)

if __name__ == "__main__":
    cli()
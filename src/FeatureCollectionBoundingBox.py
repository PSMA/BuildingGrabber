
import geojson

import shapely
from shapely.geometry import Point, LineString, MultiPolygon, shape, mapping

def get_boundingbox(feature_array):
	max_bounds = list(shape(feature_array[0].geometry).bounds)
	for feature in feature_array[1:]:
		bounds = shape(feature.geometry).bounds
		
		if bounds[0] < max_bounds[0]:
			max_bounds[0] = bounds[0]
		if bounds[1] < max_bounds[1]:
			max_bounds[1] = bounds[1]
		if bounds[2] > max_bounds[2]:
			max_bounds[2] = bounds[2]
		if bounds[3] > max_bounds[3]:
			max_bounds[3] = bounds[3]
			
	return max_bounds
		
		
if __name__ == "__main__":
	with open('Bris_Cbd.geojson') as gj_file:
		gj = geojson.load(gj_file)
		
	bounding_box = get_boundingbox(gj.features)
	
	gj['bbox'] = bounding_box
	
	with open("Bris_Cbd_bb.geojson", 'w') as out_file:
		out_file.write(geojson.dumps(gj))
		

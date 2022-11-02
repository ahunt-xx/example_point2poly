"""
Exmaple point to polygon tool
Author: Aaron Hunt
Date: 11/2/2022
"""

import shapefile
import shapely.geometry
from shapely.geometry import LineString, Polygon, mapping, shape
from shapely import affinity
from datetime import datetime, timedelta

#max time in seconds between points
max_time = 3

#input shpape in UTM16
sf = shapefile.Reader("utm16n.shp")

#output polygon file
w = shapefile.Writer('testfile',shapeType=5)
w.fields = list(sf.fields)


line_1 = None #First line in the polygon
last_time = None #The time stamp from the last loop


#Sort the recorde by time
features = sf.shapeRecords()
features.sort(key=lambda feat: feat.record["IsoTime"])

#loop throught each point feature
for point in features:
	the_point = shapely.geometry.shape(point.shape)

	#Feet to meter if you data requires it
	width = point.record[1]*0.3048 
	
	heading = point.record[8]
	#For affinity.rotate need to take the heading * -1
	heading = heading * -1

	#Create the line in the x axis that is the width anf the point x as the center
	x1 = the_point.x - width/2
	x2 = the_point.x + width/2

	#rotate the line based on the heading
	rotated_line = affinity.rotate(LineString([(x1, the_point.y), (x2, the_point.y)]), heading, origin=(the_point.x,the_point.y))

	#Get the current point time stamp
	time = datetime.strptime(point.record[11], "%Y-%m-%dT%H:%M:%S.%fZ")
	
	#if we have a line from the point before
	if line_1:
		#Fine the different in time in seconds
		total_seconds = (time - last_time).total_seconds()

		#make the polygon if the time between point is < max time in seconds and the mass is > 0
		if total_seconds < max_time and point.record[5] > -1:
			#Put both lines together as a polygon
			p = Polygon([*list(line_1.coords), *list(rotated_line.coords)[::-1]])
			#add the polygon to the output shape file
			w.poly(mapping(p)["coordinates"])
			#add the records form the input shapefile to the output shapefile
			w.record(*point.record)

			#set var for next time through loop
			last_time = time
			line_1 = rotated_line
		else:
			#if max time exceeded or mass < 0 reset and skip point 
			line_1 = None
			last_time = None

	else:
		#If first line has not been created yet. Create the line
		line_1 = rotated_line
		last_time = datetime.strptime(point.record[11], "%Y-%m-%dT%H:%M:%S.%fZ")
		
#Close the shape file		
w.close()


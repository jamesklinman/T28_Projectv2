# -*- coding: utf-8 -*-
"""
Created on Mon Sep 18 14:47:20 2023

@author: james.klinman

to run: runfile('Aircraft_Tracks_Visualization.py', args='668.nc cfrad.668_172757_172829.000_CHILL_PPI.nc ParamInfoFolder/668_paramInfo.txt Flight668_TrackData.txt 1')

"""

#FIND A PLACE FOR THIS
fontsizeParam = 80

import matplotlib.pyplot as plt
import pyart
import os
import numpy as np
import cartopy.crs as ccrs
import sys
import netCDF4 
import math
import statistics as stat
import pandas as pd
import re
import Top_Hail_Methods as hail

planefile = sys.argv[1]
radarfile = sys.argv[2]
paramInfo = sys.argv[3]
trackfile = sys.argv[4]
zoomargv = sys.argv[5]

    

airplanedata = netCDF4.Dataset(planefile)
radar = pyart.io.read(radarfile)
initParameters = pd.read_csv(paramInfo, sep=' * ', engine='python')
trackData = pd.read_pickle(trackfile)
zoomfactor = int(zoomargv)

latitudedata = airplanedata.variables['LATITUDE_DECIMAL_DEG_20Hz']
longitudedata = airplanedata.variables['LONGITUDE_DECIMAL_DEG_20Hz']

paramUse = str(initParameters['Radar_Variable'][0])

display = pyart.graph.RadarMapDisplay(radar)
#
# Next makes thresholding available
gatefilter = pyart.filters.GateFilter(radar)
# Basic threshold removes gates with missing reflectivity (DZ)
gatefilter.exclude_invalid(paramUse)
gatefilter.exclude_outside('DZ', 10, 100)
if paramUse == 'RX':
    gatefilter.exclude_above('RX', 1.05)
#gatefilter.exclude_outside('DZ', -3, 100)

# Centers a lat - lon based plotting domain on the radar:
projection = ccrs.LambertConformal(central_latitude=radar.latitude['data'][0],
                                   central_longitude=radar.longitude['data'][0])

# Size arguments are width, height in inches
fig = plt.figure(figsize = [25.0,25.0])

FlightNum = str(getattr(airplanedata, 'FlightNumber'))
FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDate = FlightDate.split('/')
FlightDate = FlightDate[2]+''+FlightDate[0]+''+FlightDate[1]
label= str(initParameters['Time_Start'][0]) + '-' + str(initParameters['Time_End'][0]) + 'MT 22 June 1995, '\
     '\n Radar Variable: ' + str(paramUse)
#
# PPI plot specification
#paramuse is DZ, DR, LDR etc.    Sweep is closest sweep to aircraft.
#vmin/max are colorbar ranges.   cmap is color table to use
# here I'm using the Carbone42 color sequence (dates back to the NCAR RDSS software). 


#get auto graph limits and lines
airlatlist = trackData[0][3]
airlonlist = trackData[0][4]

upperLat = round(max(airlatlist) + (.05 / zoomfactor), 2)
lowerLat = round(min(airlatlist) - (.05 / zoomfactor), 2)
upperLon = round(max(airlonlist) + (.05 / zoomfactor), 2)
lowerLon = round(min(airlonlist) - (.05 / zoomfactor), 2)
 
#generating color limits and small marker colors for each variable
if paramUse == 'DZ':
    vminHolder, vmaxHolder = 10, 70
    colorHolder = 'blue'
    varName = 'Reflectivity'
    cbtickiter = 10
    units = 'dBZ'
elif paramUse == 'DR':
   vminHolder, vmaxHolder = -1, 5
   colorHolder = 'red' 
   varName = 'Differential\nReflectivity'
   cbtickiter = 1
   units = 'dB'
elif paramUse == 'LD':
   vminHolder, vmaxHolder = -30, -5
   colorHolder = 'yellow'
   varName = 'Linear Depolarization\nRatio'
   cbtickiter = 5
   units = 'dB'
elif paramUse == 'RX':
   vminHolder, vmaxHolder = .75, 1
   colorHolder = 'blue' 
   varName = 'Correlation\nCoeffiecient'
   cbtickiter = .05
   units = ''

lat_lines2=np.array(hail.sizechange(np.arange(lowerLat, upperLat, abs(upperLat - lowerLat)/3), 5))

sweepnumtouse = int(trackData[0][1][1])
#sweepnumtouse is the sweep closest to the aircraft.
#paramUse is the prespecified radar variable to plot
display.plot_ppi_map(paramUse, sweepnumtouse, vmin=vminHolder, vmax=vmaxHolder,
                      min_lon=upperLon, max_lon=lowerLon, min_lat=lowerLat, max_lat=upperLat,
                      lat_lines=np.array(hail.sizechange(np.arange(lowerLat, upperLat, abs(upperLat - lowerLat)/3), 5)), 
                      resolution='10m',
                      lon_lines=np.arange(upperLon, lowerLon, -abs(lowerLon - upperLon)/3),
                      projection=projection,
                      fig=fig, lat_0=radar.latitude['data'][0],
                      lon_0=radar.longitude['data'][0],
                      cmap = pyart.graph.cm.Carbone42, gatefilter = gatefilter,
                      )

cbar = display.cbs[0]
cbar.set_ticklabels(np.arange(vminHolder, vmaxHolder+cbtickiter, cbtickiter), fontsize=fontsizeParam) # [0.75, '0.80' , 0.85, '0.90' , 0.95, '1.00'  , 1.05]
cbar.set_label(label=units, fontsize=fontsizeParam)

#
# Draw the range rings (in km)
#display.plot_range_rings([30., 40.])

plt.title(varName, fontsize=fontsizeParam) 
plt.xticks(fontsize=fontsizeParam, rotation=20)
plt.yticks(fontsize=fontsizeParam)

#displaying all the lat long location of the plane for the time range
display.plot_point([airlonlist[:]], [airlatlist[:]], markersize=16, color="black")

#points of interest lists
interestlat = trackData[0][5]
interestlon = trackData[0][6]
#displaying start and end point of manual relevant time periods
display.plot_point(interestlat, interestlon, \
                    marker="x", markersize=50, mew=8, color="white")

#This loop finds the reflectivities for the gates inbetween the interesting 
#aircraft points and averages them
Interesting_Point_Lower_Loc = trackData[0][7][0]
Interesting_Point_Upper_Loc = trackData[0][7][2] #                                                                                  NOT AUTOMATIC HAS THE GLOBAL VARS
radarInfo = []
tempiter = 0
#for x in range(len(interestingPoints)):
for x in range(Interesting_Point_Lower_Loc, Interesting_Point_Upper_Loc):
    #radarInfo.append([])
    radarInfo.append(float(pyart.util.get_field_location(radar, 
                 float(latitudedata[x, 0]), float(longitudedata[x, 0]))
                 [paramUse][sweepnumtouse]))
    tempiter += 1
    

"""
For RX because some values are erronous
summedradarInfo1RX = 0
tempiter = 0
for x in radarInfo[0:10]:
    if x <= 1.05:
        summedradarInfo1RX += x
        tempiter += 1
summedradarInfo1RX = summedradarInfo1RX/tempiter

summedradarInfo2RX = 0
tempiter = 0
for x in radarInfo[10:21]:
    if x <= 1.05:
        summedradarInfo2RX += x
        tempiter += 1
summedradarInfo2RX = summedradarInfo2RX/tempiter
"""
    
summedradarInfo1 = sum(radarInfo[0:10]) / len(radarInfo[0:10])
summedradarInfo2 = sum(radarInfo[10:21]) / len(radarInfo[10:21])

plt.annotate(str(round(summedradarInfo1, 2)), 
             xy=(8900, 37200), 
             xytext=(0.78, .08), fontsize=fontsizeParam-34, textcoords='axes fraction',
             #arrowprops=dict(facecolor='black', shrink=0.25, width=8, headwidth=25),
             horizontalalignment='left',
             verticalalignment='top')
plt.annotate(str(round(summedradarInfo2, 2)), 
             xy=(9800, 37500), 
             xytext=(0.78, .18), fontsize=fontsizeParam-34, textcoords='axes fraction',
             #arrowprops=dict(facecolor='black', shrink=0.25, width=8, headwidth=25),
             horizontalalignment='left',
             verticalalignment='top')
    
plt.show()
 
#fig.savefig('./T28_22jun1995_track' + paramUse + '.png')#, bbox_inches = 'tight')
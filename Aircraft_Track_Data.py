#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 14:15:18 2023

@author: james.klinman

for running in spyder
to run: runfile('Aircraft_Track_Data.py', args='668.nc cfrad.668_172757_172829.000_CHILL_PPI.nc ParamInfoFolder/668_paramInfo.txt')
        runfile('Aircraft_Track_Data.py', args='Flight_Files/757.nc Radar_Files/cfrad.20000623_002721.000_to_20000623_003226.000_CHILL_PPI.nc Param_Info/757_paramInfo.txt Param_Info/20231023/Flight_757_Indexs.pkl')

Pre-requisites to run:
    Programs to run before this one:
        -Flight_Index_Finder
    
    Files required:
        -Flight_Files/*FlightNum*.nc (netcdf flight file)
        -Radar_Files/*radar file* 
            -only tested for netcdf CFRadial files
        -Param_Info/20231023/Flight_*FlightNum*_Indexs.pkl
        -Param_Info/*FlightNum*_paramInfo.txt


ONLY WORKS FOR THREE POINTS OF INTEREST AT THE MOMENT
"""

import pyart
import os
import numpy as np
import sys
import netCDF4 
import pandas as pd
import Top_Hail_Methods as hail
import pickle

planefile = sys.argv[1]
radarfile = sys.argv[2]
paramInfo = sys.argv[3]
indexInfo = sys.argv[4]
"""
flightData = sys.argv[6]

if flightData == 'yes':
    pass
elif flightData == 'Yes':
    pass
elif flightData == None:
    pass
"""
airplanedata = netCDF4.Dataset(planefile)
timedata = airplanedata.variables['TIME_GPS_DECIMAL']
latitudedata = airplanedata.variables['LATITUDE_DECIMAL_DEG_20Hz']
longitudedata = airplanedata.variables['LONGITUDE_DECIMAL_DEG_20Hz']
aircraftalt = airplanedata.variables['GPS_ALTITUDE']
with open(indexInfo, "rb") as file:   # Unpickling
   indexs = pickle.load(file)


radardata = netCDF4.Dataset(radarfile)
radarangle = radardata.variables['fixed_angle']
radarlat = radardata.variables['latitude']
radarlon = radardata.variables['longitude'] 
groundelevation = int(radardata['altitude'][:]) #was named elevation

initParameters = pd.read_csv(paramInfo, sep=' * ', engine='python')



#NOTE for all of this time stuff. I'm thinking of converting all the time
#dependent code into seconds from midnight as a standard way of operating
#plus that would make it easier to deal with the hertz data I think
#and then anything that is printed out to the user as a presentable format
#can be in HHMMSS
initTime = str(initParameters['Time_Start'][0])
finTime = str(initParameters['Time_End'][0])
wholeAirTrack = hail.sep_HHMMSS(time=[initTime, finTime])
time_range = initTime + ':' + finTime

interestingPoints = []
for x in initParameters['Points_of_Interest']:
    interestingPoints.append(str(x))
interestingPoints = hail.forceHHMMSS(interestingPoints)
print('hi')
pInterest = hail.sep_HHMMSS(time=interestingPoints) #points of interest shortend
"""
startTime_hrs = int(wholeAirTrack[0][0])
startTime_min = int(wholeAirTrack[0][1]) 
startTime_sec = int(wholeAirTrack[0][2])
endTime_hrs = int(wholeAirTrack[1][0]) 
endTime_min = int(wholeAirTrack[1][1]) 
endTime_sec = int(wholeAirTrack[1][2])
"""
timeZone = int(initParameters['Timezone'][0])

#Naming some global variables that are later used in a calculation 

#variables for the calculation of radar sweep height. might not be accurate
estH0 = .007 #in km, is the estimated height of the radar. potentially neglible
Rprime = 8483 #in km, the fictious earth radius pulled from the meteorlogical book
errorNum = -99.9


"""
#converted time range to decimal because that seemed to be the easiest array to 
#look through for time. all this is used for is to get the start and end xy variables
timeConverted = hail.HHMMSS_2_Dec(HHMMSS=[initTime, finTime], timeCorrect=timeZone)
timeStart, timeEnd = timeConverted[0], timeConverted[1]

startArray = hail.find_loc_in_array(dataset=timedata, valueToFind=timeStart)
endArray = hail.find_loc_in_array(dataset=timedata, valueToFind=timeEnd)

#pull out the start and end x,y coordinates
startxvar = startArray[0]
startyvar = startArray[1]
endxvar = endArray[0]
endyvar = endArray[1]
print('Past time consuming part. Found start and end loc in array for analysis')
"""
startxvar = indexs[time_range][0][0][0]
startyvar = indexs[time_range][0][0][1]
endxvar = indexs[time_range][0][1][0]
endyvar = indexs[time_range][0][1][1]

#created x and y coordinates for airplane track
airlatlist = hail.create_dataList(dataset=latitudedata, startxLoc=startxvar,\
                                    endxLoc=endxvar)
airlonlist = hail.create_dataList(dataset=longitudedata, startxLoc=startxvar,\
                                    endxLoc=endxvar)
print('Air track coords found and stored')

#The sweep number containing the airplane or closest to the airplace is found
#It was calculated using the avg og 
sweepData = hail.getSweep(R=Rprime, Hradar=estH0, aircraftAlt=aircraftalt,\
                          radarlat=radarlat, radarlon=radarlon,\
                          radarAngles=radarangle, elevation=groundelevation,\
                          startxloc=startxvar, endxloc=endxvar, \
                          planelat=airlatlist, planelon=airlonlist)
print('Got the sweep data')

#The below chunk is finding the location of the interesting points within the 
#data file 
planeMarkers = hail.HHMMSS_2_Dec(interestingPoints, timeZone)

Mark1 = hail.find_loc_in_array(dataset=timedata, valueToFind=planeMarkers[0]\
                                       , startLoc=startxvar)
Mark2 = hail.find_loc_in_array(dataset=timedata, valueToFind=planeMarkers[1]\
                                       , startLoc=startxvar)
Mark3 = hail.find_loc_in_array(dataset=timedata, valueToFind=planeMarkers[2]\
                                       , startLoc=startxvar)
templist = [Mark1, Mark2, Mark3]

Mark1Lat = latitudedata[Mark1[0], 0]
Mark1Lon = longitudedata[Mark1[0], 0]
Mark2Lat = latitudedata[Mark2[0], 0]
Mark2Lon = longitudedata[Mark2[0], 0]
Mark3Lat = latitudedata[Mark3[0], 0]
Mark3Lon = longitudedata[Mark3[0], 0]

latList = [float(Mark1Lat), float(Mark2Lat), float(Mark3Lat)]
lonList = [float(Mark1Lon), float(Mark2Lon), float(Mark3Lon)]

print("Got positions of interesting points for analysis")

#Creating all the lists of data so that they're stored in rows/their own arrays
#Because creating same sized columns so that the data could be looped through
#sounded like a pain to do.
#it looks so ugly in the txt file but it reads in fine for the programs that
#use the data so ¯\_(ツ)_/¯ 
dataRangearr = np.array([startxvar, startyvar, endxvar, endyvar])
sweepDataarr = np.array([sweepData[0], sweepData[1], sweepData[2]])
sweepheightsarr = np.array(sweepData[3])
airlatlistarr = np.array(airlatlist)
airlonlistarr = np.array(airlonlist)
latlistarr = np.array(latList)
lonlistarr = np.array(lonList)
interestloc = np.array([Mark1[0], Mark2[0], Mark3[0]])

allinformation = np.array([dataRangearr, sweepDataarr, sweepheightsarr,\
                           airlatlistarr, airlonlistarr, latlistarr,\
                           lonlistarr, interestloc], dtype=object)

df = pd.DataFrame(allinformation)


#Creating the file with all of the data we just found
FlightNum = str(getattr(airplanedata, 'FlightNumber'))
FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDate = FlightDate.split('/')
FlightDate = FlightDate[2]+''+FlightDate[0]+''+FlightDate[1]


filesave = 'Sensor_Information/Flight' + FlightNum + '_TrackData' + '.txt'

df.to_pickle(filesave)

#writing the start and end index into the init param file
#start_index_loc = initParameters.loc[0, 'Index_StartEnd']
#end_index_loc = initParameters.loc[0, 'Index_StartEnd']
initParameters.at[0, 'Index_StartEnd'] = startxvar
initParameters.at[1, 'Index_StartEnd'] = endxvar

initParameters.to_csv('testing', sep=' ', encoding='utf-8')

initParameters.insert(0, 'indxs', startxvar)



""", index=0, header=['The rows are: Range of data, Single sweep variables,'\
                                           'Potential sweep heights, Airplane Latitude Track, '\
                                           'Airplane longitude track, '\
                                           'Interesting range latitudes, '\
                                           'Interesting range longitudes'\
                                           'Interesting range locinarray'])"""

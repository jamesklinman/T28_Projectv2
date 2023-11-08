# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 10:00:40 2023

@author: james.klinman

Takes bin adjusted files!
takes spec and normalizes the ocncentration
hvps data is prepped
produces PSD
currently works well for 10 sec ranges. Not properly tested for other time ranges.
Not tested for non 5interval chunks of time either    have notes need to implement


!!!plot and table titles are wrong and need to account for if it's just five seconds or whatever
!!!the binning of the remaning time chunks does not tell you if it was just
     5 seconds or whatever or not
     so need to implement a check to see if it entered the final loop and to
     make a note on the final plot and table that the data is reduced

runfile('HVPS_Spectrometer_Comparison.py', args='Particle_Concs/06222000_232921_HVPS1.txt Particle_Concs/06222000_232921_HAIL.txt Param_Info/757_paramInfo.txt Sensor_Information/HHMMSS_True_Calc_Airspeed_757.txt Flight_Files/757.nc Param_Info/757_paramInfo.txt')
runfile('HVPS_Spectrometer_Comparison.py', args='Particle_Concs/06222000_232921_HVPS1.txt Particle_Concs/disp757.0 Param_Info/757_paramInfo.txt Sensor_Information/HHMMSS_True_Calc_Airspeed_757.txt Flight_Files/757.nc Param_Info/757_paramInfo.txt')
"""

import os
import sys
import pandas as pd
import numpy as np
import Top_Hail_Methods as hail
import matplotlib.pyplot as plt
import math
import netCDF4
from datetime import date
import pickle


#getting flight num
flight_programs_file = 'Param_Info/File_Runner_Info.txt'
flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')
flight_num = str(flight_programs_info['flight_num'][0])

#file running files
paramInfo = 'Param_Info/' + flight_num + '_paramInfo.txt'
indexInfo = 'Param_Info/Indexs/Flight_' + flight_num + '_Indexs.pkl'
iteration_track_file = 'Automated_Files/Iteration_Tracker.txt'


#Calling in plane data files
#---------------------------
TASfilename = 'Sensor_Information/HHMMSS_True_Calc_Airspeed_'\
               + flight_num + '.txt'
planefile = 'Flight_Files/' + flight_num + '.nc'

#true airspeed for each second
#and airplane data for naming the tables and plots
#-------------------------------------------------
TASfile = pd.read_csv(TASfilename, sep=' * ')
airplanedata = netCDF4.Dataset(planefile)

#Getting the flight data and other data for file naming and plot title making.
#Needed up here since SODA file names require date
#-----------------------------------------------------------------------------
FlightNum = str(getattr(airplanedata, 'FlightNumber'))
FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDateSplit = FlightDate.split('/')
FlightDate = FlightDateSplit[2]+''+FlightDateSplit[0]+''+FlightDateSplit[1]
FlightDate_File = FlightDateSplit[0]+''+FlightDateSplit[1]+''+FlightDateSplit[2]

plane_time_start = getattr(airplanedata, 'TimeInterval')[0:8]
for char in plane_time_start:
    if char == ':':
        plane_time_start = plane_time_start.replace(':', '')

#Now can finally call concentration file names
#---------------------------------------------
filenameHVPS = 'Particle_Concs/' + FlightDate_File + '_' + plane_time_start +\
               '_HVPS1.txt'
filenameSpec = 'Particle_Concs/disp' + flight_num + '.0'


#Calling start and end time before reading in the 
#rest of the files since they're time dependent
#------------------------------------------------
initParameters = pd.read_csv(paramInfo, sep=' * ', engine='python')

iterationTracker = pd.read_csv(iteration_track_file, sep=' * ', engine='python')
with open(indexInfo, "rb") as file:   # Unpickling
   indexs = pickle.load(file)
print(indexs)

time_index_to_use = iterationTracker['Iteration'][0] * \
    iterationTracker['Skip_Num'][0]

starttime = str(initParameters['Time_Start'][time_index_to_use])
endtime = str(initParameters['Time_End'][time_index_to_use])
timeZone = int(initParameters['Timezone_true'][0])


#Tells the program what the chunks/number
#of seconds to bin the data together is
#minimum of either 1s or what SODA was set to
#--------------------------------------------
TimeResolution = int(initParameters['PSD_Time_Res'][0])


#SODA defaults to a rate of 5 seconds (read as 5s chunks which is
#related to the time resolution). So this just hardcodes that in.
#----------------------------------------------------------------
HvpsPreChunk = 5
                
#If the spectrometer data is read in from the 1D hail counts file generated
#by SDSMT, it requires the below corrections.
#BinSize is the change in width for each channel
#SA is surface area the probe covered.
#--------------------------------------------------------------------------
BinSize = np.array([.1, .1, .1, .1, .14, .16, .20, .26, .30, .31, .44, .60,\
                    .79, 1])
BinSize = BinSize / 100 #to correct for cm -> m
SA = .1 #in m^-2


#These are the channels/bins, whatever you want to call them. Units are in cm
#xaxis 2 is the channels for the 1D SDSMT hail counts. It is also used for 
#SODA if SODA bins were set to match the SDSMT ones
#xaxis3 are the default SODA bins and are typically used for the HVPS data
#-----------------------------------------------------------------------------
xaxis2 = np.array([.4, .5, .6, .7, .8, .94, 1.1, 1.3, 1.56, 1.86, 2.17, 2.61,\
                   3.21, 4])

xaxis3 = np.array([.02, .04, .06, .08, .1, .12, .14, .16, .18, .22, .26, .3,\
                   .34, .38, .42, .46, .5, .6, .7, .8, .9, 1, 1.5, 2, 2.5])


#Reading in the HVPS data
#------------------------
HVPSData = pd.read_csv(filenameHVPS, sep=' * ', header=22)
tempdf = pd.DataFrame(HVPSData)
tempdf = tempdf.drop(index=0)
HVPSData = pd.DataFrame.reset_index(tempdf)


#There are two variations of hail spectrometer data. One is a file generated
#by SODA. This is under "try". The other is the file generated by SDSMT and is
#under "except".
#-----------------------------------------------------------------------------
try:
    SpecData = pd.read_csv(filenameSpec, sep=' * ', header=22)
    tempdf2 = pd.DataFrame(SpecData)
    tempdf2 = tempdf2.drop(index=0)
    SpecData = pd.DataFrame.reset_index(tempdf2)
    
    #determines which if statements to use/how to process 
    #the data for the rest of the file
    new_spec_file_tracker = 'y'

except:
    #Preping Spectrometer data
    #got the first chunk of code below from
    #https://stackoverflow.com/questions/7356043/how-to-delete-specific-strings-from-a-file
    #it deletes all the new page headers that are attached to the rows of data
    #-------------------------------------------------------------------------
    strToDelete = ['F l i g h t  757  22-Jun-0  Hail Info'] 
    endoffiletodelete = '-=-'
    fin = open(filenameSpec, "r")
    fout = open("Random/Spec_Corrected_File", "w+")
    for line in fin:
        for word in strToDelete:
            line = line.replace(word, "")
        fout.write(line)
    fin.close()
    fout.close()
    
    #first loop from https://pynative.com/python-count-number-of-lines-in-file/
    #gets length of file and get reads in just the spec data
    with open(r"Random/Spec_Corrected_File", 'r') as file:
        for count, line in enumerate(file):
            pass
        FileLen = count + 1
    Spacing = 55 #spacing between rows to skip. Hardcoded in for SDSMT data
    RowsToSkip = []
    RowsToSkip.append(57)
    NewHeadSkip = 57
    while NewHeadSkip <= FileLen:
        NewHeadSkip += Spacing
        RowsToSkip.append((NewHeadSkip))
    SpecFile = "Random/Spec_Corrected_File"
    SpecData = pd.read_csv(SpecFile, sep=' * ', header=0, skiprows=RowsToSkip)
    
    #Since the SDSMT files are in local time, the
    #below chunk  converts the time into UTC
    starttimeSpec = hail.HHMMSS_adjustHH(starttime, (-(timeZone)))
    endtimeSpec = hail.HHMMSS_adjustHH(endtime, (-(timeZone)))
    starttimeSpec = hail.forceHHMMSS(starttimeSpec)
    endtimeSpec = hail.forceHHMMSS(endtimeSpec)
    
    #determines which if statements to use/how to process 
    #the data for the rest of the file 
    new_spec_file_tracker = 'n'



#------------------------------------------------------------------
#Now that the files are read in, the code can pull the HVPS and 
#Spectrometer data and apply corrections and create the time bins.
#------------------------------------------------------------------



#Converting SODA's HVPS time to HHMMSS format
#SODA's spits out time in UTC so no timezone correction needed
#-------------------------------------------------------------
templist = []
for x in HVPSData['Time']:
    templist.append(int(x))
HVPSTimeConv = hail.seconds_HHMMSS(templist)

#This says that if your start time is after the 24 hour mark, then 
#it needs to be adjusted to run over 24 hrs (ex: 00:51:20 -> 24:51:20).
#This is because the probe data was stored with the clock running past 24hrs
#This is because the parameter file that you set requires time to 
#not go over 24 hours.
#!NOTE! -- THIS ASSUMES NO FLIGHTS STARTED AFTER 2:59 UTC
#---------------------------------------------------------------------------
if int(airplanedata['TIME_HOURS_20Hz'][0][0]) > 3:
    if starttime[0:2] == '00':
        adjustHH = 24
    elif int(starttime[0:2]) <= 3:
        adjustHH = 24
    else:
        adjustHH = 0

starttime_adjust = hail.HHMMSS_adjustHH(starttime, adjustHH)
endtime_adjust = hail.HHMMSS_adjustHH(endtime, adjustHH)
starttime_adjust = hail.forceHHMMSS(starttime_adjust)
endtime_adjust = hail.forceHHMMSS(endtime_adjust)


#Since we don't need to bin or plot all the data, just some,
#the start and end index in the data is found for HVPS
#-----------------------------------------------------------
HVPS_Indx_Start = hail.find_loc_in_array_1D(
    HVPSData['Time'], hail.HHMMSS_2_SS([starttime_adjust])[0])

HVPS_Indx_End = hail.find_loc_in_array_1D(
    HVPSData['Time'], hail.HHMMSS_2_SS([endtime_adjust])[0])


#Getting start and end index for spectrometer data. "try" is if the file
#was produced using SODA. "except" is if it's in the SDSMT format
#-----------------------------------------------------------------------
if new_spec_file_tracker == 'y':
    SpecStartTimeIndx = hail.find_loc_in_array_1D(
        SpecData['Time'], hail.HHMMSS_2_SS([starttime_adjust])[0])
    
    SpecEndTimeIndx = hail.find_loc_in_array_1D(
        SpecData['Time'], hail.HHMMSS_2_SS([endtime_adjust])[0])

#POTENTIAL ERROR NOTE. If there's and error with the start and end time here
#then copy the method from starttime_adjust etc. to correct the spec data.
elif new_spec_file_tracker == 'n':
    SpecStartTimeIndx = None
    SpecEndTimeIndx = None
    tempiter = 0
    for x in SpecData['Time']:
        if x == '-=-':
            break
        if str(int(float(x))) == str(starttime_adjust): #need starttimeSPec if its 1995, but adjust if it's 2000   .....
            SpecStartTimeIndx = tempiter
        if str(int(float(x))) == str(endtime_adjust):
            SpecEndTimeIndx = tempiter
            break
        else:
            tempiter +=1


#Gets the start and end time for the airplane
#along with the start and end index
#--------------------------------------------
starttimeTAS = hail.HHMMSS_resetHH(starttime)
endtimeTAS = hail.HHMMSS_resetHH(endtime)

starttimeTAS = hail.forceHHMMSS(starttimeTAS)
endtimeTAS = hail.forceHHMMSS(endtimeTAS)

PlaneStartIndx = None
PlaneEndIndx = None
tempiter = 0
#TAS file is in HHMMSS and resets after 24hrs 
for x in TASfile['HHMMSS']:
    if int(x) == int(starttimeTAS):
        PlaneStartIndx = tempiter
    if int(x) == int(endtimeTAS):
        PlaneEndIndx = tempiter
        break
    else:
        tempiter +=1 
        

#This is just making a list of the plane speeds and making
#sure that they're the same time as the spectrometer data.
#This is used later on for spectrometer data corrections      
#---------------------------------------------------------
PlaneSpeeds = []
for x in range(PlaneStartIndx, PlaneEndIndx + 1):
    for y in range(SpecStartTimeIndx, SpecEndTimeIndx + 1):
        if (int(SpecData['Time'][y])) == int(TASfile['HHMMSS'][x]):
            PlaneSpeeds.append(TASfile['Calc_Airspeed'][x])
        else:
            pass



#Using SODA particle concentration data for HVPS, the below
#two loops bin the data into 5n second chunks.
#----------------------------------------------------------
HvpsPlotLists = []
HvpsTimeRes = TimeResolution / HvpsPreChunk  #how many 5n sec to bin together
modulus_checker_thing = TimeResolution / HvpsPreChunk - 1
#modulus checker is a helper to let the code know how many
#5n seconds to chunk together

for x in range(math.ceil((HVPS_Indx_End - HVPS_Indx_Start) / HvpsTimeRes)): 
    HvpsPlotLists.append([])
    #Makes a empty list for each final chunk for the concentrations
    
tempiter = 0
concCount = 0
tempConc = None
for y in range(HVPS_Indx_End - HVPS_Indx_Start): 
    if y==0:
        pass
    #for an example of the below code, if time resolution is set to 10s, then 
    #the modulus checker is 1. So everytime that y modulus 2 (the HvpsTimeRes) 
    #is equal to 1 the condition will be met and the the current and previous 
    #bin will be added together.
    elif y%HvpsTimeRes == modulus_checker_thing:
        lowIndx = int(HVPS_Indx_Start + y - HvpsTimeRes)
        highIndx = int(HVPS_Indx_Start + y)
        for x in range(25): #hardcoded as 25 concs right now
            concCount += 1
            if concCount < 10:
                tempConc = 'Conc' + str(0)+str(0)+str(concCount)
            else:
                tempConc = 'Conc' + str(0)+str(concCount)
            HvpsPlotLists[tempiter].append(np.sum(HVPSData[str(tempConc)][int(lowIndx):int(highIndx)]))
        tempiter += 1
        concCount = 0
    #the below just sums up the remaining data if there is any
    elif y == (HVPS_Indx_End - HVPS_Indx_Start - 1): 
        lowIndx = HVPS_Indx_Start + y - HvpsTimeRes
        highIndx = HVPS_Indx_Start + y
        for x in range(25): #hardcoded as 25 concs right now
            concCount += 1
            if concCount < 10:
                tempConc = 'Conc' + str(0)+str(0)+str(concCount)
            else:
                tempConc = 'Conc' + str(0)+str(concCount)    
            HvpsPlotLists[tempiter].append(np.sum(HVPSData[str(tempConc)][int(lowIndx):int(highIndx)]))
HvpsPlotListsArray = np.array(HvpsPlotLists)   


#Is binning the spectrometer data into the chunks specified by TimeResolution. 
#If your hail concentrations are generated by SODA, then it does the if 'yes', 
#and if your hail counts are from SDMST 1D files, then it uses the elif 'no'.
#-----------------------------------------------------------------------------
#for this if statement, see the HVPS processing for comments
if new_spec_file_tracker == 'y':
    SpecPlotLists = []
    SpecTimeRes = TimeResolution / HvpsPreChunk
    for x in range(math.ceil((SpecEndTimeIndx - SpecStartTimeIndx) / HvpsTimeRes)):
        SpecPlotLists.append([])
    
    tempiter = 0
    concCount = 0
    tempConc = None
    for y in range(SpecEndTimeIndx - SpecStartTimeIndx):
        tempSum = SpecPlotLists[tempiter]
        print(y)
        if y==0:
            pass
        elif y%SpecTimeRes == modulus_checker_thing:
            lowIndx = int(SpecStartTimeIndx + y - HvpsTimeRes)
            highIndx = int(SpecStartTimeIndx + y)
            for x in range(1, 15): #hardcoded as 15 concs right now
                concCount += 1
                if concCount < 10:
                    tempConc = 'Conc' + str(0)+str(0)+str(concCount)
                else:
                    tempConc = 'Conc' + str(0)+str(concCount)
                tempSum.append(np.sum(SpecData[str(tempConc)][int(lowIndx):int(highIndx)]))
            tempiter += 1
            concCount = 0
        elif y == SpecEndTimeIndx - SpecStartTimeIndx - 1:
            lowIndx = SpecStartTimeIndx + y - HvpsTimeRes
            highIndx = SpecStartTimeIndx + y
            for x in range(1, 15): #hardcoded as 15 concs right now
                concCount += 1
                if concCount < 10:
                    tempConc = 'Conc' + str(0)+str(0)+str(concCount)
                else:
                    tempConc = 'Conc' + str(0)+str(concCount)    
                tempSum.append(np.sum(SpecData[str(tempConc)][int(lowIndx):int(highIndx)]))
    SpecPlotListsArray = np.array(SpecPlotLists)            

elif new_spec_file_tracker == 'n':
    print('oogabooga')
    ColumnRange = len(range(SpecStartTimeIndx, SpecEndTimeIndx + 1))
    SpecDataCorrected = np.array([[]])
    SpecDataCorrected = SpecDataCorrected.reshape(ColumnRange,0)
    for x in range(1, 15): #starts at 1 because of file format
        BinCorrected = np.array([[]])
        for y in range(SpecStartTimeIndx, SpecEndTimeIndx + 1):#we want data for this range
            tempBin = float(SpecData[str(x)][y])
            BinCorrected = np.append(BinCorrected, tempBin)
        BinCorrected = np.array([BinCorrected]).reshape(ColumnRange, 1)
        BinCorrected = BinCorrected / BinSize[x - 1] #Normalizing each bin for its change in size 
        if x == 1:
            print 
        SpecDataCorrected = np.append(SpecDataCorrected, BinCorrected, axis=1)
    
    SpecDataCorrected = SpecDataCorrected / SA  
    
    #Needed to make a copy to prevent overwriting I think. I'm not sure if it's
    #needed but I'm too scared to get rid of it
    SpecCor = SpecDataCorrected.copy() 

    for x in range(SpecCor.shape[0]):
        SpecCor[x] = SpecCor[x] / PlaneSpeeds[x]
    
    #This will end up being all the chunked together concs
    SpecPlotLists = [] 

    for x in range(math.ceil((SpecCor.shape[0] - 1)/TimeResolution)): 
        SpecPlotLists.append([])
    tempiter = 0
    for y in range(SpecCor.shape[0]):
        tempSum = SpecPlotLists[tempiter]
        if y==0:
            pass
        elif y%TimeResolution == 0: #Sums together chunks of TimeResolution
            tempy = y - TimeResolution
            for x in range(SpecCor.shape[1]):
                tempSum.append(np.sum(SpecCor[tempy:y][:,x]))
            tempiter += 1
        elif y == SpecCor.shape[0] - 1: #Sums up the remaining data 
            tempRange = SpecCor.shape[0] - 1 - tempiter * TimeResolution
            tempy = y - tempRange
            for x in range(SpecCor.shape[1]):
                tempSum.append(np.sum(SpecCor[tempy:y][:,x]))
    SpecPlotListsArray = np.array(SpecPlotLists)


print("0000000000000000000000000000000000000000000000000000000000000000000000000000000000")


#Getting current date for folder making purposes
#Creating the directory to store the plots and tables in
#-------------------------------------------------------
current_date = date.today()
file_created_date = current_date.strftime("%Y%m%d")

if os.path.exists('./PSD_Plots/' + file_created_date) is False:
    os.mkdir('./PSD_Plots/' + file_created_date)
if os.path.exists('./PSD_Tables/' + file_created_date) is False:
     os.mkdir('./PSD_Tables/' + file_created_date)


#The for loop here is where the plots and tables are made.
#---------------------------------------------------------
titleTimeIndx = HVPS_Indx_Start
for x in range(len(SpecPlotLists)):
    fig = plt.figure(figsize = [23.0,20.0])


    tempRange = int(HVPSTimeConv[titleTimeIndx]) + TimeResolution
    timeRange = str(HVPSTimeConv[titleTimeIndx][0:2] +':'+
                    HVPSTimeConv[titleTimeIndx][2:4] +':'+
                    HVPSTimeConv[titleTimeIndx][4:6]) + "-" + str(
                        str(tempRange)[0:2] +':'+
                        str(tempRange)[2:4] +':'+
                        str(tempRange)[4:6])
    plt.title("HVPS & Hail Spectrometer Concentrations,\n" + timeRange,
              fontsize=50)


    #Creating spectrometer table of concentrations
    #---------------------------------------------
    tableNameSpec = "./PSD_Tables/" + file_created_date + "/Spec_Conc_per_Bin_" + str(FlightDate)\
                    + '_' + HVPSTimeConv[titleTimeIndx]+'-'+ \
                      str(tempRange) +'.txt'
    filein = open(tableNameSpec, "w+")
    filein.write('{z:<7}{q:<18}{a:<18}'.format\
                   (z='Bin', q='Bin_Size_Min(cm)', a='Spec_Conc(#/m^4)'))
    filein.write('\n\n')
    if new_spec_file_tracker == 'y': 
        for y in range(xaxis2.shape[0]):
            filein.write('{z:<7}{q:<18}{a:<18}'.format(z=int(y +1), q=float(xaxis2[y]), a=SpecPlotListsArray[x][y]))
            filein.write('\n')
    elif new_spec_file_tracker == 'n':
        for y in range(xaxis2.shape[0]):
            filein.write('{z:<7}{q:<18}{a:<18}'.format(z=int(y +1), q=float(xaxis2[y]), a=SpecPlotListsArray[x][y]))
            filein.write('\n')
    filein.close()
        
    
    #Creating HVPS table of concentrations
    #-------------------------------------
    tableNameHvps = "./PSD_Tables/" + file_created_date + "/Hvps_Conc_per_Bin_" + str(FlightDate) \
                    + '_' + HVPSTimeConv[titleTimeIndx]+'-'+ \
                      str(tempRange) +'.txt'
    filein = open(tableNameHvps, "w+")
    filein.write('{z:<7}{q:<18}{b:<18}'.format\
                   (z='Bin', q='Bin_Size_Min(cm)', b='Hvps_Conc(#/m^4)'))
    filein.write('\n\n')
    for y in range(xaxis3.shape[0]):
        filein.write('{z:<7}{q:<18}{b:<18}'.format(z=int(y +1), q=float(xaxis3[y]), b=HvpsPlotListsArray[x][y]))
        filein.write('\n')
    filein.close()
    
    
    #Plotting spectrometer and HVPS concentrations
    #---------------------------------------------
    plt.yscale("log")
    
    testidx = np.isfinite(np.log(SpecPlotListsArray[x]), where=True)
    testidx2 = np.isfinite(np.log(HvpsPlotListsArray[x]), where=True)

    if new_spec_file_tracker == 'y': 
        plt.scatter(xaxis2[testidx], SpecPlotListsArray[x][testidx], label='Spectrometer', s=500)
    elif new_spec_file_tracker == 'n':
        plt.scatter(xaxis2[testidx], SpecPlotListsArray[x][testidx], label='Spectrometer', s=500)

    plt.scatter(xaxis3[testidx2], HvpsPlotListsArray[x][testidx2], label='HVPS', s=500)

    plt.ylim(bottom=0)
    plt.xticks(fontsize=50) 
    plt.yticks(fontsize=50)       
    plt.xlabel("Bin Size (cm)", fontsize=50)
    plt.ylabel("Conc (#/m^4)", fontsize=50)
    plt.legend(fontsize=50)
    #plt.plot = np.polyfit(xaxis2, np.log(SpecPlotLists[x]), 1)
    #HVPSFit = np.polyfit(xaxis, np.log(HvpsPlotLists[x]), 1)
    plt.show()
    
    fig.savefig('./PSD_Plots/' + file_created_date + '/PSD_' + str(FlightDate)\
                    + '_' + HVPSTimeConv[titleTimeIndx]+'-'+ \
                      str(tempRange) + '.png')#, bbox_inches = 'tight')
    fig.clf()
    
    #Iterating up to next time range
    titleTimeIndx += int(1 * HvpsTimeRes)

"""
#testing reflectivity calc
#-------------------------
reflectivities = []
for x in SpecPlotLists:
    temp = []
    for y in range(len(x)):
        num = x[y] * (xaxis2[y]*10)**6
        temp.append(num)
    ref = 10 * np.log10(sum(temp))
    reflectivities.append(ref)
"""
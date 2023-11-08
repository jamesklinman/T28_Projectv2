# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 20:55:14 2023

@author: james.klinman

to run, make sure to set up:
    -File_Runner_Info.txt
    -*flightnum*_paramInfo.txt
"""

import subprocess
import os
import sys
import pandas as pd


flight_programs_file = 'Param_Info/File_Runner_Info.txt'
flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')
flight_num = str(flight_programs_info['flight_num'][0])
programs_to_use = flight_programs_info['programs_to_run']


param_file = 'Param_Info/' + flight_num + '_paramInfo.txt'
initParameters = pd.read_csv(param_file, sep=' * ', engine='python')


#Makes a list of the programs so that 
#they can be run in the correct order
#------------------------------------
program_list = []
for x in programs_to_use:
    program_list.append(x)

#This function runs a program for each time period.
#It does not work yet if it has to iterate over other variables.    
#---------------------------------------------------------------
def run_program(program_to_run):
    counter = 0
    number_of_time_periods = 0
    #Skip is 3 because of the way the paramInfo file is formatted. 
    #Likewise the counter%4 is a result of the formatting as well
    skip = 3
    for x in initParameters['Time_Start']:
        if counter%4 == 0:
            number_of_time_periods +=1
        counter+=1
    
    for time_period in range(number_of_time_periods):
        print(time_period)
        f = open('Automated_Files/Iteration_Tracker.txt', "w+")
        f.write('{a:<11}{b:<10}'.format(a='Iteration', b='Skip_Num'))
        f.write('\n')
        f.write('{a:<11}{b:<10}'.format(a=time_period, b=skip))
        f.close()
        
        #Running the program
        if aircraft_tracks_check == 'y':
            pass
        
        elif aircraft_plotting_check == 'y':
            num_of_vars_to_plot = 0
            for x in range(0, len(initParameters['Variables_Plot']), 3):
                if initParameters['Variables_Plot'][x] != '.':
                    num_of_vars_to_plot += 1
            #variable_iter_tracker -= 1
            
            variables_index = 0
            #honestly idk why rn but the +1 is important and makes it so the
            #code actually does all the plotting
            for x in range(num_of_vars_to_plot +1):
                f = open('Automated_Files/Variable_Tracker.txt', "w+")
                f.write('{c:<11}'.format(c='Variable_Iteration'))
                f.write('\n')
                f.write('{c:<11}'.format(c=variables_index))
                
                subprocess.call([sys.executable, program_to_run])
                
                variables_index += skip
            
        else:
            subprocess.call([sys.executable, program_to_run])


#All the programs that can be run as part of the processing package
#They are loosely ordered so that programs that need to be run first
#in order for other programs to function are run first
#-------------------------------------------------------------------
aircraft_plotting_check = None
aircraft_tracks_check = None

if 'Flight_Index_Finder.py' in program_list:
    run_program('Flight_Index_Finder.py')
    
if 'Aircraft_Track_Data.py' in program_list:
    run_program('Aircraft_Track_Data.py')

if 'Aircraft_Plotting.py' in program_list:
    aircraft_plotting_check = 'y'
    run_program('Aircraft_Plotting.py')
    aircraft_plotting_check = None
    #set to none so that it doesn't start the if loops again above

if 'Aircraft_Plots_Combined.py' in program_list:
    run_program('Aircraft_Plots_Combined.py')

if 'Aircraft_Tracks_Visualization.py' in program_list:
    aircraft_tracks_check = 'y'
    run_program('Aircraft_Tracks_Visualization.py')

if 'HVPS_Spectrometer_Comparison.py' in program_list:
    run_program('HVPS_Spectrometer_Comparison.py')

if 'Lat_Lon_Alt.py' in program_list:
    run_program('Lat_Lon_Alt.py')

if 'True_Airspeed.py' in program_list:
    run_program('True_Airspeed.py')

    
    
    
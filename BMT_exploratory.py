# -*- coding: utf-8 -*-
"""
Created on Thu May 30 11:57:33 2024

@author: rajnishk

This script is used to do exploratory analysis on BMT patients. 
"""

# Pick a random dyad from BMT group and plot their 

import cx_Oracle, string, getpass
import pandas as pd
import numpy as np
import datetime

import getpass
import oracledb
import cx_Oracle
import pickle
import pandas as pd
import matplotlib.pyplot as plt

# Enfore the DSN String has the service_name field instead of the SID
dsnStr = cx_Oracle.makedsn("abcd.abcd.med.umich.edu", "1521", service_name="abcd.abcd")
connection = oracledb.connect(
    user="userrname",
    password="password",
    dsn=dsnStr
)

print("Successfully connected to Oracle Database")


cursor = connection.cursor()

cur = cursor

subj = [1558,1561,1563,1572,1577,1613,1616,1650] 

N = len(subj)


# day is for 8am through 8pm
# daily is for the 24hrs
comp_day = pd.DataFrame()
comp_daily = pd.DataFrame()

# loop through the participants
for k in range(len(subj)):
    # get the device id of the participant k
    subjid = str(subj[k])
    
    # Fetch data from oracle database
    cur.execute("select STUDY_METRIC_MSR_VAL, STUDY_METRIC_MSR_START_DT from ROADMAP.STUDY_METRIC_HEARTRATE where PRTCPT_DVC_ID = "+subjid)
    rows = cur.fetchall()
    
    # Store data in pandas dataframe and rename variables
    df = pd.DataFrame(rows, columns = ['value', 'time'])
    
    # Change the type of the variables: value is an int32 and time is a datetime
    df.astype({'value': 'int32'})
    df.time = pd.to_datetime(df.time)
    
    # Sort the entire dataframe using the time 
    df.sort_values(by=['time'])
    
    # Get the number of days we have data for an individual, could be replace by study period (ex: 90)
    diff_days = df["time"].iloc[-1] - df["time"].iloc[0]
    number_days = round(diff_days/np.timedelta64(1,'D')) -1
    
    # initialize matrices that will contain the compliance values
    comp_daily_matrix = np.zeros(number_days)
    comp_day_matrix = np.zeros(number_days)
    
    # initialize values for the while loop below
    i_day = 0
    sum_minutes = 0
    sum_minutes_day = 0
    
    # nextday contains a datetime that will be updated to advance through the dates day by day
    nextday = df["time"].iloc[0] + datetime.timedelta(days=1)
    nextday = nextday.replace(hour=0, minute=0, second=0)
    
    # While loop will go through data day by day until it reaches the last day
    while nextday < df["time"].iloc[-1].replace(hour=0, minute=0, second=0):
        
        # t_mask contains the datetimes for one day
        t_mask = np.array(df["time"][(df["time"] >= nextday) & (df["time"] < (nextday + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0))])
        t_mask = np.sort(t_mask)
        
        # t_mask_day contains the datetimes for one day
        t_mask_day = np.array(df["time"][(df["time"] >= nextday + datetime.timedelta(hours = 8)) & (df["time"] < (nextday + datetime.timedelta(hours = 20)))])
        t_mask_day = np.sort(t_mask_day)
        
        # If these masks are not empty, it means we have some data for this day we can process
        if len(t_mask) != 0:
            
            # Identify the gaps in the datetimes, e.g., where are the gaps of non-wear time
            minutes_plus = np.array(t_mask[1:]) 
            minutes_minus = np.array(t_mask[0:-1]) 
            secdata = (minutes_plus-minutes_minus)/np.timedelta64(1,'s')
            gap_list = np.where((secdata > 60) & (secdata > 0))[0]
            
            # If the list of indices is not empty, it means there are gaps we need to take into account
            if len(gap_list) != 0:
                
                # Here we are counting the minutes before and after gaps
                # This line is to get data from the start to the first gap
                sum_minutes = sum_minutes + (t_mask[gap_list[0]] - t_mask[0])/np.timedelta64(1,'m')
                
                # Then, we loop into the set of gaps stored into (gap_list)
                for j in range(1,len(gap_list)):
                    
                    # limit: index of the gap j; limitminusone: index of previous gap + 1
                    limit = gap_list[j]
                    limitminusone = gap_list[j-1] + 1
                    
                    # These two indices could be the same, which means there would be some duplicates in the data
                    # there are sometimes
                    if limit != limitminusone:  
                        # Here we add the minutes between the gaps 
                        sum_minutes = sum_minutes + (t_mask[limit] - t_mask[limitminusone])/np.timedelta64(1,'m')
                    else:
                        # If there is a duplicate, we just add a minute
                        sum_minutes = sum_minutes + 1
                        
                # This line is to get data from the last gap to the end
                sum_minutes = sum_minutes + (t_mask[-1] - t_mask[gap_list[-1]+1])/np.timedelta64(1,'m')
            
            # Else if the list of indices is empty, there are no gaps and the person wore the sensor for the whole day
            else:
                sum_minutes = sum_minutes + (t_mask[-1] - t_mask[0])/np.timedelta64(1,'m')
            comp_daily_matrix[i_day] = sum_minutes*100/1440
        
        # If these masks are not empty, it means we have some data for this day we can process
        if len(t_mask_day) != 0:
            
            # Identify the gaps in the datetimes, e.g., where are the gaps of non-wear time
            minutes_plus = np.array(t_mask_day[1:]) 
            minutes_minus = np.array(t_mask_day[0:-1]) 
            secdata = (minutes_plus-minutes_minus)/np.timedelta64(1,'s')
            gap_list = np.where((secdata > 60) & (secdata > 0))[0]
            
            # If the list of indices is not empty, it means there are gaps we need to take into account
            if len(gap_list) != 0:
                
                # Here we are counting the minutes before and after gaps
                # This line is to get data from the start to the first gap
                sum_minutes_day = sum_minutes_day + (t_mask_day[gap_list[0]] - t_mask_day[0])/np.timedelta64(1,'m')

                # Then, we loop into the set of gaps stored into (gap_list)
                for j in range(1,len(gap_list)):
                    
                    # limit: index of the gap j; limitminusone: index of previous gap + 1
                    limit = gap_list[j]
                    limitminusone = gap_list[j-1] + 1
                    
                    # These two indices could be the same, which means there would be some duplicates in the data
                    # there are sometimes
                    if limit != limitminusone:  
                        # Here we add the minutes between the gaps 
                        sum_minutes_day = sum_minutes_day + (t_mask_day[limit] - t_mask_day[limitminusone])/np.timedelta64(1,'m')
                    else:
                        # If there is a duplicate, we just add a minute
                        sum_minutes_day = sum_minutes_day + 1
                        
                # This line is to get data from the last gap to the end
                sum_minutes_day = sum_minutes_day + (t_mask_day[-1] - t_mask_day[gap_list[-1]+1])/np.timedelta64(1,'m')
            # Else if the list of indices is empty, there are no gaps and the person wore the sensor for the whole day
            else:
                sum_minutes_day = sum_minutes_day + (t_mask_day[-1] - t_mask_day[0])/np.timedelta64(1,'m')
                
            comp_day_matrix[i_day] = sum_minutes_day*100/720
        
        
        # Once we found our value of compliance, we reinitilize the variables to start the loop again into 
        # the next day
        sum_minutes = 0
        sum_minutes_day = 0
        i_day = i_day + 1
        nextday = (nextday + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
    
    # Once we looped through all the days, we store the values for this subject
    comp_daily_new = pd.DataFrame({subjid:comp_daily_matrix})
    comp_day_new = pd.DataFrame({subjid:comp_day_matrix})
    
    comp_daily = pd.concat([comp_daily, comp_daily_new], axis=1)
    comp_day = pd.concat([comp_day, comp_day_new], axis=1)

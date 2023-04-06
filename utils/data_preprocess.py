import requests
import json
import pandas as pd
import numpy as np 

from datetime import datetime, timedelta, timezone
from tqdm import tqdm

import psychrolib # Library for WetBulb estimation 

def convert_str_double(arr):
    '''
    Convert the arr list to numpy array with double datatype
    and 
        Args:    arr
        Return:  arr_double
    '''
    # Find the indices of the missing values
    missing_indices = (arr =="M")
    
    # Create a copy of the array to avoid modifying the original
    arr_double = arr.copy()
    
    # Replace the "M" values to np.nan
    arr_double[missing_indices] = "0"
    arr_double = arr_double.astype(np.float)
    arr_double[missing_indices] = np.nan
    
    return arr_double

def fix_nan_value(arr):
    '''
    Replace the nan values by linear interpolation
    '''
    # Create a copy of the array to avoid modifying the original
    interpolated_arr = arr.copy()
    
    # Find the indices of the missing values
    missing_indices = np.isnan(arr)

    # Interpolate the missing values using linear interpolation
    interpolated_arr[missing_indices] = np.interp(
        np.flatnonzero(missing_indices),
        np.flatnonzero(~missing_indices),
        interpolated_arr[~missing_indices]
    )
    
    return interpolated_arr

def detect_missing_values(time_str_list):
    
    def convert_utc_timehour(time_str):
        # Convert to timestamp in hour, the input is the UTC time
        return int(round(datetime.strptime(time_str, '%Y-%m-%dT%H').replace(tzinfo=timezone.utc).timestamp()/3600))

    ts_start = convert_utc_timehour(time_str_list[0])
    ts_end   = convert_utc_timehour(time_str_list[-1])
    
    num_timestep = len(time_str_list)
    i           = 0
    miss_count  = 0
    missed_list = []
    
    while i < num_timestep:
        current_ts = convert_utc_timehour(time_str_list[i])
        
        if(current_ts - ts_start != i + miss_count):
            missed_ts    = ts_start + i + miss_count
            missed_time  = datetime.fromtimestamp((missed_ts)*3600)
            missed_str   = missed_time.astimezone(timezone.utc).strftime('%Y-%m-%dT%H')
        
            missed_list += [missed_str]    
            miss_count  += 1
        else:
            i +=1
    
    return missed_list

def convert_to_TWetBulb(drytemp_array, relh_array, pressuere):
    '''
    Estimate the WetBulbT based on the DryBulbT array and HumRatio array 
        Args: 
            drytemp_array : dry temperature array in °F [IP]
            relh_array    : relative Humidity in % 
            pressuere     : sea level pressure in millibar
        Return:
            wetBulb_array : wet bulb temperature array in °F [IP]
    '''
    
    # Set the unit system, for example to SI (can be either psychrolib.SI or psychrolib.IP)
    #  °F [IP] or °C [SI]
    psychrolib.SetUnitSystem(psychrolib.IP)
    
    assert len(drytemp_array) == len(relh_array)
    num_ins       = len(drytemp_array)
    wetBulb_array = np.zeros(num_ins)
    
    psi_mb_scale  = 0.0145037738
    
    for i in range(num_ins):
        drytemp = drytemp_array[i]
        relh    = relh_array[i]*0.01
        pres    = pressuere[i]*psi_mb_scale
        
        WetBulb = psychrolib.GetTWetBulbFromRelHum(drytemp, relh, pres)
        wetBulb_array[i] = WetBulb
    
    return wetBulb_array

def round_hour(date_str):
    '''
    Round the date str into the nearst hour, in order to match with EIA's data
        Args:   date_str  (e.g. "2022-01-01 00:53")
        Return: out_str   (e.g. '2022-01-01T01')
    '''
    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    rounded_date_obj = date_obj.replace(minute=0, second=0)
    if date_obj.minute >= 30:
        rounded_date_obj += timedelta(hours=1)
    
    return rounded_date_obj.strftime('%Y-%m-%dT%H')

def align_time(df_temper):
    '''
    Replace the time time into the EIA's datatype
    '''
    num_ins = df_temper.shape[0]
    converted_time = []
    for i in range(num_ins):
        org_date        = df_temper['valid'][i]
        converted_time += [round_hour(org_date)]
    
    return df_temper.assign(valid=converted_time)

def repair_single_fuel(df_i, dummy_head):
    '''
    Detect the missed time slots and insert NaN to these positions
    Args:
        df_i:        dataframe subset for a certain kind of feultype
        dummy_head:  series template
    Return:
        df_res:      dataframe after insertion
    '''
    time_str_list = df_i["period"].values.copy()
    missed_array  = detect_missing_values(time_str_list)
    
    dummy_head_i = dummy_head.copy()
    dummy_head_i["fueltype"]   = df_i["fueltype"].values[0]
    dummy_head_i["type-name"]  = df_i["type-name"].values[0]
    
    df_res    = df_i.copy()
    for missed_key in missed_array:
        dummy_head_i["period"]     = missed_key
        df_res = df_res.append(dummy_head_i)

    df_res = df_res.sort_values(['period', "fueltype"])
    
    return df_res

import requests
import json
import pandas as pd
import numpy as np 
from datetime import datetime, timedelta
from tqdm import tqdm

import matplotlib
import matplotlib.pyplot as plt

import psychrolib # Library for WetBulb estimation 


def download_online_data(region, start_time, end_time, api_key=None):
    
    if api_key is None:
        print("Please apply for a API key from https://www.eia.gov/opendata/")
        return []
    
    # Set the API endpoint URL
    url = 'https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/'

    # Set the request parameters (if any)
    params = {'api_key': api_key,
                "frequency":"hourly",
                "data[0]":"value",
                "facets[respondent][]":region,
                "start":start_time,
                "end":end_time,
                "sort[0][column]":"period",
                "sort[0][direction]":"desc",
                "offset":0,
                "length":5000
             }
    headers = {}

    # Make the HTTPS request
    response = requests.get(url, params=params, headers=headers)
    if response.status_code!= 200:
        print("Return Code  :  ", response.status_code)
        
    # Convert to dataframe
    json_object = json.loads(response.content)
    if 'warnings' in json_object["response"].keys():
        print(json_object["response"]['warnings'])
    df = pd.read_json(json.dumps(json_object['response']['data']))

    # Sort the array in ascending order
    sorted_df = df.sort_values(['period', "fueltype"])
    sorted_df = sorted_df.reset_index(drop=True)
    
    return sorted_df

def download_whole_year(year, loc_name, api_key):
    
    df_list = []
    region_code = loc_name
    # Loop through each month of the year
    for month in tqdm(range(1, 13)):
        # Get the last day of the month
        start_time = datetime(year, month, 1).strftime('%Y-%m-%dT00')
        end_time   = datetime(year, month, 15).strftime('%Y-%m-%dT23')

        df = download_online_data(region_code, start_time, end_time, api_key = api_key)
        df_list.append(df)

        start_time = datetime(year, month, 16).strftime('%Y-%m-%dT00')
        last_day = datetime(year, month, 1) + timedelta(days=32)
        last_day = last_day.replace(day=1) - timedelta(days=1)
        end_time = last_day.strftime('%Y-%m-%dT23')

        df = download_online_data(region_code, start_time, end_time, api_key = api_key)
        df_list.append(df)

    df_year = pd.concat(df_list).reset_index(drop=True)
    
    return df_year
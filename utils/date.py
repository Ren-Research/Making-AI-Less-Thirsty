from datetime import datetime, timedelta, timezone
import numpy as np 

def convert_to_str_days(data_str):
    base_date = datetime.strptime("2022-01-01T01", '%Y-%m-%dT%H')
    date_1    = datetime.strptime(data_str,        '%Y-%m-%dT%H')
    delta_t   = date_1 - base_date
    
    return delta_t.days

def convert_days_to_str(days):
    base_date = datetime.strptime("2022-01-01T01", '%Y-%m-%dT%H')
    delta_t   = timedelta(days=days)
    date_2    = base_date + delta_t
    
    return date_2.strftime('%Y-%m-%dT%H')
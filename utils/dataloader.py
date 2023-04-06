import pandas as pd
import numpy as np 

def load_indirect_WUE(fuel_mix_path, dc_loc):
    '''
    Indirect water
    Data source : A Review of Operational Water Consumption and
    Withdrawal Factors for Electricity Generating Technologies.
    
    +---------------+-------------+------+---------+-----+-------+-------+-------+------+
    |    FuelName   | Natrual Gas | Coal | Nuclear | Oil | Other | Solar | Hydro | Wind |
    +---------------+-------------+------+---------+-----+-------+-------+-------+------+
    |    FuelType   |      NG     |  COL |   NUC   | OIL |  OTH  |  SUN  |  WAT  |  WND |
    +---------------+-------------+------+---------+-----+-------+-------+-------+------+
    | WUE (gal/MWh) |     300     |  450 |   600   | 350 |  475  |   0   |   0   |   0  |
    +---------------+-------------+------+---------+-----+-------+-------+-------+------+
    
    Args:
        fuel_mix_path  : data path for the fuel mix csv file
        dc_loc         : data center location
    Return:
        indirectWue    : estimated average offsite water efficiency
        
    '''

    #### Texas Only, it only has 7 classes
    if dc_loc == "Texas":
        df          = pd.read_csv(fuel_mix_path)
        df_water    = df.reset_index(drop=True)

        # `fueltype` is already sorted, here is the sort result
        type_list   = ['COL', 'NG', 'NUC',  'OTH', 'SUN', 'WAT', 'WND']
        ewif_list   = [0.45,   0.3,   0.6,  0.475,  0.0,   0.0,     0]
        ewif_list   = np.array(ewif_list)*3.785412
    else:
        df          = pd.read_csv(fuel_mix_path)   #.drop("Unnamed: 0", axis=1)
        df_water    = df.reset_index(drop=True)

        # `fueltype` is already sorted, here is the sort result
        type_list   = ['COL', 'NG', 'NUC', 'OIL',  'OTH', 'SUN', 'WAT', 'WND']
        ewif_list   = [0.45,   0.3,   0.6,  0.35,  0.475,  0.0,   0.0,     0]
        ewif_list   = np.array(ewif_list)*3.785412

    total_energy = 0
    total_water  = 0

    for i,t in enumerate(type_list):
        total_water += df_water[df_water['fueltype'] == t]["value"].values * ewif_list[i]
        total_energy += df_water[df_water['fueltype'] == t]["value"].values


    indirectWue = total_water/total_energy
    
    return indirectWue

def load_carbon(fuel_mix_path, dc_loc):
    '''
    Carbon Estimation
    Source: It’s not easy being green (sigcomm)
    +-------------+-------------+------+---------+-----+-------+-------+-------+------+
    |   FuelName  | Natrual Gas | Coal | Nuclear | Oil | Other | Solar | Hydro | Wind |
    +-------------+-------------+------+---------+-----+-------+-------+-------+------+
    |   FuelType  |      NG     |  COL |   NUC   | OIL |  OTH  |  SUN  |  WAT  |  WND |
    +-------------+-------------+------+---------+-----+-------+-------+-------+------+
    | WUE (g/kWh) |     440     |  968 |    15   | 890 |  450  |   20  |  13.5 | 22.5 |
    +-------------+-------------+------+---------+-----+-------+-------+-------+------+
    Args:
        fuel_mix_path  : data path for the fuel mix csv file
        dc_loc         : data center location
    Return:
        carbon_curve   : estimated average carbon emission rate 
    '''

    #### Texas Only, it only has 7 classes
    if dc_loc == "Texas":
        df          = pd.read_csv(fuel_mix_path)
        df_carbon   = df.reset_index(drop=True)

        # `fueltype` is already sorted, here is the sort result
        type_list     = ['COL',  'NG',  'NUC',  'OTH',  'SUN',  'WAT', 'WND']
        carbon_list   = [0.968,  0.44,  0.015,   0.45,   0.02,  0.014, 0.023]

    else:
        df           = pd.read_csv(fuel_mix_path)   #.drop("Unnamed: 0", axis=1)
        df_carbon    = df.reset_index(drop=True)

        # `fueltype` is already sorted, here is the sort result
        type_list     = ['COL',  'NG',  'NUC',  'OIL',  'OTH', 'SUN', 'WAT',  'WND']
        carbon_list   = [0.968,  0.44,  0.015,   0.89,   0.45,  0.02, 0.014,  0.023]

    total_energy  = 0
    total_carbon  = 0

    for i,t in enumerate(type_list):
        total_carbon  += df_carbon[df_carbon['fueltype'] == t]["value"].values * carbon_list[i]
        total_energy  += df_carbon[df_carbon['fueltype'] == t]["value"].values


    carbon_curve = total_carbon/total_energy

    return carbon_curve



def load_direct_WUE(weather_path, wCycle = 6):
    '''
    Estimate on-site WUE from wetBulb temperature
    Args:
        weather_path : path for the weather csv data
        wCycle       : number of water cycles
    Return:
        directWue    : estimated on-site water for server cooling
    '''
    
    # 
    df = pd.read_csv(weather_path)
    df_temper = df[['valid', 'tmpf', 'dwpf', 'wbtmp']]
    # df_temper = df_temper

    dryBulbTemp  = np.array(df_temper["tmpf"].values, dtype=np.double)
    wetBulbTemp  = np.array(df_temper["wbtmp"].values, dtype=np.double)

    
    directWue = wCycle/(wCycle-1)*(6e-5* wetBulbTemp**3 - 0.01 * wetBulbTemp**2 + 0.61 * wetBulbTemp - 10.4);
    
    # Even though when the temperature is low, we still need 
    # a little bit water for moisture, e.g. 0.05
    return np.clip(directWue, 0.05, None)
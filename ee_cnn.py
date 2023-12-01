import ee
import geemap
import pandas as pd
import numpy as np
import gc
import math
import time
import datetime as dt
import keras
import keras as k
import keras.backend as kr
import multiprocessing as mp
from pysolar.solar import get_altitude_fast
import tensorflow as tf
import warnings
import xarray as xr
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
import rioxarray
import geopandas as gpd
import geojson
from shapely.geometry import Point
from scipy.spatial import KDTree
import datetime





def fetch_slv_data(start_date, end_date):
    collection_name = "NASA/GSFC/MERRA/slv/2"
    variables = ['PS', 'QV10M', 'Q500', 'Q850', 'T10M', 'T500', 'T850', 'U10M', 'V10M']


    # Convert the string date to a datetime object
    end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    # Add one day to the end date
    end_date_obj += datetime.timedelta(days=1)
    # Convert the datetime object back to a string
    end_date = end_date_obj.strftime("%Y-%m-%d")

    # Fetch the data
    collection = ee.ImageCollection(collection_name).filter(ee.Filter.date(start_date, end_date))
    data = collection.select(variables)

    return data

def fetch_aer_data(start_date, end_date):
    collection_name = "NASA/GSFC/MERRA/aer/2"
    variables = ['BCSMASS', 'DUSMASS25', 'OCSMASS', 'SO2SMASS', 'SO4SMASS', 'SSSMASS25', 'TOTEXTTAU']
    # Convert the string date to a datetime object
    end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    # Add one day to the end date
    end_date_obj += datetime.timedelta(days=1)
    # Convert the datetime object back to a string
    end_date = end_date_obj.strftime("%Y-%m-%d")
    # Fetch the data
    collection = ee.ImageCollection(collection_name).filter(ee.Filter.date(start_date, end_date))
    data = collection.select(variables)

    return data

def fetch_slv_data_hourly(date, hour):
    collection_name = "NASA/GSFC/MERRA/slv/2"
    variables = ['PS', 'QV10M', 'Q500', 'Q850', 'T10M', 'T500', 'T850', 'U10M', 'V10M']
    
    start_datetime = f"{date}T{hour:02d}:00"  # Start of the hour
    end_datetime = f"{date}T{hour:02d}:59"    # End of the hour
    
    # Fetch the data
    collection = ee.ImageCollection(collection_name).filter(ee.Filter.date(start_datetime, end_datetime)).first()
    data = collection.select(variables)

    return data

def fetch_aer_data_hourly(date, hour):
    collection_name = "NASA/GSFC/MERRA/aer/2"
    variables = ['BCSMASS', 'DUSMASS25', 'OCSMASS', 'SO2SMASS', 'SO4SMASS', 'SSSMASS25', 'TOTEXTTAU']
    
    start_datetime = f"{date}T{hour:02d}:00"  # Start of the hour
    end_datetime = f"{date}T{hour:02d}:59"    # End of the hour
    
    # Fetch the data
    collection = ee.ImageCollection(collection_name).filter(ee.Filter.date(start_datetime, end_datetime)).first()
    data = collection.select(variables)

    return data

# Process the data
def process_data(slv_data, aer_data,date_org):
  # Convert aerosol mass variables except TOTEXTTAU
  aer_data_wo_TOTEXTTAU = aer_data.select(['BCSMASS','DUSMASS25','OCSMASS','SO2SMASS', 'SO4SMASS','SSSMASS25']).multiply(1.0e9)
  aer_data = aer_data_wo_TOTEXTTAU.addBands(aer_data.select('TOTEXTTAU'))

  # Convert specific humidity variables
  slv_humidity = slv_data.select(['Q850','QV10M', 'Q500']).multiply(1000)
  slv_data = slv_data.select(['PS','T10M','T500','T850','U10M','V10M']).addBands(slv_humidity)

  # Calculate MERRA2
  MERRA2 = aer_data.select('DUSMASS25').add(
            aer_data.select('SSSMASS25')).add(
            aer_data.select('BCSMASS')).add(
            aer_data.select('OCSMASS')).add(
            aer_data.select('SO4SMASS').multiply(1.375))

  # Add MERRA2 to the aer_data Image
  aer_data = aer_data.addBands(MERRA2.rename('MERRA2'))

  # Combine slv_data and aer_data
  combined_data = slv_data.addBands(aer_data)



  # Calculate WIND (assuming you have U10M and V10M bands in your slv_data)
  WIND = slv_data.select('U10M').pow(2).add(slv_data.select('V10M').pow(2)).sqrt().rename('WIND')

  # Add WIND to combined_data
  combined_data = combined_data.addBands(WIND)

  # Create a mask where all bands are valid
  combined_mask = combined_data.reduce(ee.Reducer.min()).mask()

  # Apply the combined mask to the image
  combined_data = combined_data.updateMask(combined_mask)

  # Replace masked values with a placeholder value (e.g., -9999)
  combined_data = combined_data.unmask(-9999)


  # Add latitude and longitude bands
  latlon = ee.Image.pixelLonLat()



  # Reproject bands with different resolution
  latlon = latlon.reproject(crs='EPSG:4326', crsTransform=[0.625, 0, -180.5, 0, 0.5, -90.5])
  #latlon = latlon.reproject(crs='EPSG:4326', crsTransform=[0.5, 0, -180, 0, 0.5, -90])
  '''Not a viable solution for V3 lat lon problem as we need this reproject
  to match data to be able to combine bands'''

  # Add latitude and longitude bands
  combined_data = combined_data.addBands(latlon.select(['longitude', 'latitude']))

  return combined_data


def get_SZA(row):
   #print (row)
   time_obj = (pd.Timestamp(row[1],tz="utc")).to_pydatetime()
   lat, lon = row[2], row[3]
   return 90 - get_altitude_fast(lat, lon, time_obj)


def normalize(DF,mx,mn):
  range1 = (mx-mn)
  d = pd.DataFrame(((DF.values - mn.values)/range1.values),columns=DF.columns,index=DF.index)
  return d

def customLoss1(o,p):
  ioa = 1 -(k.sum((o-p)**2))/(k.sum((k.abs(p-k.mean(o))+k.abs(o-k.mean(o)))**2))
  return (-ioa)


def CNN(dates_list, coordinates=None, country = None):
    t1 = time.time()
    
    shape = False

    # Default region value
    region = {
        'type': 'Polygon',
        'coordinates': [[[-180, -90], [-180, 90], [180, 90], [180, -90], [-180, -90]]]
    }

    # Check for feature collection
    if country:
        print('A feature collection')
        region = country.geometry()

    elif coordinates:
        print('Checking Custom Type')  # Check if coordinates are provided

        # Check if it's a single pair (point)
        if isinstance(coordinates[0], (float, int)) and len(coordinates) == 2:
          print('Coordinates Selected')
          region = {
              'type': 'Point',
              'coordinates': coordinates
          }
            
            
        # Check if it's three or more pairs (polygon)
        elif isinstance(coordinates, list) and len(coordinates) >= 3:
          print('Custom Region')
          shape = True
          region = {
              'type': 'Polygon',
              'coordinates': [coordinates]
          }
            
            

    else:
      print('Caution World Region Selected, Extended Processing Time')
      



    # Check the length of dates_list
    if len(dates_list) == 1:
        start_date = dates_list[0]
        end_date = dates_list[0]
    else:
        start_date = dates_list[0]
        end_date = dates_list[-1]

    print(f"Fetching data from {start_date} to {end_date}")

    # Fetch data from Earth Engine
    #slv_data = fetch_slv_data(start_date, end_date)
    #aer_data = fetch_aer_data(start_date, end_date)

    batch_size = 512  # or any other value


    results = []
    '''for date_org in dates_list:
        print(f"Processing data for {date_org}")
        # Loop through each hour and fetch data
        
        for hour in range(24):
            hourly_data = slv_data.filter(ee.Filter.calendarRange(hour, hour, 'hour'))
            if hourly_data.size().getInfo() > 0:
                print(f"Data available for time: {hour}:30 UTC")

                if country:
                  # Filter the image collection for the specific date and hour timestamp
                  slv_image = slv_data.filter(ee.Filter.date(f"{date_org}T{hour:02d}:00", f"{date_org}T{hour:02d}:29")).first().clip(country)
                  aer_image = aer_data.filter(ee.Filter.date(f"{date_org}T{hour:02d}:00", f"{date_org}T{hour:02d}:29")).first().clip(country)
                elif shape:
                  slv_image = slv_data.filter(ee.Filter.date(f"{date_org}T{hour:02d}:00", f"{date_org}T{hour:02d}:29")).first().clip(region)
                  aer_image = aer_data.filter(ee.Filter.date(f"{date_org}T{hour:02d}:00", f"{date_org}T{hour:02d}:29")).first().clip(region)
                else:
                  slv_image = slv_data.filter(ee.Filter.date(f"{date_org}T{hour:02d}:00", f"{date_org}T{hour:02d}:29")).first()
                  aer_image = aer_data.filter(ee.Filter.date(f"{date_org}T{hour:02d}:00", f"{date_org}T{hour:02d}:29")).first()'''
                # Process the data
                #processed_data = process_data(slv_image, aer_image, date_org)

    for date_org in dates_list:
        print(f"Processing data for {date_org}")
        
        # Loop through each hour and fetch data
        for hour in range(24):
            
            # Fetch data from Earth Engine for the current hour
            slv_data_hourly = fetch_slv_data_hourly(date_org, hour)
            aer_data_hourly = fetch_aer_data_hourly(date_org, hour)
            
            # Check if data is available
            if slv_data_hourly:
                print(f"Data available for time: {hour}:30 UTC")
                            
                
                # Process the data
                processed_data = process_data(slv_data_hourly, aer_data_hourly, date_org)






                DF = geemap.ee_to_numpy(processed_data,
                                bands=['PS', 'QV10M', 'Q500','Q850', 'T10M', 'T500', 'T850','U10M','V10M','BCSMASS', 'DUSMASS25', 'OCSMASS', 'SO2SMASS', 'SO4SMASS', 'SSSMASS25', 'TOTEXTTAU', 'MERRA2', 'WIND', 'longitude','latitude'],
                                region = region,
                                properties=None,
                                default_value=-9999)
                column_names = ['PS', 'QV10M', 'Q500','Q850', 'T10M', 'T500', 'T850','U10M','V10M','BCSMASS', 'DUSMASS25', 'OCSMASS', 'SO2SMASS', 'SO4SMASS', 'SSSMASS25', 'TOTEXTTAU', 'MERRA2', 'WIND', 'longitude','latitude']
                reshaped_DF = DF.reshape(-1, DF.shape[2])
                DF = pd.DataFrame(reshaped_DF, columns=column_names)
                DF['Date'] =  pd.Timestamp(date_org)

                DF['SED'] = 1 - 0.01672 * np.cos(np.radians(0.9856 * (DF['Date'].dt.dayofyear - 4)))

                # Rename the columns
                DF.rename(columns={
                    'longitude': 'lon',
                    'latitude': 'lat'
                }, inplace=True)


                num_cores = mp.cpu_count()
                with mp.Pool(num_cores) as pool:
                    a = pool.imap(get_SZA, DF[["Date",'lat', 'lon']].itertuples(name=None), chunksize=10)
                    DF['SZA'] = [x for x in a]



                selected_columns = ['PS','QV10M','Q500','T10M','T500','T850', 'WIND',
                                    'BCSMASS','DUSMASS25','OCSMASS','SO2SMASS',
                                    'SO4SMASS','SSSMASS25','TOTEXTTAU','SED','SZA']

                DF.loc[DF['T850'] == -9999, 'T850'] = DF.loc[DF['T850'] == -9999, 'T10M']


                cols_2 = ['time','lat', 'lon',"MERRA2"]
                DF['time'] = date_org
                DF = DF[selected_columns+cols_2]
                print(DF)


              
                DP ="/content/drive/MyDrive/Colab Notebooks"
                SCALAR = DP + "/Scalars/"     # Universal Scalers
                MODEL = DP + "/Models/"
                zxc=pd.read_csv(SCALAR+"global_scalars2.csv",index_col=0)
                zxc = zxc.rename({"QV10m":"QV10M","T10m":"T10M"},axis=0)
                mx = zxc["max"]
                mn = zxc["min"]
                keras.losses.customLoss1 = customLoss1

                t2= time.time()-t1
                print (t2/60)
                



                ##########
                ### V1 ###
                ##########
                model = keras.models.load_model(MODEL+"V1_1t.h5", custom_objects={'customLoss1': customLoss1})
                DF["V1"]= model.predict(normalize(DF[selected_columns],mx[selected_columns],mn[selected_columns]),verbose=2,\
                batch_size=batch_size,use_multiprocessing=True)
                print ("V1 Done")


                ##########
                ### V2 ###
                ##########

                cols_test =['DUSMASS25','OCSMASS','SO2SMASS','SO4SMASS','SSSMASS25',]
                DF["V2_DS"]=DF[cols_test].idxmax(axis=1)
                DF["V2"]=np.nan
                for spec in cols_test:
                    print("V2", spec)

                    # Check if the subset is empty
                    subset_df = DF[DF.V2_DS == spec]
                    if subset_df.empty:
                        print(f"Skipping {spec} because the subset is empty.")
                        continue

                    model = keras.models.load_model(MODEL + "V2_1_" + spec + "t.h5", custom_objects={'customLoss1': customLoss1})
                    DF.V2[DF.V2_DS == spec] = model.predict(normalize(subset_df[selected_columns], mx[selected_columns], mn[selected_columns]), verbose=0,\
                    batch_size=batch_size, use_multiprocessing=True)[:, 0]

                print ("V2 Done")



                ##########
                ### V3 ###
                ##########


                # Load a CSV file into a pandas DataFrame, selecting only the columns 'MERRALat', 'MERRALon', and 'Rank_1'
                cats = pd.read_csv(SCALAR + "rankwise_v3.csv" )[['MERRALat','MERRALon',"Rank_1"]]
                # Rename the columns 'MERRALat' to 'lat', 'MERRALon' to 'lon', and 'Rank_1' to 'V3_DS'
                cats = cats.rename({'MERRALat':"lat", 'MERRALon':"lon","Rank_1":"V3_DS"},axis=1)
                # Extract unique values from the 'V3_DS' column and sort them
                unq_cats = sorted(list(cats['V3_DS'].unique()))



                # Merge the 'DF' DataFrame with the 'cats' DataFrame based on the columns 'lat' and 'lon'
                # create a combined key in both dataframes that represents the latitude and longitude as a tuple
                DF['lat_lon'] = list(zip(DF['lat'], DF['lon']))
                cats['lat_lon'] = list(zip(cats['lat'], cats['lon']))
                # Create a KDTree for cats
                #https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.html
                tree = KDTree(cats[['lat', 'lon']].values)
                # Find the index of the closest point in cats for each point in DF
                distances, indices = tree.query(DF[['lat', 'lon']].values)
                # Map the closest lat_lon from cats to DF
                DF['closest_lat_lon'] = cats['lat_lon'].iloc[indices].values
                DF = pd.merge(DF, cats, left_on='closest_lat_lon', right_on='lat_lon', suffixes=('', '_cats'))



                # Load another CSV file into a pandas DataFrame, setting the first column as the index
                zxc=pd.read_csv(SCALAR+"global_scalars2.csv",index_col=0)
                # Rename the rows (index) 'QV10m' to 'QV10M' and 'T10m' to 'T10M'
                zxc = zxc.rename({"QV10m":"QV10M","T10m":"T10M"},axis=0)
                # Extract the 'max' column from the 'zxc' DataFrame
                mx = zxc["max"]
                # Extract the 'min' column from the 'zxc' DataFrame
                mn = zxc["min"]
                # Create a new column 'V3' in the 'DF' DataFrame and initialize it with NaN values
                DF["V3"]=np.nan



                # Loop over each unique category in 'unq_cats'
                for spec in unq_cats:
                    print ("V3",spec)

                    # Check if the subset is empty
                    subset_df = DF[DF.V3_DS == spec]
                    if subset_df.empty:
                        print(f"Skipping {spec} because the subset is empty.")
                        continue

                    model = keras.models.load_model(MODEL+"V3_1_"+spec+"t.h5", custom_objects={'customLoss1': customLoss1})
                    normalized_data = normalize(DF[DF.V3_DS == spec][selected_columns], mx[selected_columns], mn[selected_columns])
                    #normalized_data = normalized_data.values.reshape(-1, 16, 1)
                    DF.V3[DF.V3_DS == spec]= model.predict(normalized_data,verbose=0,batch_size=batch_size,use_multiprocessing=True)[:,0]
                print ("V3 Done")


                #################
                ###### V4 #######
                #################

                cats = pd.read_csv(SCALAR + "rankwise_5cat.csv" )[['MERRALat','MERRALon',"Rank_1"]]
                cats = cats.rename({'MERRALat':"lat", 'MERRALon':"lon","Rank_1":"V4_DS"},axis=1)
                unq_cats = sorted(list(cats['V4_DS'].unique()))


                # create a combined key in both dataframes that represents the latitude and longitude as a tuple
                DF['lat_lon'] = list(zip(DF['lat'], DF['lon']))
                cats['lat_lon'] = list(zip(cats['lat'], cats['lon']))
                # Create a KDTree for cats
                #https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.html
                tree = KDTree(cats[['lat', 'lon']].values)
                # Find the index of the closest point in cats for each point in DF
                distances, indices = tree.query(DF[['lat', 'lon']].values)
                # Map the closest lat_lon from cats to DF
                DF['closest_lat_lon'] = cats['lat_lon'].iloc[indices].values
                DF = pd.merge(DF, cats, left_on='closest_lat_lon', right_on='lat_lon', suffixes=('', '_cats'))



                DF["V4"]=np.nan
                for spec in unq_cats:
                    print ("V4",spec)

                    # Check if the subset is empty
                    subset_df = DF[DF.V4_DS == spec]
                    if subset_df.empty:
                        print(f"Skipping {spec} because the subset is empty.")
                        continue

                    model = keras.models.load_model(MODEL+"V4_1_cat_"+spec+"t.h5", custom_objects={'customLoss1': customLoss1})
                    DF.V4[DF.V4_DS == spec]= model.predict(normalize(DF[DF.V4_DS == spec][selected_columns],mx[selected_columns],mn[selected_columns]),verbose=0,\
                    batch_size=batch_size,use_multiprocessing=True)[:,0]

                print ("V4 Done")


                #################
                ###### V5 #######
                #################


                zxc=pd.read_csv(SCALAR+"global_scalars3.csv",index_col=0)
                zxc = zxc.rename({"QV10m":"QV10M","T10m":"T10M"},axis=0)
                mx = zxc["max"]
                mn = zxc["min"]
                cats = pd.read_csv(SCALAR + "rankwise_4cat.csv" )[['MERRALat','MERRALon',"Rank_1"]]
                cats = cats.rename({'MERRALat':"lat", 'MERRALon':"lon","Rank_1":"V5_DS"},axis=1)
                unq_cats = sorted(list(cats['V5_DS'].unique()))


                # create a combined key in both dataframes that represents the latitude and longitude as a tuple
                DF['lat_lon'] = list(zip(DF['lat'], DF['lon']))
                cats['lat_lon'] = list(zip(cats['lat'], cats['lon']))
                # Create a KDTree for cats
                #https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.html
                tree = KDTree(cats[['lat', 'lon']].values)
                # Find the index of the closest point in cats for each point in DF
                distances, indices = tree.query(DF[['lat', 'lon']].values)
                # Map the closest lat_lon from cats to DF
                DF['closest_lat_lon'] = cats['lat_lon'].iloc[indices].values
                DF = pd.merge(DF, cats, left_on='closest_lat_lon', right_on='lat_lon', suffixes=('', '_cats'))



                DF["V5"]=np.nan
                for spec in unq_cats:
                    print ("V5",spec)

                    # Check if the subset is empty
                    subset_df = DF[DF.V5_DS == spec]
                    if subset_df.empty:
                        print(f"Skipping {spec} because the subset is empty.")
                        continue

                    model = keras.models.load_model(MODEL+"V5_1_cat_"+spec+"t.h5", custom_objects={'customLoss1': customLoss1})
                    DF.V5[DF.V5_DS == spec]= model.predict(normalize(DF[DF.V5_DS == spec][selected_columns],mx[selected_columns],mn[selected_columns]),verbose=0,\
                    batch_size=batch_size,use_multiprocessing=True)[:,0]

                print ("V5 Done")

                #################
                ###### V6 #######
                #################

                DF["Region"] = np.nan
                kk = 1
                step =45
                for i in range(-180,180,step):
                    for j in range (-90,90,step):
                        if j+step==90:
                            DF.Region[(DF.lat >= j) & (DF.lat <= j+step) &  (DF.lon >= i) & (DF.lon <= i+step)]=kk
                        else:
                            DF.Region[(DF.lat >= j) & (DF.lat < j+step) &  (DF.lon >= i) & (DF.lon < i+step)]=kk
                        kk=kk+1
                        #print (i,j,kk)

                DF.Region[DF.Region==1]=9
                DF.Region[DF.Region==2]=30
                DF.Region[DF.Region==5]=9
                DF.Region[DF.Region==6]=10
                DF.Region[DF.Region==13]=9
                DF.Region[DF.Region==14]=10
                DF.Region[DF.Region==17]=9
                DF.Region[DF.Region==18]=19
                DF.Region[DF.Region==21]=9
                DF.Region[DF.Region==25]=9
                DF.Region[DF.Region==29]=9
                DF.Region[DF.Region==31]=27
                DF.Region[DF.Region==32]=4
                unq_Reg = sorted(DF.Region.unique())
                print(unq_Reg)
                print(DF[DF['Region'].isna()])
                unq_Reg = [x for x in unq_Reg if not np.isnan(x)]



                zxc=pd.read_csv(SCALAR+"global_scalars3.csv",index_col=0)
                zxc = zxc.rename({"QV10m":"QV10M","T10m":"T10M"},axis=0)
                mx = zxc["max"]
                mn = zxc["min"]
                DF["V6"]=np.nan
                for i in unq_Reg:
                    model = keras.models.load_model(MODEL+'V6_1_reg_'+str(int(i))+"t.h5", custom_objects={'customLoss1': customLoss1})
                    DF.V6[DF.Region == i]= model.predict(normalize(DF[DF.Region == i][selected_columns],mx[selected_columns],mn[selected_columns]),verbose=0,\
                    batch_size=batch_size,use_multiprocessing=True)[:,0]
                print ("V6 Done")

                #################
                ###### V7 #######
                #################

                selected_columns = ['MERRA2', 'V1', 'V2','V3',  'V4','V5', 'V6']
                mx = DF[selected_columns].max() *0+1000
                mn = DF[selected_columns].max() *0
                model = keras.models.load_model(MODEL+"V7_1t.h5", custom_objects={'customLoss1': customLoss1})
                DF["V7"]= model.predict(normalize(DF[selected_columns],mx[selected_columns],mn[selected_columns]),verbose=0,
                batch_size=batch_size,use_multiprocessing=True)
                print ("V7 Done")


                #################
                ###### V8 #######
                #################
                selected_columns = ['MERRA2', 'V1', 'V2','V3',  'V4','V5']
                mx = DF[selected_columns].max() *0+1000
                mn = DF[selected_columns].max() *0
                model = keras.models.load_model(MODEL+"V8_1t.h5", custom_objects={'customLoss1': customLoss1})
                DF["V8"]= model.predict(normalize(DF[selected_columns],mx[selected_columns],mn[selected_columns]),verbose=0,\
                batch_size=batch_size,use_multiprocessing=True)
                print ("V8 Done")

                # Append DF w/ Date, hour and model result
                #DF['hour'] = hour # create column for current hour processed# Format the hour to be in the format 0030 to 2330
                formatted_hour = f"{str(hour).zfill(2)}:30"
                DF['Hour'] = formatted_hour
                DF['Date'] = DF['time']
                hourly_result = DF[['Date', 'Hour', 'V8','lat','lon']]
                results.append(hourly_result)

                # Clean up the hourly data to free up memory
                del slv_data_hourly, aer_data_hourly
                gc.collect()

            else:
              print(f"Data not available for time: {hour}:30 UTC")

    # Clean up
    final_df = pd.concat(results, ignore_index=True)
    # Convert the Date column to a datetime type
    final_df['Date'] = pd.to_datetime(final_df['Date'])
    final_df['Hour'] = pd.to_timedelta(final_df['Hour'] + ':00')
    final_df['Datetime'] = final_df['Date'] + final_df['Hour']
    # Rename the V8 column to PM2.5
    final_df.rename(columns={'V8': 'PM2.5'}, inplace=True)
    # drop the original Date and Hour columns
    final_df.drop(columns=['Date', 'Hour'], inplace=True)
    final_df.set_index('Datetime', inplace=True)
 
    #del slv_data, aer_data
    gc.collect()

    return final_df

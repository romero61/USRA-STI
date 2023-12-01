
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
import geemap.cartoee as cartoee
import datetime
import ipywidgets as widgets
from ipyleaflet import Map, DrawControl, GeoData, WidgetControl

from IPython.display import display, clear_output
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
service_account = 'yourusername@yourprojectname.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, 'your_.json_file_from_earth_engine_service_account')
# alternative run ee.authenticate() for a seven day token
ee.Initialize(credentials) 

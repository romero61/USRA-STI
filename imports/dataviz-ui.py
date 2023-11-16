import altair as alt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geemap
import ee
import ipywidgets as widgets
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from IPython.display import display, clear_output

class EarthEngineDataVizUI:
    def __init__(self, dataframe, coordinates=None, country=None):
        self.dataframe = dataframe
        self.coordinates = coordinates
        self.country = country
        self.shape = False
        self.world = False

        # Determine the type of region (point, polygon, or feature collection)
        self.determine_region_type()


        # Create dropdown for selecting the date
        self.date_options = ['All Days', 'Date Range'] + list(np.unique(self.dataframe.index.date))
        self.date_dropdown = widgets.Dropdown(
            options=self.date_options,
            description='Date:',
            disabled=False,
        )
        
        # Create date range picker for 'Date Range' option
        self.start_date_picker = widgets.DatePicker(
            description='Start Date:',
            disabled=True,
            layout=widgets.Layout(display='none')  # Initially hidden
    )

        self.end_date_picker = widgets.DatePicker(
            description='End Date:',
            disabled=True,
            layout=widgets.Layout(display='none')  # Initially hidden
        )


        # Visualization options
        viz_options = ['Time Series', 'Histogram']
        if self.shape:
            viz_options.insert(0, 'Contour Plot')
            viz_options.append('Geemap')
        
        # Create dropdown for selecting the visualization type
        self.viz_type_dropdown = widgets.Dropdown(
            options=viz_options,
            description='Visualization:',
            disabled=False,
        )
        
        # Create dropdown for selecting the hour (only for Map)
        hour_options = ['Average'] + [f"{str(i).zfill(2)}:30" for i in range(24)]
        self.hour_dropdown = widgets.Dropdown(
            options=hour_options,
            description='Hour:',
            disabled=True,
        )
        
        # Update hour dropdown visibility based on viz type
        def update_hour_dropdown(change):
            if change['new'] == 'Contour Plot':
                self.hour_dropdown.disabled = False
            else:
                self.hour_dropdown.disabled = True

        def update_date_pickers(change):
            if change['new'] == 'Date Range':
                self.start_date_picker.layout.display = 'flex'
                self.end_date_picker.layout.display = 'flex'
            else:
                self.start_date_picker.layout.display = 'none'
                self.end_date_picker.layout.display = 'none'

        self.date_dropdown.observe(update_date_pickers, names='value')        
        self.viz_type_dropdown.observe(update_hour_dropdown, names='value')

        # Create a button for generating the plot
        self.plot_button = widgets.Button(description="Generate Plot", button_style='info')
        self.plot_button.on_click(self.on_plot_button_clicked)

        # Create a button to show statistics
        self.stats_button = widgets.Button(description="Show Statistics", button_style='info')
        self.stats_button.on_click(self.on_stats_button_clicked)

        # Create an output widget to display the plot or statistics
        self.output = widgets.Output()

    def determine_region_type(self):
      # Check for feature collection
      if self.country:
          print("Country selected")
          self.shape = True
      elif self.coordinates:
          # Check if it's a single pair (point)
          if isinstance(self.coordinates[0], (float, int)) and len(self.coordinates) == 2:
              print("Point selected")
              self.shape = False
          # Check if it's three or more pairs (polygon)
          elif isinstance(self.coordinates, list) and len(self.coordinates) >= 3:
              print("Polygon selected")
              self.shape = True
      else:
          # If neither country nor coordinates are provided, consider it as global
          print("Global region selected")
          self.shape = True
          self.world = True



    def get_map_extent(self):
        if self.country:
            # Extract bounding box from the country's geometry
            bbox = self.country.geometry().bounds().getInfo()
            return [bbox['coordinates'][0][0][0], bbox['coordinates'][0][2][0], 
                    bbox['coordinates'][0][0][1], bbox['coordinates'][0][2][1]]
        elif self.coordinates:
            # If a custom region is selected, set the extent based on the region's bounding box
            lons = [coord[0] for coord in self.coordinates]
            lats = [coord[1] for coord in self.coordinates]
            return [min(lons), max(lons), min(lats), max(lats)]
        else:
            # Default global extent
            return [-180, 180, -90, 90]

    def on_plot_button_clicked(self, b):
        with self.output:
            clear_output(wait=True)
            selected_option = self.date_dropdown.value
            viz_type = self.viz_type_dropdown.value
            
            # Filter the dataframe based on user's selection
            if selected_option == 'All Days':
                filtered_df = self.dataframe
            elif selected_option == 'Date Range':
                start_date = self.start_date_picker.value
                end_date = self.end_date_picker.value
                mask = (self.dataframe.index.date >= start_date) & (self.dataframe.index.date <= end_date)
                filtered_df = self.dataframe[mask]
            else:
                selected_date = pd.to_datetime(selected_option)
                filtered_df = self.dataframe[self.dataframe.index.date == selected_date]
            
            if viz_type == 'Time Series':
                # Group by hour and calculate the mean
                avg_values = filtered_df.groupby(filtered_df.index.hour).mean()
                
                plt.plot(avg_values.index, avg_values['PM2.5'])
                plt.title('Average PM2.5 by Hour')
                plt.xlabel('Hour of the Day')
                plt.ylabel('Average PM2.5 Value')
                plt.show()
                    
            elif viz_type == 'Histogram':
                plt.hist(filtered_df['PM2.5'], bins=30, color='skyblue', edgecolor='black')
                plt.title('Histogram of PM2.5 Values')
                plt.xlabel('PM2.5 Value')
                plt.ylabel('Frequency')
                plt.show()
            

            
            
 
            elif viz_type == 'Contour Plot':
                # Filter the dataframe based on the selected hour (if not 'Average')
                if self.hour_dropdown.value != 'Average':
                    hour = int(self.hour_dropdown.value[:2])  # Extract the hour value from the string
                    filtered_df = filtered_df[filtered_df.index.hour == hour]
                elif self.hour_dropdown.value == 'Average':
                    # Group by latitude and longitude and calculate the mean for each group
                    filtered_df = filtered_df.groupby(['lat', 'lon']).mean().reset_index()

                # Check if filtered_df is empty
                if filtered_df.empty:
                    print("No data available for the selected criteria.")
                    return

                # Extract lats, lons, and values AFTER filtering
                lats = filtered_df['lat'].values
                lons = filtered_df['lon'].values
                values = filtered_df['PM2.5'].values

                fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()}, figsize=(10, 6))
                ax.set_extent(self.get_map_extent())
                ax.add_feature(cfeature.COASTLINE)
                ax.add_feature(cfeature.BORDERS, linestyle=':')
                ax.gridlines(draw_labels=True)
                contour = ax.tricontourf(lons, lats, values, transform=ccrs.PlateCarree(), cmap='turbo')
                cbar = plt.colorbar(contour, ax=ax, orientation='vertical', pad=0.05)
                cbar.set_label('PM2.5 Value')
                plt.title('Contour Plot of PM2.5 values')
                plt.show()
                
            elif viz_type == 'Geemap':
              
              if selected_option == 'All Days' or selected_option == 'Date Range':
                  # Group by latitude and longitude and calculate the mean for each group
                  filtered_df = filtered_df.groupby(['lat', 'lon']).mean().reset_index()
              elif selected_option != 'All Days' and selected_option != 'Date Range':
                  hour = int(self.hour_dropdown.value[:2])  # Extract the hour value from the string
                  filtered_df = filtered_df[filtered_df.index.hour == hour]
              
              # Check if filtered_df is empty
              if filtered_df.empty:
                  print("No data available for the selected criteria.")
                  return

              filtered_df.rename(columns={"PM2.5": "PM25"}, inplace=True)
              # Calculate the extent of the data
              min_lat, max_lat = filtered_df['lat'].min(), filtered_df['lat'].max()
              min_lon, max_lon = filtered_df['lon'].min(), filtered_df['lon'].max()
              # Predefined latitude and longitude bands
              lat_bands = [[-90, 0], [0, 90]]
              lon_bands = [[-180, -108], [-108, -36], [-36, 36], [36, 108], [108, 180]]

              # Create subsets based on the predefined bands
              subsets = []
              for lat_band in lat_bands:
                  for lon_band in lon_bands:
                      subset = filtered_df[
                          (filtered_df['lat'] >= lat_band[0]) & (filtered_df['lat'] <= lat_band[1]) &
                          (filtered_df['lon'] >= lon_band[0]) & (filtered_df['lon'] <= lon_band[1])
                      ]
                      subsets.append(subset)

              # Initialize a geemap Map
              Map = geemap.Map()
              Map.add_basemap('CartoDB.DarkMatter')
              
              if not self.world:
                min = 0
                max = float(self.dataframe['PM2.5'].max())
              else:
                min = 0
                max = 301


              



              # Initialize an empty ImageCollection
              image_collection = ee.ImageCollection([])
              turbo = [ "30123b", "321543", "33184a", "341b51", "351e58", "36215f", "372466", "38276d", 
                          "392a73", "3a2d79", "3b2f80", "3c3286", "3d358b", "3e3891", "3f3b97", "3f3e9c", 
                          "4040a2", "4143a7", "4146ac", "4249b1", "424bb5", "434eba", "4451bf", "4454c3", 
                          "4456c7", "4559cb", "455ccf", "455ed3", "4661d6", "4664da", "4666dd", "4669e0", 
                          "466be3", "476ee6", "4771e9", "4773eb", "4776ee", "4778f0", "477bf2", "467df4", 
                          "4680f6", "4682f8", "4685fa", "4687fb", "458afc", "458cfd", "448ffe", "4391fe", 
                          "4294ff", "4196ff", "4099ff", "3e9bfe", "3d9efe", "3ba0fd", "3aa3fc", "38a5fb", 
                          "37a8fa", "35abf8", "33adf7", "31aff5", "2fb2f4", "2eb4f2", "2cb7f0", "2ab9ee", 
                          "28bceb", "27bee9", "25c0e7", "23c3e4", "22c5e2", "20c7df", "1fc9dd", "1ecbda", 
                          "1ccdd8", "1bd0d5", "1ad2d2", "1ad4d0", "19d5cd", "18d7ca", "18d9c8", "18dbc5", 
                          "18ddc2", "18dec0", "18e0bd", "19e2bb", "19e3b9", "1ae4b6", "1ce6b4", "1de7b2", 
                          "1fe9af", "20eaac", "22ebaa", "25eca7", "27eea4", "2aefa1", "2cf09e", "2ff19b", 
                          "32f298", "35f394", "38f491", "3cf58e", "3ff68a", "43f787", "46f884", "4af880", 
                          "4ef97d", "52fa7a", "55fa76", "59fb73", "5dfc6f", "61fc6c", "65fd69", "69fd66", 
                          "6dfe62", "71fe5f", "75fe5c", "79fe59", "7dff56", "80ff53", "84ff51", "88ff4e", 
                          "8bff4b", "8fff49", "92ff47", "96fe44", "99fe42", "9cfe40", "9ffd3f", "a1fd3d", "a4fc3c", "a7fc3a", "a9fb39", "acfb38", 
                          "affa37", "b1f936", "b4f836", "b7f735", "b9f635", "bcf534", "bef434", "c1f334", 
                          "c3f134", "c6f034", "c8ef34", "cbed34", "cdec34", "d0ea34", "d2e935", "d4e735", 
                          "d7e535", "d9e436", "dbe236", "dde037", "dfdf37", "e1dd37", "e3db38", "e5d938", 
                          "e7d739", "e9d539", "ebd339", "ecd13a", "eecf3a", "efcd3a", "f1cb3a", "f2c93a", 
                          "f4c73a", "f5c53a", "f6c33a", "f7c13a", "f8be39", "f9bc39", "faba39", "fbb838", 
                          "fbb637", "fcb336", "fcb136", "fdae35", "fdac34", "fea933", "fea732", "fea431", 
                          "fea130", "fe9e2f", "fe9b2d", "fe992c", "fe962b", "fe932a", "fe9029", "fd8d27", 
                          "fd8a26", "fc8725", "fc8423", "fb8122", "fb7e21", "fa7b1f", "f9781e", "f9751d", 
                          "f8721c", "f76f1a", "f66c19", "f56918", "f46617", "f36315", "f26014", "f15d13", 
                          "f05b12", "ef5811", "ed5510", "ec530f", "eb500e", "ea4e0d", "e84b0c", "e7490c", 
                          "e5470b", "e4450a", "e2430a", "e14109", "df3f08", "dd3d08", "dc3b07", "da3907", 
                          "d83706", "d63506", "d43305", "d23105", "d02f05", "ce2d04", "cc2b04", "ca2a04", 
                          "c82803", "c52603", "c32503", "c12302", "be2102", "bc2002", "b91e02", "b71d02", 
                          "b41b01", "b21a01", "af1801", "ac1701", "a91601", "a71401", "a41301", "a11201", 
                          "9e1001", "9b0f01", "980e01", "950d01", "920b01", "8e0a01", "8b0902", "880802", 
                          "850702", "810602", "7e0502", "7a0403"
                          ]
              palette = ['green', 'yellow', 'orange', 'red', 'purple', 'maroon','maroon']
              aqi_breakpoints = [0, 50, 100, 150, 200, 300, 500]
              label = "Air Quality Index (AQI)"                          
              # Process each subset
              for idx, subset in enumerate(subsets):
                  print(f'Processing subset {idx+1}...')

                  if not subset.empty:
                      # Convert the DataFrame subset to an Earth Engine FeatureCollection
                      ee_fc = geemap.df_to_ee(subset, latitude='lat', longitude='lon')
                      # Convert the FeatureCollection to an Image for V8
                      v8_image = ee.Image(ee_fc.reduceToImage(['PM25'], ee.Reducer.first()))               


                      # Define a crsTransform for the desired pixel size
                      pixel_size = .63
                      crs_transform = [pixel_size, 0, min_lon, 0, -pixel_size, max_lat]
                      
                      # Reproject the image
                      v8_image_pixels = v8_image.reproject(crs='EPSG:4326', crsTransform=crs_transform)
                      
                      # Visualization parameters
                      v8_viz = {
                        'bands': ['first'],
                        'min': min,
                        'max': max,
                        'palette': palette,
                          'opacity': 0.87}


                      # Add the image to the ImageCollection
                      image_collection = image_collection.merge(ee.ImageCollection([v8_image_pixels]))

                      if self.world:
                           Map.addLayer(v8_image_pixels, v8_viz, f'PM25_{idx+1}')
      

              if not self.world:
                # Reduce the ImageCollection to a single image
                combined_image = image_collection.mosaic()
                Map.addLayer(combined_image, v8_viz, 'PM25')
                Map.center_object(ee_fc,4)
                display(Map)
              else:
                print('Multiple layers loaded to layer manager, decreased performance')
                Map.add_colorbar_branca(
                    colors=palette,
                    vmin=0,
                    vmax=301,
                    transparent_bg= True,
                    step = 50
                )
                display(Map)
                
        '''# Reduce the ImageCollection to a single image
        #combined_image = image_collection.reduce(ee.Reducer.first())
        combined_image = image_collection.mosaic()

        # Add the combined image to the map
        Map.addLayer(combined_image, v8_viz, 'PM25')
        Map.center_object(ee_fc,4)
        display(Map)'''



    def on_stats_button_clicked(self, b):
        with self.output:
            clear_output(wait=True)
            # Generate statistics for the dataset
            stats = self.dataframe['PM2.5'].describe()
            # Display the statistics
            display(stats)

    def on_geemap_button_clicked(self, b):
            with self.output:
                clear_output(wait=True)
                
    def display(self):
        # Display the dropdowns, date range picker, buttons, and output
        display(self.date_dropdown, self.start_date_picker, self.end_date_picker,\
        self.viz_type_dropdown, self.hour_dropdown, self.plot_button,\
        self.stats_button,  self.output)


'''elif viz_type == 'Scatter Plot':
  # Extract the hour from the Datetime index
  hours = filtered_df.index.hour
  
  plt.scatter(hours, filtered_df['PM2.5'])
  plt.title('Scatter Plot of PM2.5 Values')
  plt.xlabel('Hour of the Day')
  plt.ylabel('PM2.5 Value')
  
  # Optionally, you can set xticks to make it more readable
  plt.xticks(np.arange(0, 24, step=1))
  
  plt.show()
  
  
            if viz_type == 'Altair Hexbin Plot':
                hexbin = alt.Chart(filtered_df).mark_circle().encode(
                    alt.X('hour:O', bin=alt.Bin(maxbins=24)),
                    alt.Y('PM2.5:Q', bin=alt.Bin(maxbins=30)),
                    alt.Color('count()', scale=alt.Scale(scheme='inferno'))
                ).properties(
                    title='Hexbin Plot of PM2.5 Values',
                    width=400,
                    height=300
                )
                display(hexbin)

            elif viz_type == 'Altair Violin Plot':
                violin = alt.Chart(filtered_df).mark_area(
                    opacity=0.3,
                    interpolate='step'
                ).encode(
                    alt.X('PM2.5:Q', bin=alt.Bin(maxbins=50)),
                    alt.Y('hour:O'),
                    alt.Color('hour:O')
                ).properties(
                    title='Violin Plot of PM2.5 Values',
                    width=400,
                    height=300
                )
                display(violin)
            elif viz_type == 'Scatter Plot':
                # Check if 'index' is already a column in the DataFrame
                if 'index' not in filtered_df.columns:
                    s_df = filtered_df.reset_index(inplace=True)
                s_df['hour'] = s_df['index'].dt.hour
                
                # Create the Altair chart
                chart = alt.Chart(s_df).mark_circle().encode(
                    x='hour:O',  # 'O' stands for ordinal data
                    y='PM2.5:Q',  # 'Q' stands for quantitative data
                    tooltip=['hour', 'PM2.5']
                ).properties(
                    title='Scatter Plot of PM2.5 Values',
                    width=400,
                    height=300
                )
    
                display(chart)
                
                if viz_type == 'Hexbin Plot':
                # Convert the Datetime index to a column and extract the hour
                # Check if 'index' is already a column in the DataFrame
                if 'index' not in filtered_df.columns:
                  h_df = filtered_df
                  h_df.reset_index(inplace=True)
                  h_df['hour'] =  h_df['index'].dt.hour
                
                plt.hexbin(x= h_df['hour'], y= h_df['PM2.5'], gridsize=50, cmap='inferno')
                plt.colorbar(label='Density')
                plt.xlabel('Hour of the Day')
                plt.ylabel('PM2.5 Value')
                plt.title('Hexbin Plot of PM2.5 Values')
                plt.show()

            elif viz_type == 'Violin Plot':
                # Convert the Datetime index to a column and extract the hour
                # Check if 'index' is already a column in the DataFrame
                if 'index' not in filtered_df.columns:
                    v_df = filtered_df
                    v_df.reset_index(inplace=True)
                    v_df['hour'] = v_df['index'].dt.hour
                
                sns.violinplot(x='hour', y='PM2.5', data=v_df)
                plt.xlabel('Hour of the Day')
                plt.ylabel('PM2.5 Value')
                plt.title('Violin Plot of PM2.5 Values')
                plt.show()'''

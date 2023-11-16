import geemap
import ee
import ipywidgets as widgets
from IPython.display import display, clear_output, FileLink

class ExportUI:
    def __init__(self, dataframe):
        self.dataframe = dataframe
        self.final_df = dataframe

        # Create a button for downloading the data and style it
        self.download_button = widgets.Button(description="Download Data",\
        button_style='info')
        self.download_button.on_click(self.on_download_button_clicked)

        # Button for Asset Export
        self.asset_export_button = widgets.Button(description="Asset Export",\
        button_style='warning')
        self.asset_export_button.on_click(self.on_asset_export_button_clicked)

        # Button for Download TIFF
        self.download_tiff_button = widgets.Button(description="Download TIFF",\
        button_style='success')
        self.download_tiff_button.on_click(self.on_download_tiff_button_clicked)
        # Button for Google Drive
        self.download_drive_button = widgets.Button(description="Drive Export",\
         button_style='warning')
        self.download_drive_button.on_click(self.on_download_drive_button_clicked)


        
        # Output widget to display information
        self.output = widgets.Output()
           

    def on_download_button_clicked(self, b):
      with self.output:
          clear_output(wait=True)
          # Convert final_df to .csv
          if not self.final_df.empty:
            self.final_df.to_csv('output_data.csv', index=True)
          else:
              print("No data available to download!")

    def on_asset_export_button_clicked(self, b):
        with self.output:
            clear_output(wait=True)

            # Convert each subset to an Earth Engine FeatureCollection and export
            for idx, subset in enumerate(subsets):
                ee_fc = geemap.df_to_ee(subset, latitude='lat', longitude='lon')

                # Define the export parameters
                export_params = {
                    'collection': ee_fc,
                    'description': f'my_feature_collection_export_{idx}',
                    'assetId': f'users/usra/eight_cell/ee_fc_{idx}'
                }

                # Start the export
                export_task = ee.batch.Export.table.toAsset(**export_params)
                export_task.start()

                # Monitor the export task
                while export_task.status()['state'] in ['READY', 'RUNNING']:
                    print(export_task.status())
                    time.sleep(60)
                print(f'Export of subset {idx} completed.')

    def on_download_drive_button_clicked(self, b):
        with self.output:
            clear_output(wait=True)
            
            # Assuming you've already processed your subsets as before
            for idx, subset in enumerate(subsets):
                ee_fc = geemap.df_to_ee(subset, latitude='lat', longitude='lon')
                v8_image = ee.Image(ee_fc.reduceToImage(['PM25'], ee.Reducer.first()))
                
                # Exporting each subset to Google Drive
                task = ee.batch.Export.image.toDrive(
                    image=v8_image,
                    description=f'subset_{idx+1}',
                    folder='Your_Google_Drive_Folder_Name',
                    fileNamePrefix=f'subset_{idx+1}',
                    scale=30,
                    region=subset.geometry().bounds().getInfo(),
                    fileFormat='GeoTIFF'
                )
                task.start()
                print(f"Exporting subset {idx+1} to Google Drive...")

    def on_download_tiff_button_clicked(self, b):
        with self.output:
            clear_output(wait=True)
            
            # Assuming you've already processed your subsets and have a combined image
            # For simplicity, let's assume you're downloading the first subset
            ee_fc = geemap.df_to_ee(subsets[0], latitude='lat', longitude='lon')
            v8_image = ee.Image(ee_fc.reduceToImage(['PM25'], ee.Reducer.first()))
            
            # Generate a download URL
            url = v8_image.getDownloadURL({
                'scale': 30,
                'region': subsets[0].geometry().bounds().getInfo(),
                'fileFormat': 'GeoTIFF'
            })
            
            print(f"Download TIFF file from the following link: {url}")

    def display(self):
        display( widgets.HBox([self.download_button,self.download_tiff_button,\
        self.asset_export_button, self.download_drive_button, self.output]))


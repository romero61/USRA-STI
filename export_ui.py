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

   

    def display(self):
        display( widgets.HBox([self.download_button, self.output]))


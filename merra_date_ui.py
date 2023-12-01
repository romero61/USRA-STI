# merra_date_ui.py

import ee
import ipywidgets as widgets
from IPython.display import display

class MerraDateUI:
    def __init__(self):
        self.selected_dates = None
        self.available_dates = None
        self._initialize_ui()

    def _initialize_ui(self):
        # Create two date picker widgets
        self.start_date_picker = widgets.DatePicker(
            description='Start Date',
            disabled=False
        )

        self.end_date_picker = widgets.DatePicker(
            description='End Date',
            disabled=False
        )

        # Create a button to fetch available MERRA dates
        self.fetch_dates_button = widgets.Button(
            description="Fetch MERRA Dates",
            button_style="info",
            tooltip="Click to fetch available MERRA dates",
        )
        self.fetch_dates_button.on_click(self.on_fetch_dates_click)

        # Create a Text widget to display available dates
        self.dates_output = widgets.Textarea(
            value='',
            placeholder="Available MERRA dates will be displayed here.",
            description='Dates:',
            disabled=True,
            layout=widgets.Layout(height='150px')
        )

        # Layout the widgets vertically
        self.vbox = widgets.VBox([self.start_date_picker, self.end_date_picker, self.fetch_dates_button, self.dates_output])

    def on_fetch_dates_click(self, b):
        start_date_str = self.start_date_picker.value.strftime('%Y-%m-%d')
        end_date_str = self.end_date_picker.value.strftime('%Y-%m-%d')
        self.available_dates = self.get_available_merra_dates(start_date_str, end_date_str)
        self.dates_output.value = "\n".join(self.available_dates)

    def get_available_merra_dates(self, start_date_str, end_date_str):
        """
        Returns a list of unique dates with available MERRA images in the specified collection between the start and end dates.

        Parameters:
        - start_date_str: The start date in the format 'YYYY-MM-DD'.
        - end_date_str: The end date in the format 'YYYY-MM-DD'.

        Returns:
        - A list of strings representing the available unique dates in the format 'YYYY-MM-DD'.
        """
        # Load the MERRA collection
        collection = ee.ImageCollection("NASA/GSFC/MERRA/slv/2")

        # Filter the collection by the specified date range
        filtered_collection = collection.filterDate(start_date_str, end_date_str)

        try:
            # Extract the system:index property for each image in the filtered collection
            indices = filtered_collection.aggregate_array('system:index').getInfo()

            # Check if indices are empty
            if not indices:
                print(f"No data available between {start_date_str} and {end_date_str}")
                return []

            # Convert the indices to a list of dates in the format 'YYYY-MM-DD'
            dates = [index[:4] + "-" + index[4:6] + "-" + index[6:8] for index in indices]

            # Convert the list of dates to a set to remove duplicates, then convert it back to a list
            unique_dates = list(set(dates))

            # Sort the list of unique dates
            unique_dates.sort()

            # Print the unique dates and return the list
            for date in unique_dates:
                print(date)

            return unique_dates

        except ee.EEException as e:
            print(f"Error occurred while fetching data between {start_date_str} and {end_date_str}, ee.EEException: {e} ")
            return []
    
    def display_ui(self):
        return self.vbox

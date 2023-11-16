import ipywidgets as widgets
from IPython.display import display, clear_output
from ee_cnn import CNN 

class EarthEngineUI:
    def __init__(self, available_dates=None, selected_coordinates=None, selected_country_feature=None):
        self.available_dates = available_dates
        self.selected_coordinates = selected_coordinates
        self.selected_country_feature = selected_country_feature

        # Create a button for running the model and style it
        self.run_button = widgets.Button(description="Run Model", button_style='danger')
        self.run_button.on_click(self.on_run_button_clicked)

        # Create an output widget to display messages
        self.output = widgets.Output()

    def on_run_button_clicked(self, b):
        with self.output:
            clear_output(wait=True)
            # Call your CNN function here
            self.final_df = CNN(dates_list=self.available_dates, 
                                coordinates=self.selected_coordinates, 
                                country=self.selected_country_feature)
            print("Model run complete!")


    def display(self):
        # Display the buttons and output
        display(self.run_button,  self.output)

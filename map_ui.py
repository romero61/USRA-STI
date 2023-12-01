# map-ui.py
import ee
import geemap
import ipywidgets as widgets
from ipyleaflet import WidgetControl, DrawControl
from IPython.display import display

class MapUI:
    def __init__(self):
        self.selected_coordinates = None
        self.selected_country_feature = None
        self.map = geemap.Map()
        self.last_country_layer = None
        self._initialize_ui()

    def _initialize_ui(self):
        countries = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
        country_names = sorted(list(set(countries.aggregate_array('country_na').getInfo())))
        style = {'description_width': 'initial'}

        country_dropdown = widgets.Dropdown(
            options=country_names,
            description='Select Country:',
            disabled=False,
            button_style='primary',
            style=style
        )

        

        def on_country_change(change):
            country_name = change['new']
            country_feature = countries.filter(ee.Filter.eq('country_na', country_name))
            country_geometry = country_feature.geometry().getInfo()
            self.selected_coordinates = country_geometry['coordinates'][0]
            self.selected_country_feature = country_feature

            # Hide the 'Countries' layer
            countries_layer = self.map.find_layer('Countries')
            if countries_layer:
                countries_layer.visible = False

            # Hide the last added country layer
            if self.last_country_layer:
                self.map.find_layer(self.last_country_layer).visible = False

            # Check if the country layer already exists, if not, add it
            existing_layer = self.map.find_layer(country_name)
            if existing_layer:
                existing_layer.visible = True
            else:
                self.map.addLayer(country_feature, {}, country_name)

            # Update the last added country layer
            self.last_country_layer = country_name

            # Center the map on the selected country
            self.map.centerObject(country_feature, 4)  
                # Update the textarea_widget with the name of the selected country
            self.textarea_widget.value = f"Selected Country: {country_name}\nCoordinates: {self.selected_coordinates}"

        country_dropdown.observe(on_country_change, names='value')
        self.map.addLayer(countries, {}, 'Countries')

        # Create a Text widget and assign it to the class attribute
        self.textarea_widget  = widgets.Textarea(
            value='',
            placeholder= ("Country Coordinates loaded from country selection.\n\nFor point, rectangle or custom shapes use tools on left"),
            description='Text:',
            disabled=True,
            style = style,
            layout = widgets.Layout(height='100px', color = 'blue')
        )

        # Wrap the Text widget in a WidgetControl and Add the WidgetControl to the map
        text_control = WidgetControl(widget=self.textarea_widget , position='bottomright')
        self.map.add_control(text_control)



        # Create a button to clear the drawn shapes
        clear_button = widgets.Button(
            description="Clear Shapes",
            button_style="danger",
            tooltip="Click to clear the drawn shapes",
            style=style,
        )

         # Connect the clear_button to the on_clear_click function
        clear_button.on_click(self.on_clear_click)

        # Attach the handle_draw function to the draw control of geemap
        self.map.draw_control.on_draw(self.handle_draw)

        # Add the buttons to an output widget and then to the map
        output_widget = widgets.Output(layout={'border': '4px solid blue'})
        with output_widget:
            display(country_dropdown)
            display(clear_button)
        output_control = WidgetControl(widget=output_widget, position='topright')
        self.map.add_control(output_control)
       


    def handle_draw(self, target, action, geo_json):
        """
        Handle drawn shapes on the map and extract their coordinates.
        """
        if action == 'created':
            if geo_json['geometry']['type'] == 'Point':
                self.selected_coordinates = geo_json['geometry']['coordinates']
            else:
                self.selected_coordinates = geo_json['geometry']['coordinates'][0]
            self.textarea_widget.value = str(self.selected_coordinates)
            self.selected_country_feature = None  # Reset the country code when a shape or point is drawn


    def on_clear_click(self, b):
        # Clear all drawn shapes
        self.map.draw_control.clear()

        # Reset the textarea widget
        self.textarea_widget.value = ""



    # Display the map
    def display_map(self):
        return self.map
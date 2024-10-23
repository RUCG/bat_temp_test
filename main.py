# main.py

import pandas as pd
from database import extract_inlet_outlet_flow, extract_temperatures_and_sensor_numbers
from interactive import interactive_battery_layout
from settings import load_config  # Import only the load function

# Main function
def main(config):
    # Load the lookup table
    lookup_table = pd.read_csv(config['lookup_table_path'])

    # Define the configuration parameters
    sensors_per_module = 2
    strings_count = 3

    # Extract data from the database
    temperatures, sensor_numbers = extract_temperatures_and_sensor_numbers(config['db_path'], lookup_table, config['file_id'])
    inlet_temp, outlet_temp, flow = extract_inlet_outlet_flow(config['db_path'], config['file_id'], lookup_table)

    # Check and display the interactive layout if temperatures are found
    if len(temperatures) > 0:
        interactive_battery_layout(temperatures, sensor_numbers, sensors_per_module, strings_count, config['custom_sensor_order'], inlet_temp, outlet_temp, flow)
    else:
        print("No temperature data found.")

if __name__ == "__main__":
    # Load configuration from JSON
    config = load_config()

    # Run the main function with the loaded configuration
    main(config)
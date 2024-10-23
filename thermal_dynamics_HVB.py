import tkinter as tk
from tkinter import ttk
import pandas as pd
from tkinter import messagebox
from database import extract_inlet_outlet_flow, extract_temperatures_and_sensor_numbers
from interactive import interactive_battery_layout

# Static sensor order (could be moved to a configuration file if needed)
custom_sensor_order = [
    # Layer 1
    32, 31, 30, 29, 28, 27, 26, 25,
    17, 18, 19, 20, 21, 22, 23, 24, 
    16, 15, 14, 13, 12, 11, 10, 9,
    1, 2, 3, 4, 5, 6, 7, 8,
    # Layer 2
    48, 47, 46, 45, 44, 43, 42, 41, 
    33, 34, 35, 36, 37, 38, 39, 40, 
    64, 63, 62, 61, 60, 59, 58, 57, 
    49, 50, 51, 52, 53, 54, 55, 56, 
    # Layer 3
    96, 95, 94, 93, 92, 91, 90, 89, 
    81, 82, 83, 84, 85, 86, 87, 88, 
    80, 79, 78, 77, 76, 75, 74, 73, 
    65, 66, 67, 68, 69, 70, 71, 72
]

def main(db_path, lookup_table_path, file_id):
    # Load the lookup table
    lookup_table = pd.read_csv(lookup_table_path)

    # Define the configuration parameters
    sensors_per_module = 2
    strings_count = 3

    # Extract data from the database
    temperatures, sensor_numbers = extract_temperatures_and_sensor_numbers(db_path, lookup_table, file_id)
    inlet_temp, outlet_temp, flow = extract_inlet_outlet_flow(db_path, file_id, lookup_table)

    # Check and display the interactive layout if temperatures are found
    if len(temperatures) > 0:
        interactive_battery_layout(temperatures, sensor_numbers, sensors_per_module, strings_count, custom_sensor_order, inlet_temp, outlet_temp, flow)
    else:
        print("No temperature data found.")

if __name__ == "__main__":
    # Define file paths
    db_path = "mf4_data.db"
    lookup_table_path = "db_lookup_table.csv"
    file_id = "TCP0014_Run17_01.MF4"

    # Run the main function
    main(db_path, lookup_table_path, file_id)
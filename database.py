import sqlite3
import numpy as np

def extract_temperatures_and_sensor_numbers(db_path, lookup_table, file_id_value):
    all_temperatures = []
    sensor_numbers = []
    min_length = None
    processed_sensors = set()

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Filter lookup table entries matching the current `file_id`
        signal_info = lookup_table[lookup_table['File.ID'] == file_id_value]
        relevant_tables = set(signal_info['Table.Name'])

        for index, row in signal_info.iterrows():
            table_name = row['Table.Name']
            signal_name = row['Channel.Name']
            sensor_number = row['SensorNumber']

            # Skip sensor numbers 102 (outlet) and 103 (coolant flow)
            if sensor_number in processed_sensors or sensor_number in [102, 103]:
                continue

            if table_name in relevant_tables:
                query = f"SELECT {signal_name} FROM {table_name} WHERE file_id = ?"
                try:
                    cursor.execute(query, (file_id_value,))
                    data = cursor.fetchall()
                    temperatures = [temp_row[0] for temp_row in data if temp_row[0] is not None]

                    if temperatures:
                        all_temperatures.append(temperatures)
                        sensor_numbers.append(sensor_number)
                        processed_sensors.add(sensor_number)

                    if temperatures and (min_length is None or len(temperatures) < min_length):
                        min_length = len(temperatures)

                except Exception as e:
                    print(f"Error processing signal {signal_name} in table {table_name}: {e}")
                    all_temperatures.append([])
                    sensor_numbers.append(None)
                    
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

    if min_length is None:
        min_length = 0

    all_temperatures_trimmed = [temps[:min_length] for temps in all_temperatures]
    return np.array(all_temperatures_trimmed), sensor_numbers

def extract_inlet_outlet_flow(db_path, file_id_value, lookup_table):
    conn = None
    inlet_temperature = []
    outlet_temperature = []
    coolant_flow = []
    
    try:
        print(f"Connecting to database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"Looking up inlet, outlet, and flow for file ID: {file_id_value}")

        # Get all entries for inlet, outlet temperatures, and coolant flow matching the `file_id`
        inlet_info_list = lookup_table[(lookup_table['File.ID'] == file_id_value) & (lookup_table['SensorNumber'] == 101)]
        outlet_info_list = lookup_table[(lookup_table['File.ID'] == file_id_value) & (lookup_table['SensorNumber'] == 102)]
        flow_info_list = lookup_table[(lookup_table['File.ID'] == file_id_value) & (lookup_table['SensorNumber'] == 103)]

        # Extract inlet temperature
        for index, inlet_info in inlet_info_list.iterrows():
            inlet_table = inlet_info['Table.Name']
            inlet_column = inlet_info['Channel.Name']

            query = f"SELECT {inlet_column} FROM {inlet_table} WHERE file_id = ?"
            cursor.execute(query, (file_id_value,))
            inlet_temperature = [temp[0] for temp in cursor.fetchall() if temp[0] is not None]

            if inlet_temperature:
                break  # Stop once data is found

        # Extract outlet temperature
        for index, outlet_info in outlet_info_list.iterrows():
            outlet_table = outlet_info['Table.Name']
            outlet_column = outlet_info['Channel.Name']

            query = f"SELECT {outlet_column} FROM {outlet_table} WHERE file_id = ?"
            cursor.execute(query, (file_id_value,))
            outlet_temperature = [temp[0] for temp in cursor.fetchall() if temp[0] is not None]

            if outlet_temperature:
                break  # Stop once data is found

        # Extract coolant flow
        for index, flow_info in flow_info_list.iterrows():
            flow_table = flow_info['Table.Name']
            flow_column = flow_info['Channel.Name']

            query = f"SELECT {flow_column} FROM {flow_table} WHERE file_id = ?"
            cursor.execute(query, (file_id_value,))
            coolant_flow = [flow[0] for flow in cursor.fetchall() if flow[0] is not None]

            if coolant_flow:
                break  # Stop once data is found

    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            print("Closing database connection.")
            conn.close()
    
    return inlet_temperature, outlet_temperature, coolant_flow
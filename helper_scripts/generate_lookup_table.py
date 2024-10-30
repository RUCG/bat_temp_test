import sqlite3
import re
import pandas as pd

# Connect to the SQLite database
db_path = '/Users/gian/Documents/bat_temp_test/mf4_data.db'  # Path to your SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all table names from the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Regular expression to filter the desired signals
pattern = re.compile(r'^moduleTemperature(\d+)_BMS(01|05)$', re.IGNORECASE)

# Additional column names for inlet, outlet temperatures, and coolant flow
inlet_outlet_columns = ['VCU_AI_BatTempIn_Mean', 'VCU_AI_BatTempOut_Mean']
coolant_flow_signal = 'VCU_AI_ClntFlow_Mean'  # Signal name for coolant flow

# List to store the found signals
found_columns = []

# Iterate through all tables and search for matching columns
for table in tables:
    table_name = table[0]
    
    # Get all column names of the current table
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    # Check if the table has a 'file_id' column (assuming there is one)
    file_id_column = any('file_id' in column[1].lower() for column in columns)
    
    # Check each column if it matches the pattern or is a special signal
    for column in columns:
        column_name = column[1]
        match = pattern.match(column_name)
        
        if match:  # Check if the column name matches the pattern
            sensor_number = int(match.group(1))  # Extract sensor number from the name
            bms_id = match.group(2)  # Extract BMS_ID from the name
            
            # If there is a 'file_id', add it
            if file_id_column:
                # Get distinct 'file_id' values for the current table
                cursor.execute(f"SELECT DISTINCT file_id FROM {table_name}")
                file_ids = cursor.fetchall()
                
                for file_id in file_ids:
                    found_columns.append((column_name, table_name, sensor_number, bms_id, file_id[0]))
            else:
                found_columns.append((column_name, table_name, sensor_number, bms_id, None))

        # Check for inlet and outlet temperature columns
        elif column_name in inlet_outlet_columns:
            # Add them with a special sensor number code, e.g., 101 for inlet and 102 for outlet
            sensor_number = 101 if 'In_Mean' in column_name else 102
            bms_id = None  # No BMS_ID available
            if file_id_column:
                cursor.execute(f"SELECT DISTINCT file_id FROM {table_name}")
                file_ids = cursor.fetchall()
                for file_id in file_ids:
                    # Check if there are valid (non-NULL) entries
                    cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL AND file_id = ? LIMIT 1", (file_id[0],))
                    if cursor.fetchone():
                        found_columns.append((column_name, table_name, sensor_number, bms_id, file_id[0]))
            else:
                # Check if there are valid (non-NULL) entries
                cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 1")
                if cursor.fetchone():
                    found_columns.append((column_name, table_name, sensor_number, bms_id, None))

        # Check for the coolant flow signal
        elif column_name == coolant_flow_signal:
            sensor_number = 103  # Use sensor number 103 for coolant flow signal
            bms_id = None  # No BMS_ID available
            print(f"Found coolant flow signal '{coolant_flow_signal}' in table '{table_name}'")
            
            if file_id_column:
                cursor.execute(f"SELECT DISTINCT file_id FROM {table_name}")
                file_ids = cursor.fetchall()
                for file_id in file_ids:
                    # Check if there are valid (non-NULL) entries for coolant flow
                    cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL AND file_id = ? LIMIT 1", (file_id[0],))
                    if cursor.fetchone():  # Only add if there are non-NULL values
                        found_columns.append((column_name, table_name, sensor_number, bms_id, file_id[0]))
            else:
                # Check if there are valid (non-NULL) entries for coolant flow
                cursor.execute(f"SELECT 1 FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 1")
                if cursor.fetchone():
                    found_columns.append((column_name, table_name, sensor_number, bms_id, None))

# Convert results into a DataFrame
df = pd.DataFrame(found_columns, columns=['Channel.Name', 'Table.Name', 'SensorNumber', 'BMS_ID', 'File.ID'])

# Sort the DataFrame by BMS_ID and SensorNumber
df = df.sort_values(by=['BMS_ID', 'SensorNumber']).reset_index(drop=True)

# Save the DataFrame as a Parquet file
output_parquet = '/Users/gian/Documents/GitHub/bat_temp_test/db_lookup_table.parquet'
df.to_parquet(output_parquet, index=False)

print(f"Found signals have been saved to '{output_parquet}'.")

# Close the connection
conn.close()
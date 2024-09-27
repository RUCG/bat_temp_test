import sqlite3
from asammdf import MDF
import os
from tqdm import tqdm  # Import the tqdm library for progress display

# Directory containing the MF4 files
logs_directory = "testrun_logs"

# Check if the directory exists
if not os.path.exists(logs_directory):
    print(f"The directory '{logs_directory}' does not exist. Please check the path.")
    exit()

# Search for all MF4 files in the specified directory and its subdirectories
file_paths = []
for root, dirs, files in os.walk(logs_directory):
    for file in files:
        if file.endswith(".MF4"):
            file_paths.append(os.path.join(root, file))

# Check if any files were found
if not file_paths:
    print(f"No MF4 files found in the directory '{logs_directory}'.")
    exit()

# Connect to the SQLite database
db_path = "mf4_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Error logging
error_log = []

# Function to create or update a table for a group with a 'file_id' column
def create_or_update_table(group_name, channels):
    cursor.execute(f"PRAGMA table_info({group_name})")
    columns_info = cursor.fetchall()

    # If the table does not exist, create it with 'time' and 'file_id' as primary keys
    if not columns_info:
        columns = ", ".join([f"{channel} REAL" for channel in channels])
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {group_name} (time REAL, file_id TEXT, {columns}, PRIMARY KEY(time, file_id))")
    else:
        # If the table exists, check if 'file_id' exists, and add it if not
        existing_columns = [col[1] for col in columns_info]
        
        # Add 'file_id' column if it's missing
        if 'file_id' not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE {group_name} ADD COLUMN file_id TEXT")
                conn.commit()
                print(f"Added 'file_id' column to {group_name}.")
            except sqlite3.OperationalError as e:
                error_message = f"Error adding 'file_id' to {group_name}: {e}"
                print(error_message)
                error_log.append(error_message)

        # Check if there are new columns to add
        new_columns = [f"{channel} REAL" for channel in channels if channel not in existing_columns]
        for column in new_columns:
            try:
                cursor.execute(f"ALTER TABLE {group_name} ADD COLUMN {column}")
            except sqlite3.OperationalError as e:
                error_message = f"Error adding column {column} to {group_name}: {e}"
                print(error_message)
                error_log.append(error_message)

# Function to check if a file is already loaded based on 'file_id'
def is_file_already_loaded(file_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    # Check all tables for this file_id
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT 1 FROM {table_name} WHERE file_id = ?", (file_name,))
        if cursor.fetchone():
            return True
    return False

# Process all MF4 files found in the directory
for file_path in tqdm(file_paths, desc="Processing MF4 files", unit="file"):
    file_name = os.path.basename(file_path)  # Use filename as unique 'file_id'

    # Check if the file has already been processed
    if is_file_already_loaded(file_name):
        print(f"File '{file_name}' is already loaded in the database. Skipping...")
        continue

    print(f"\nProcessing file: {file_name}")

    # Open the MDF file and clean up the timestamps
    with MDF(file_path) as mdf:
        mdf.cleanup_timestamps(minimum=0, maximum=float('inf'))

        # Process each group with a progress bar
        for group_index, group in tqdm(enumerate(mdf.groups), desc=f"Processing groups in {file_name}", total=len(mdf.groups), unit="group", leave=False):
            group_name = f"Group_{group_index}"
            channels = [channel.name for channel in group.channels]

            # Create or update the table for the group
            create_or_update_table(group_name, channels)

            # Dictionary to group data by timestamp
            data_by_timestamp = {}

            # Process each channel within the group
            for channel in group.channels:
                try:
                    signal = mdf.get(channel.name, group=group_index)
                    time_data = signal.timestamps  # Timestamps
                    signal_data = signal.samples  # Signal values

                    # Add data to the dictionary grouped by timestamp
                    for time, value in zip(time_data, signal_data):
                        if time not in data_by_timestamp:
                            data_by_timestamp[time] = {}
                        data_by_timestamp[time][channel.name] = value

                except Exception as e:
                    error_message = f"Error retrieving signal '{channel.name}' in group '{group_name}': {e}"
                    print(error_message)
                    error_log.append(error_message)

            # Insert data into the database, grouped by timestamp
            for time, channel_data in data_by_timestamp.items():
                # Insert missing channels as None
                values = [time, file_name] + [channel_data.get(channel, None) for channel in channels]
                placeholders = ", ".join(["?"] * (len(channels) + 2))  # +2 for time and file_id
                columns = ", ".join(["time", "file_id"] + channels)

                # Use INSERT OR REPLACE to avoid duplicates for the same time and file_id
                cursor.execute(f"INSERT OR REPLACE INTO {group_name} ({columns}) VALUES ({placeholders})", values)

            # Commit after each group
            conn.commit()
            print(f"Data for group '{group_name}' from file '{file_name}' successfully inserted.")

            # Check the row count for the group
            cursor.execute(f"SELECT COUNT(*) FROM {group_name} WHERE file_id = ?", (file_name,))
            row_count = cursor.fetchone()[0]
            print(f"Group {group_name} from file {file_name} has {row_count} rows.")

# Commit changes and close the connection
conn.commit()
conn.close()

# Save the error log if any errors occurred
if error_log:
    with open("error_log.txt", "w") as log_file:
        for entry in error_log:
            log_file.write(f"{entry}\n")

print(f"MF4 data successfully exported to the database '{db_path}'.")
if error_log:
    print(f"Some errors occurred. Details can be found in 'error_log.txt'.")
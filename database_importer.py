import sqlite3
from asammdf import MDF
import os

# List of MF4 files to import
file_paths = ["TCP0014_Run19_02.MF4", "TCP0014_Run1_01.MF4", "TCP0014_Run17_01.MF4"]  # Add more files as needed

# Connect to the SQLite database
db_path = "mf4_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Error logging
error_log = []

# Function to create or update a table for a group with 'file_id' column
def create_or_update_table(group_name, channels):
    # Check if the table already exists
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

        # Check if there are new channels to add
        new_columns = [f"{channel} REAL" for channel in channels if channel not in existing_columns]
        for column in new_columns:
            try:
                cursor.execute(f"ALTER TABLE {group_name} ADD COLUMN {column}")
            except sqlite3.OperationalError as e:
                error_message = f"Error adding column {column} to {group_name}: {e}"
                print(error_message)
                error_log.append(error_message)

# Loop through all MF4 files
for file_path in file_paths:
    file_name = os.path.basename(file_path)  # Use filename as unique 'file_id'
    print(f"Processing file: {file_name}")

    # Open the MDF file and clean up the timestamps
    with MDF(file_path) as mdf:
        mdf.cleanup_timestamps(minimum=0, maximum=float('inf'))

        # Loop through all groups and channels
        for group_index, group in enumerate(mdf.groups):
            group_name = f"Group_{group_index}"
            channels = [channel.name for channel in group.channels]

            # Create or update the table for the group
            create_or_update_table(group_name, channels)

            # Debugging: Show how many channels are in the group
            print(f"Processing group {group_name} with {len(group.channels)} channels.")

            # Dictionary to group data by timestamp
            data_by_timestamp = {}

            # Get the data for each channel
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
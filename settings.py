import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
import json

def load_file_ids(lookup_table_path):
    # Load lookup table (Parquet or CSV)
    if lookup_table_path.endswith(".parquet"):
        lookup_table = pd.read_parquet(lookup_table_path)
    else:
        lookup_table = pd.read_csv(lookup_table_path)

    # Get unique file IDs
    file_ids = lookup_table['File.ID'].unique()
    return file_ids

def save_to_json(data, json_filename="config.json"):
    """Save dictionary to a JSON file."""
    with open(json_filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Configuration saved to {json_filename}")

def update_variables():
    # Get values from the Tkinter entries
    config_data = {
        "db_path": db_path_entry.get(),
        "lookup_table_path": lookup_table_entry.get(),
        "file_id": file_id_var.get(),
        "vmin": float(vmin_entry.get()),
        "vmax": float(vmax_entry.get())
    }

    # Save the configuration data to a JSON file
    save_to_json(config_data)

    # Print confirmation (optional)
    print("Updated variables saved to config.json:")
    print(config_data)

    # Close the Tkinter window
    root.quit()

def browse_file(entry_field):
    # Open a file dialog to choose a file
    filename = filedialog.askopenfilename(filetypes=[("Parquet/CSV Files", "*.parquet *.csv")])
    entry_field.delete(0, tk.END)
    entry_field.insert(0, filename)

# Initial setup for default values
db_path = "mf4_data.db"
lookup_table_path = "db_lookup_table.parquet"  # or 'db_lookup_table.csv'
file_id = "TCP0014_Run17_01.MF4"
vmin = 15
vmax = 40

# Tkinter setup
root = tk.Tk()
root.title("Heatmap Configuration")

# DB Path input
tk.Label(root, text="Database Path (db_path):").grid(row=0, column=0, sticky=tk.W)
db_path_entry = tk.Entry(root, width=40)
db_path_entry.grid(row=0, column=1)
db_path_entry.insert(0, db_path)

# Browse button for DB path
browse_db_button = tk.Button(root, text="Browse", command=lambda: browse_file(db_path_entry))
browse_db_button.grid(row=0, column=2)

# Lookup Table Path input
tk.Label(root, text="Lookup Table Path (lookup_table_path):").grid(row=1, column=0, sticky=tk.W)
lookup_table_entry = tk.Entry(root, width=40)
lookup_table_entry.grid(row=1, column=1)
lookup_table_entry.insert(0, lookup_table_path)

# Browse button for lookup table path
browse_lookup_button = tk.Button(root, text="Browse", command=lambda: browse_file(lookup_table_entry))
browse_lookup_button.grid(row=1, column=2)

# File ID dropdown
tk.Label(root, text="File ID:").grid(row=2, column=0, sticky=tk.W)
file_id_var = tk.StringVar(root)

# Load unique file IDs from the lookup table
try:
    file_ids = load_file_ids(lookup_table_path)
    file_id_var.set(file_ids[0])  # Set default value
    file_id_dropdown = ttk.Combobox(root, textvariable=file_id_var, values=file_ids)
    file_id_dropdown.grid(row=2, column=1)
except Exception as e:
    print(f"Error loading file IDs: {e}")
    file_id_dropdown = ttk.Combobox(root, textvariable=file_id_var, values=[])
    file_id_dropdown.grid(row=2, column=1)

# Min/Max heatmap values
tk.Label(root, text="Heatmap Min Value (vmin):").grid(row=3, column=0, sticky=tk.W)
vmin_entry = tk.Entry(root)
vmin_entry.grid(row=3, column=1)
vmin_entry.insert(0, str(vmin))

tk.Label(root, text="Heatmap Max Value (vmax):").grid(row=4, column=0, sticky=tk.W)
vmax_entry = tk.Entry(root)
vmax_entry.grid(row=4, column=1)
vmax_entry.insert(0, str(vmax))

# Update button
update_button = tk.Button(root, text="Save to JSON", command=update_variables)
update_button.grid(row=5, column=1, pady=10)

root.mainloop()

# After the Tkinter window is closed, the variables will be updated and saved to a JSON file.
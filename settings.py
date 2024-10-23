import tkinter as tk
from tkinter import messagebox
import json
import pandas as pd

# Load configuration from JSON file
def load_config(config_file="config.json"):
    with open(config_file, 'r') as f:
        return json.load(f)

# Save updated configuration to JSON file
def save_config(config, config_file="config.json"):
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)

# Get available file IDs from the lookup table CSV
def get_available_file_ids(lookup_table_path):
    lookup_table = pd.read_csv(lookup_table_path)
    return lookup_table['File.ID'].unique()  # Extract unique file IDs from the CSV

# Tkinter window to modify configuration
def modify_config_window(config, config_file="config.json"):
    root = tk.Tk()
    root.title("Edit Configuration")

    def save_changes():
        config['db_path'] = db_path_var.get()
        config['lookup_table_path'] = lookup_table_var.get()
        config['file_id'] = file_id_var.get()
        save_config(config, config_file)
        root.destroy()
        messagebox.showinfo("Success", "Configuration saved!")

    # DB Path
    tk.Label(root, text="DB Path").grid(row=0, column=0)
    db_path_var = tk.StringVar(value=config['db_path'])
    tk.Entry(root, textvariable=db_path_var).grid(row=0, column=1)

    # Lookup Table Path
    tk.Label(root, text="Lookup Table Path").grid(row=1, column=0)
    lookup_table_var = tk.StringVar(value=config['lookup_table_path'])
    tk.Entry(root, textvariable=lookup_table_var).grid(row=1, column=1)

    # File ID Dropdown
    tk.Label(root, text="Select File ID").grid(row=2, column=0)
    file_id_var = tk.StringVar(value=config['file_id'])  # Pre-select the current file ID
    available_file_ids = get_available_file_ids(config['lookup_table_path'])  # Get available file IDs from CSV
    file_id_dropdown = tk.OptionMenu(root, file_id_var, *available_file_ids)
    file_id_dropdown.grid(row=2, column=1)

    # Save Button
    tk.Button(root, text="Save", command=save_changes).grid(row=3, column=0, columnspan=2)

    root.mainloop()

# Run settings window if this file is executed
if __name__ == "__main__":
    config = load_config()
    modify_config_window(config)
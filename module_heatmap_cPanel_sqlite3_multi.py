import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import sqlite3
from matplotlib.widgets import Slider, Button

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

def plot_battery_layout(data, sensor_numbers, sensors_per_module, strings_count, t_index, total_frames, axes, cbar_list, custom_sensor_order, vmin=15, vmax=30, title="Battery Temperature Layout"):
    # Load the background image
    background_image_path = "/Users/gian/Documents/bat_temp_test/coolingplate_edited.png"
    background_img = plt.imread(background_image_path)
    
    image_height, image_width = background_img.shape[:2]
    white_area_width = 486
    white_area_height = 212
    x_start = (image_width - white_area_width + 40) / 2
    x_end = x_start + white_area_width
    y_start = (image_height - white_area_height) / 2
    y_end = y_start + white_area_height
    heatmap_extent = [x_start, x_end, y_start, y_end]
    
    data_at_timestamp = data[:, t_index]  # Get data for the current timestamp

    total_sensors_per_layer = 4 * sensors_per_module * 4  # Updated: 4 rows with 4 columns each
    reordered_layers = []
    reordered_sensor_numbers_layers = []

    for layer in range(strings_count):
        # Initialize an empty grid with NaNs
        reordered_data_layer = np.full((4, 4 * sensors_per_module), np.nan)
        reordered_sensor_numbers_layer = np.full((4, 4 * sensors_per_module), None, dtype=object)

        # Extract the appropriate slice for the current layer from `custom_sensor_order`
        start_index = layer * total_sensors_per_layer
        end_index = start_index + total_sensors_per_layer
        
        # Ensure we do not exceed the length of `custom_sensor_order`
        if end_index > len(custom_sensor_order):
            end_index = len(custom_sensor_order)

        layer_sensor_indices = custom_sensor_order[start_index:end_index]
        
        if len(layer_sensor_indices) != total_sensors_per_layer:
            print(f"Warning: Expected {total_sensors_per_layer} sensors for layer {layer + 1}, but got {len(layer_sensor_indices)}")

        for i in range(4):
            for j in range(4 * sensors_per_module):
                local_index = i * (4 * sensors_per_module) + j
                if local_index < len(layer_sensor_indices):
                    sensor_order = layer_sensor_indices[local_index]
                    
                    # Check if this sensor exists in our data and fill it in the grid
                    if sensor_order in sensor_numbers:
                        sensor_index = sensor_numbers.index(sensor_order)
                        reordered_data_layer[i, j] = data_at_timestamp[sensor_index]
                        reordered_sensor_numbers_layer[i, j] = sensor_order
                    else:
                        # Mark the sensor number as missing
                        reordered_sensor_numbers_layer[i, j] = None
                else:
                    reordered_sensor_numbers_layer[i, j] = None

        reordered_layers.append(reordered_data_layer)
        reordered_sensor_numbers_layers.append(reordered_sensor_numbers_layer)

    # Plot each layer of the battery
    for string_index in range(strings_count):
        ax = axes[string_index]
        ax.clear()
        ax.imshow(background_img, extent=[0, image_width, 0, image_height], aspect='auto', zorder=1)

        heatmap = ax.imshow(reordered_layers[string_index], cmap='coolwarm', interpolation='nearest', vmin=vmin, vmax=vmax, extent=heatmap_extent, alpha=1.0, zorder=2)

        # Annotate sensor data
        cell_width = (x_end - x_start) / (4 * sensors_per_module)
        cell_height = (y_end - y_start) / 4

        for i in range(4):
            for j in range(4 * sensors_per_module):
                annotation_x = x_start + (j + 0.5) * cell_width
                annotation_y = y_start + (4 - i - 0.5) * cell_height
                temp = reordered_layers[string_index][i, j]
                sensor_number = reordered_sensor_numbers_layers[string_index][i, j]
                
                if sensor_number is not None and not np.isnan(temp):
                    ax.text(annotation_x, annotation_y, f'Sensor {sensor_number}\n{temp:.1f}°C',
                            ha='center', va='center', color='black', fontsize=8, zorder=3)

        if cbar_list[string_index] is None:
            cbar_list[string_index] = ax.figure.colorbar(heatmap, ax=ax)

        ax.set_xlim(0, image_width)
        ax.set_ylim(image_height, 0)
        ax.set_title(f'{title} (Layer {string_index + 1}, Time Index: {t_index + 1} / {total_frames})')

    plt.tight_layout(pad=3.0)

def interactive_battery_layout(data, sensor_numbers, sensors_per_module, strings_count, custom_sensor_order, inlet_temp, outlet_temp, flow):
    total_frames = data.shape[1]
    fig, axes = plt.subplots(strings_count, 1, figsize=(10, 5 * strings_count))
    cbar_list = [None] * strings_count

    ax_slider = plt.axes([0.25, 0.02, 0.50, 0.04], facecolor='lightgoldenrodyellow')
    slider = Slider(ax_slider, 'Time', 0, total_frames - 1, valinit=0, valstep=1)

    ax_button_play = plt.axes([0.8, 0.02, 0.1, 0.04])
    button_play = Button(ax_button_play, 'Play/Pause')

    ax_button_ff = plt.axes([0.1, 0.02, 0.1, 0.04])
    button_ff = Button(ax_button_ff, 'Fast Forward')

    ax_button_rw = plt.axes([0.01, 0.02, 0.1, 0.04])
    button_rw = Button(ax_button_rw, 'Rewind')

    playing = [False]

    def update(val):
        t_index = int(slider.val)
        plot_battery_layout(data, sensor_numbers, sensors_per_module, strings_count, t_index, total_frames, axes, cbar_list, custom_sensor_order)
        
        if len(inlet_temp) > t_index and inlet_temp[t_index] is not None:
            inlet_display = f"{inlet_temp[t_index]:.2f} °C"
        else:
            inlet_display = 'N/A'
        
        if len(outlet_temp) > t_index and outlet_temp[t_index] is not None:
            outlet_display = f"{outlet_temp[t_index]:.2f} °C"
        else:
            outlet_display = 'N/A'
        
        if len(flow) > t_index and flow[t_index] is not None:
            flow_display = f"{flow[t_index]:.2f} L/min"
        else:
            flow_display = 'N/A'
        
        fig.suptitle(f"Inlet Temp: {inlet_display} | Outlet Temp: {outlet_display} | Coolant Flow: {flow_display}", fontsize=14, fontweight='bold')
        fig.canvas.draw_idle()

    slider.on_changed(update)

    def toggle_play(event):
        playing[0] = not playing[0]

    def fast_forward(event):
        if slider.val < total_frames - 5:
            slider.set_val(slider.val + 5)
        else:
            slider.set_val(total_frames - 1)

    def rewind(event):
        if slider.val > 5:
            slider.set_val(slider.val - 5)
        else:
            slider.set_val(0)

    button_play.on_clicked(toggle_play)
    button_ff.on_clicked(fast_forward)
    button_rw.on_clicked(rewind)

    def animate(i):
        if playing[0]:
            slider.set_val((slider.val + 1) % total_frames)

    ani = FuncAnimation(fig, animate, interval=200)

    update(0)
    plt.show()

def main(db_path, lookup_table_path, file_id):
    lookup_table = pd.read_csv(lookup_table_path)

    sensors_per_module = 2
    strings_count = 3

    temperatures, sensor_numbers = extract_temperatures_and_sensor_numbers(db_path, lookup_table, file_id)

    inlet_temp, outlet_temp, flow = extract_inlet_outlet_flow(db_path, file_id, lookup_table)

    # Custom sensor order (example, update with real physical layout)
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

    if len(temperatures) > 0:
        interactive_battery_layout(temperatures, sensor_numbers, sensors_per_module, strings_count, custom_sensor_order, inlet_temp, outlet_temp, flow)
    else:
        print("No temperature data found.")

if __name__ == "__main__":
    db_path = "mf4_data.db"
    lookup_table_path = "db_lookup_table.csv"
    file_id = "TCP0014_Run1_01.MF4"
    main(db_path, lookup_table_path, file_id)
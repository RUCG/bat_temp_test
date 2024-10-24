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

        for table_name in relevant_tables:
            # Query all signals for the relevant table and file_id at once
            signals_in_table = signal_info[signal_info['Table.Name'] == table_name]
            signal_names = signals_in_table['Channel.Name'].tolist()
            query = f"SELECT {', '.join(signal_names)} FROM {table_name} WHERE file_id = ?"
            
            try:
                cursor.execute(query, (file_id_value,))
                data = cursor.fetchall()

                for signal_idx, signal_name in enumerate(signal_names):
                    sensor_number = signals_in_table.iloc[signal_idx]['SensorNumber']
                    if sensor_number in processed_sensors or sensor_number in [102, 103]:
                        continue
                    
                    temperatures = [row[signal_idx] for row in data if row[signal_idx] is not None]
                    
                    if temperatures:
                        all_temperatures.append(temperatures)
                        sensor_numbers.append(sensor_number)
                        processed_sensors.add(sensor_number)

                        if min_length is None or len(temperatures) < min_length:
                            min_length = len(temperatures)

            except Exception as e:
                print(f"Error processing signals in table {table_name}: {e}")
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
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get signal info for the file ID
        signal_info = lookup_table[lookup_table['File.ID'] == file_id_value]

        # Inlet temperature (SensorNumber 101)
        inlet_signals = signal_info[signal_info['SensorNumber'] == 101]
        for index, inlet_info in inlet_signals.iterrows():
            inlet_table = inlet_info['Table.Name']
            inlet_column = inlet_info['Channel.Name']

            query = f"SELECT {inlet_column} FROM {inlet_table} WHERE file_id = ?"
            cursor.execute(query, (file_id_value,))
            data = cursor.fetchall()
            inlet_temp = [row[0] for row in data if row[0] is not None]
            if inlet_temp:
                inlet_temperature = inlet_temp
                print(f"Found inlet temperature data in table {inlet_table}")
                break  # Stop after finding data

        # Outlet temperature (SensorNumber 102)
        outlet_signals = signal_info[signal_info['SensorNumber'] == 102]
        for index, outlet_info in outlet_signals.iterrows():
            outlet_table = outlet_info['Table.Name']
            outlet_column = outlet_info['Channel.Name']

            query = f"SELECT {outlet_column} FROM {outlet_table} WHERE file_id = ?"
            cursor.execute(query, (file_id_value,))
            data = cursor.fetchall()
            outlet_temp = [row[0] for row in data if row[0] is not None]
            if outlet_temp:
                outlet_temperature = outlet_temp
                print(f"Found outlet temperature data in table {outlet_table}")
                break  # Stop after finding data

        # Coolant flow (SensorNumber 103)
        flow_signals = signal_info[signal_info['SensorNumber'] == 103]
        for index, flow_info in flow_signals.iterrows():
            flow_table = flow_info['Table.Name']
            flow_column = flow_info['Channel.Name']

            query = f"SELECT {flow_column} FROM {flow_table} WHERE file_id = ?"
            cursor.execute(query, (file_id_value,))
            data = cursor.fetchall()
            flow_data = [row[0] for row in data if row[0] is not None]
            if flow_data:
                coolant_flow = flow_data
                print(f"Found coolant flow data in table {flow_table}")
                break  # Stop after finding data

        # Debugging: Print the retrieved values
        if inlet_temperature:
            print(f"Inlet Temperature: {inlet_temperature[:5]}...")  # Print first 5 for brevity
        else:
            print("No inlet temperature data found.")
        
        if outlet_temperature:
            print(f"Outlet Temperature: {outlet_temperature[:5]}...")
        else:
            print("No outlet temperature data found.")
        
        if coolant_flow:
            print(f"Coolant Flow: {coolant_flow[:5]}...")
        else:
            print("No coolant flow data found.")

    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    return inlet_temperature, outlet_temperature, coolant_flow

def calculation_heat_flux(volumenstrom, temp_inlet, temp_outlet):
    """
    Calculates the heat flux Q_HVB through the coolant.

    Parameters:
    - volumenstrom: Coolant volumetric flow rate in m^3/s
    - temp_inlet: Battery inlet temperature in °C
    - temp_outlet: Battery outlet temperature in °C

    Returns:
    - The calculated heat flux Q_HVB in Watts (W)
    """
    # Hardcoded parameters
    cw = 4186    # Specific heat capacity of water in J/(kg*K)
    cg = 3350    # Specific heat capacity of glycol in J/(kg*K)
    pw = 0.5     # Proportion of water
    pg = 0.5     # Proportion of glycol
    rho_w = 1000 # Density of water in kg/m^3
    rho_g = 1070 # Density of glycol in kg/m^3

    # Temperature difference between inlet and outlet
    delta_t = temp_outlet - temp_inlet

    # Handle cases where volumenstrom is zero or delta_t is zero
    if volumenstrom == 0 or delta_t == 0:
        heat_flux = 0
    else:
        # Calculate the heat flux
        heat_flux = volumenstrom * delta_t * (pw * cw * rho_w + pg * cg * rho_g)

    return heat_flux

def plot_battery_layout(data, sensor_numbers, sensors_per_module, strings_count, t_index, total_frames, axes, cbar_list, custom_sensor_order, vmin=15, vmax=40, title="Battery Temperature Layout", fig=None):
    # Load the background image
    background_image_path = "/Users/gian/Documents/GitHub/bat_temp_test/coolingplate_edited.png"
    
    try:
        background_img = plt.imread(background_image_path)
        print(f"Background image loaded successfully from: {background_image_path}")
    except FileNotFoundError:
        print(f"Error: Background image not found at {background_image_path}")
        return

    # Get the image size for debugging
    image_height, image_width = background_img.shape[:2]
    print(f"Background image dimensions: width={image_width}, height={image_height}")
    
    # Set the heatmap and background extent based on the image size
    white_area_width = 486
    white_area_height = 212
    x_start = (image_width - white_area_width + 40) / 2
    x_end = x_start + white_area_width
    y_start = (image_height - white_area_height) / 2
    y_end = y_start + white_area_height
    heatmap_extent = [x_start, x_end, y_start, y_end]

    print(f"Heatmap extent: x_start={x_start}, x_end={x_end}, y_start={y_start}, y_end={y_end}")
    
    # Get the current data at the specific timestamp
    data_at_timestamp = data[:, t_index]
    
    total_sensors_per_layer = 4 * sensors_per_module * 4  # 4 rows with 4 columns each
    reordered_layers = []
    reordered_sensor_numbers_layers = []

    for layer in range(strings_count):
        # Initialize an empty grid with NaNs
        reordered_data_layer = np.full((4, 4 * sensors_per_module), np.nan)
        reordered_sensor_numbers_layer = np.full((4, 4 * sensors_per_module), None, dtype=object)

        # Extract the appropriate slice for the current layer from `custom_sensor_order`
        start_index = layer * total_sensors_per_layer
        end_index = start_index + total_sensors_per_layer
        
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
                    
                    if sensor_order in sensor_numbers:
                        sensor_index = sensor_numbers.index(sensor_order)
                        reordered_data_layer[i, j] = data_at_timestamp[sensor_index]
                        reordered_sensor_numbers_layer[i, j] = sensor_order
                    else:
                        reordered_sensor_numbers_layer[i, j] = None

        reordered_layers.append(reordered_data_layer)
        reordered_sensor_numbers_layers.append(reordered_sensor_numbers_layer)

    # Plot each layer of the battery and add a title for each
    for string_index in range(strings_count):
        ax = axes[string_index]
        ax.clear()

        # Display the background image, fitting it to the subplot
        ax.imshow(background_img, extent=[0, image_width, 0, image_height], aspect='auto', origin='lower', zorder=0)

        # Plot heatmap with some transparency so the background is visible
        heatmap = ax.imshow(reordered_layers[string_index], cmap='coolwarm', interpolation='nearest', vmin=vmin, vmax=vmax, extent=heatmap_extent, alpha=0.75, origin='lower', zorder=1)

        # Add a title to each subplot to indicate the layer number
        ax.set_title(f'Layer {string_index + 1}', fontsize=10, pad=10)

        # Adjust axes limits and aspect ratio
        ax.set_xlim(0, image_width)
        ax.set_ylim(0, image_height)
        ax.set_aspect('equal')

        # Annotate sensor data with smaller font size
        cell_width = (x_end - x_start) / (4 * sensors_per_module)
        cell_height = (y_end - y_start) / 4

        for i in range(4):
            for j in range(4 * sensors_per_module):
                annotation_x = x_start + (j + 0.5) * cell_width
                annotation_y = y_start + (i + 0.5) * cell_height  # Adjusted for 'lower' origin
                temp = reordered_layers[string_index][i, j]
                sensor_number = reordered_sensor_numbers_layers[string_index][i, j]
                
                if sensor_number is not None and not np.isnan(temp):
                    ax.text(annotation_x, annotation_y, f'Sensor {sensor_number}\n{temp:.1f}°C',
                            ha='center', va='center', color='black', fontsize=6, zorder=2)  # Text overlaid on the heatmap

    return heatmap  # Return heatmap for colorbar creation

def interactive_battery_layout(data, sensor_numbers, sensors_per_module, strings_count, custom_sensor_order, inlet_temp, outlet_temp, flow):
    total_frames = data.shape[1]
    
    # Set up a 3 by 2 layout: 2 rows and 3 columns
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))  # 2 rows and 3 columns
    
    # Flatten the axes for easier iteration (since axes is a 2D array now)
    axes = axes.flatten()
    
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
        heatmap = plot_battery_layout(data, sensor_numbers, sensors_per_module, strings_count, t_index, total_frames, axes, cbar_list, custom_sensor_order, fig=fig)
        
        # If it's the first time through, create a single colorbar for the whole figure
        if cbar_list[0] is None:
            cbar_ax = fig.add_axes([0.92, 0.3, 0.02, 0.4])  # Position for colorbar
            fig.colorbar(heatmap, cax=cbar_ax)
            cbar_list[0] = True  # Avoid re-creating the colorbar
            

        # Update inlet, outlet, and flow display
        if len(inlet_temp) > t_index and inlet_temp[t_index] is not None:
            inlet_display = f"{inlet_temp[t_index]:.2f} °C"
        else:
            inlet_display = 'N/A'
            
        if len(outlet_temp) > t_index and outlet_temp[t_index] is not None:
            outlet_display = f"{outlet_temp[t_index]:.2f} °C"
        else:
            outlet_display = 'N/A'
            
        if len(flow) > t_index and flow[t_index] is not None:
            flow_value = flow[t_index]
            flow_m3_s = flow_value / 60000  # Convert from L/min to m^3/s
            flow_display = f"{flow_value:.2f} L/min"
        else:
            flow_display = 'N/A'
            flow_m3_s = 0
        
        # Calculate heat flow if all values are available
        if inlet_display != 'N/A' and outlet_display != 'N/A' and flow_display != 'N/A':
            heat_flux = calculation_heat_flux(flow_m3_s, inlet_temp[t_index], outlet_temp[t_index])
            heat_flow_display = f"Q_HVB: {heat_flux:.2f} W"
        else:
            heat_flow_display = "Q_HVB: N/A"
        
        # Update the figure title to include heat flow
        fig.suptitle(f"Inlet Temp: {inlet_display} | Outlet Temp: {outlet_display} | Coolant Flow: {flow_display} | {heat_flow_display}", fontsize=14, fontweight='bold')
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
    # Load the lookup table from Parquet or CSV
    if lookup_table_path.endswith('.parquet'):
        lookup_table = pd.read_parquet(lookup_table_path)
    else:
        lookup_table = pd.read_csv(lookup_table_path)

    sensors_per_module = 2
    strings_count = 6  # Updated to 6 layers

    temperatures, sensor_numbers = extract_temperatures_and_sensor_numbers(db_path, lookup_table, file_id)

    inlet_temp, outlet_temp, flow = extract_inlet_outlet_flow(db_path, file_id, lookup_table)

    # Custom sensor order (same as before)
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
        65, 66, 67, 68, 69, 70, 71, 72,
        # Layer 4 (empty)
        None, None, None, None, None, None, None, None,
        None, None, None, None, None, None, None, None,
        # Layer 5 (empty)
        None, None, None, None, None, None, None, None,
        None, None, None, None, None, None, None, None,
        # Layer 6 (empty)
        None, None, None, None, None, None, None, None,
        None, None, None, None, None, None, None, None
    ]

    if len(temperatures) > 0:
        interactive_battery_layout(temperatures, sensor_numbers, sensors_per_module, strings_count, custom_sensor_order, inlet_temp, outlet_temp, flow)
    else:
        print("No temperature data found.")

if __name__ == "__main__":
    db_path = "mf4_data.db"
    lookup_table_path = "db_lookup_table.parquet"  # or 'db_lookup_table.csv'
    file_id = "TCP0014_Run17_01.MF4"
    main(db_path, lookup_table_path, file_id)
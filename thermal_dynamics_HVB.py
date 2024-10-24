import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
from sqlalchemy import create_engine
import json
import pickle
import os
import time

# Function to load configuration from JSON
def load_config(json_filename="config.json"):
    """Load configuration from a JSON file."""
    try:
        with open(json_filename, 'r') as f:
            config_data = json.load(f)
        print(f"Configuration loaded from {json_filename}:")
        print(config_data)
        return config_data
    except FileNotFoundError:
        print(f"Error: Configuration file {json_filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not parse {json_filename}.")
        return None

def cache_data(func):
    """Decorator to cache data returned by a function."""
    def wrapper(*args, **kwargs):
        cache_filename = kwargs.get('cache_filename')
        force_refresh = kwargs.get('force_refresh', False)
        
        # Extract db_path from args or kwargs
        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
        args_dict = dict(zip(arg_names, args))
        db_path = kwargs.get('db_path') or args_dict.get('db_path')
        
        # Check if cache exists and is up-to-date
        if cache_filename and os.path.exists(cache_filename) and not force_refresh:
            cache_mtime = os.path.getmtime(cache_filename)
            db_mtime = os.path.getmtime(db_path) if db_path and os.path.exists(db_path) else 0
            if cache_mtime > db_mtime:
                print(f"Loading data from cache: {cache_filename}")
                with open(cache_filename, 'rb') as f:
                    return pickle.load(f)
        
        # Call the function and cache its result
        data = func(*args, **kwargs)
        if cache_filename:
            with open(cache_filename, 'wb') as f:
                pickle.dump(data, f)
            print(f"Data cached to {cache_filename}")
        return data
    return wrapper

@cache_data
def extract_temperatures_and_sensor_numbers(db_path, lookup_table, file_id_value, cache_filename=None, force_refresh=False):
    start_time = time.time()
    # Use SQLAlchemy engine for better performance
    engine = create_engine(f'sqlite:///{db_path}')
    
    # Filter lookup table entries matching the current `file_id`
    signal_info = lookup_table[lookup_table['File.ID'] == file_id_value]
    relevant_tables = signal_info['Table.Name'].unique()

    all_temperatures = []
    sensor_identifiers = []
    min_length = None
    processed_sensors = set()

    for table_name in relevant_tables:
        signals_in_table = signal_info[signal_info['Table.Name'] == table_name]
        signal_names = signals_in_table['Channel.Name'].tolist()
        sensor_numbers = signals_in_table['SensorNumber'].tolist()
        bms_ids = signals_in_table['BMS_ID'].tolist()

        # Build query to fetch all required signals
        columns = ', '.join(signal_names)
        query = f"SELECT {columns} FROM {table_name} WHERE file_id = ?"

        try:
            # Use pandas to read SQL query directly into a DataFrame
            df = pd.read_sql_query(query, engine, params=(file_id_value,))
            df.dropna(axis=0, how='all', inplace=True)  # Drop rows where all values are NaN

            # Process each signal
            for idx, signal_name in enumerate(signal_names):
                sensor_number = sensor_numbers[idx]
                bms_id = bms_ids[idx]
                sensor_identifier = (sensor_number, bms_id)
                if sensor_identifier in processed_sensors or sensor_number in [102, 103]:
                    continue

                temperatures = df[signal_name].dropna().values

                if len(temperatures) > 0:
                    all_temperatures.append(temperatures)
                    sensor_identifiers.append(sensor_identifier)
                    processed_sensors.add(sensor_identifier)

                    if min_length is None or len(temperatures) < min_length:
                        min_length = len(temperatures)
        except Exception as e:
            print(f"Error processing table {table_name}: {e}")

    if min_length is None:
        min_length = 0

    # Trim all temperature arrays to the minimum length
    all_temperatures_trimmed = [temps[:min_length] for temps in all_temperatures]
    temperatures_array = np.array(all_temperatures_trimmed)

    end_time = time.time()
    print(f"Temperature data extraction took {end_time - start_time:.2f} seconds")

    return temperatures_array, sensor_identifiers

@cache_data
def extract_inlet_outlet_flow(db_path, file_id_value, lookup_table, cache_filename=None, force_refresh=False):
    start_time = time.time()
    engine = create_engine(f'sqlite:///{db_path}')

    inlet_temperature = []
    outlet_temperature = []
    coolant_flow = []

    # Get signal info for the file ID
    signal_info = lookup_table[lookup_table['File.ID'] == file_id_value]

    # Signals to extract
    signals = {
        'inlet': {'SensorNumber': 101, 'data': None},
        'outlet': {'SensorNumber': 102, 'data': None},
        'flow': {'SensorNumber': 103, 'data': None},
    }

    for key in signals.keys():
        signal_entries = signal_info[signal_info['SensorNumber'] == signals[key]['SensorNumber']]
        for _, signal_entry in signal_entries.iterrows():
            table_name = signal_entry['Table.Name']
            column_name = signal_entry['Channel.Name']
            query = f"SELECT {column_name} FROM {table_name} WHERE file_id = ?"
            try:
                df = pd.read_sql_query(query, engine, params=(file_id_value,))
                df.dropna(inplace=True)
                if not df.empty:
                    signals[key]['data'] = df[column_name].values
                    print(f"Found {key} data in table {table_name}")
                    break  # Stop after finding data
            except Exception as e:
                print(f"Error processing {key} data from table {table_name}: {e}")

    inlet_temperature = signals['inlet']['data'] if signals['inlet']['data'] is not None else []
    outlet_temperature = signals['outlet']['data'] if signals['outlet']['data'] is not None else []
    coolant_flow = signals['flow']['data'] if signals['flow']['data'] is not None else []

    # Debugging: Print the retrieved values
    if len(inlet_temperature) > 0:
        print(f"Inlet Temperature: {inlet_temperature[:5]}...")  # Print first 5 for brevity
    else:
        print("No inlet temperature data found.")

    if len(outlet_temperature) > 0:
        print(f"Outlet Temperature: {outlet_temperature[:5]}...")
    else:
        print("No outlet temperature data found.")

    if len(coolant_flow) > 0:
        print(f"Coolant Flow: {coolant_flow[:5]}...")
    else:
        print("No coolant flow data found.")

    end_time = time.time()
    print(f"Inlet/Outlet/Flow data extraction took {end_time - start_time:.2f} seconds")

    return inlet_temperature, outlet_temperature, coolant_flow

def calculation_heat_flux(volumenstrom, temp_inlet, temp_outlet):
    # ... [same as before]
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

def plot_battery_layout(data, sensor_identifiers, sensors_per_module_list, strings_count, t_index, total_frames, axes, cbar_list, custom_sensor_order, vmin=15, vmax=40, title="Battery Temperature Layout", fig=None):
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
    
    reordered_layers = []
    reordered_sensor_numbers_layers = []
    mean_temperatures = []  # List to store mean temperatures for each layer

    for layer in range(strings_count):
        sensors_per_module = sensors_per_module_list[layer]
        total_sensors_per_layer = 4 * sensors_per_module * 4

        # Initialize an empty grid with NaNs
        reordered_data_layer = np.full((4, 4 * sensors_per_module), np.nan)
        reordered_sensor_numbers_layer = np.full((4, 4 * sensors_per_module), None, dtype=object)

        start_index = sum([4 * sensors_per_module_list[i] * 4 for i in range(layer)])
        end_index = start_index + total_sensors_per_layer

        layer_sensor_indices = custom_sensor_order[start_index:end_index]
        
        if len(layer_sensor_indices) != total_sensors_per_layer:
            print(f"Warning: Expected {total_sensors_per_layer} sensors for layer {layer + 1}, but got {len(layer_sensor_indices)}")

        for i in range(4):
            for j in range(4 * sensors_per_module):
                local_index = i * (4 * sensors_per_module) + j
                if local_index < len(layer_sensor_indices):
                    sensor_identifier = layer_sensor_indices[local_index]
                    
                    if sensor_identifier in sensor_identifiers:
                        sensor_index = sensor_identifiers.index(sensor_identifier)
                        reordered_data_layer[i, j] = data_at_timestamp[sensor_index]
                        reordered_sensor_numbers_layer[i, j] = sensor_identifier
                    else:
                        reordered_sensor_numbers_layer[i, j] = None

        reordered_layers.append(reordered_data_layer)
        reordered_sensor_numbers_layers.append(reordered_sensor_numbers_layer)

        # Calculate the mean temperature for the layer (ignoring NaN values)
        mean_temperature = np.nanmean(reordered_data_layer)
        mean_temperatures.append(mean_temperature)

    # Plot each layer of the battery and add a title for each
    for string_index in range(strings_count):
        ax = axes[string_index]
        ax.clear()

        # Display the background image, fitting it to the subplot
        ax.imshow(background_img, extent=[0, image_width, 0, image_height], aspect='auto', origin='lower', zorder=0)

        # Plot heatmap with some transparency so the background is visible
        heatmap = ax.imshow(reordered_layers[string_index], cmap='coolwarm', interpolation='nearest', vmin=vmin, vmax=vmax, extent=heatmap_extent, alpha=1, origin='lower', zorder=1)

        # Add a title to each subplot to indicate the layer number and its mean temperature
        mean_temp = mean_temperatures[string_index]
        ax.set_title(f'Layer {string_index + 1} | Mean Temp: {mean_temp:.2f}°C', fontsize=10, pad=10)

        # Adjust axes limits and aspect ratio
        ax.set_xlim(0, image_width)
        ax.set_ylim(0, image_height)
        ax.set_aspect('equal')

        # Annotate sensor data with smaller font size
        cell_width = (x_end - x_start) / (4 * sensors_per_module_list[string_index])
        cell_height = (y_end - y_start) / 4

        for i in range(4):
            for j in range(4 * sensors_per_module_list[string_index]):
                annotation_x = x_start + (j + 0.5) * cell_width
                annotation_y = y_start + (i + 0.5) * cell_height  # Adjusted for 'lower' origin
                temp = reordered_layers[string_index][i, j]
                sensor_number = reordered_sensor_numbers_layers[string_index][i, j]
                
                if sensor_number is not None and not np.isnan(temp):
                    sensor_num, bms_id = sensor_number
                    ax.text(annotation_x, annotation_y, f'Sensor {sensor_num}\n{temp:.1f}°C\nBMS {bms_id}',
                            ha='center', va='center', color='black', fontsize=6, zorder=2)  # Text overlaid on the heatmap

    return heatmap  # Return heatmap for colorbar creation

def interactive_battery_layout(data, sensor_identifiers, sensors_per_module_list, strings_count, custom_sensor_order, inlet_temp, outlet_temp, flow, vmin, vmax):
    total_frames = data.shape[1]
    
    # Set up a 3 by 2 layout: 2 rows and 3 columns
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))  # 2 rows and 3 columns
    
    # Adjust the layout to make space above the subplots for metrics
    plt.subplots_adjust(top=0.85, hspace=0.3, wspace=0.3)  # Adjust hspace and top to create space
    
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
        heatmap = plot_battery_layout(
            data,
            sensor_identifiers,
            sensors_per_module_list,
            strings_count,
            t_index,
            total_frames,
            axes,
            cbar_list,
            custom_sensor_order,
            vmin=vmin,  # Pass vmin
            vmax=vmax,  # Pass vmax
            fig=fig
        )

        # If it's the first time through, create a single colorbar for the whole figure
        if cbar_list[0] is None:
            cbar_ax = fig.add_axes([0.92, 0.3, 0.02, 0.4])  # Position for colorbar
            fig.colorbar(heatmap, cax=cbar_ax)
            cbar_list[0] = True  # Avoid re-creating the colorbar

        # Calculate the mean temperature for each battery module layer
        layer_means = []
        for layer in range(strings_count):
            layer_data = data[layer * sensors_per_module_list[layer] * 4 : (layer + 1) * sensors_per_module_list[layer] * 4, t_index]
            mean_temp = np.nanmean(layer_data)  # Mean temperature of the current layer
            layer_means.append(mean_temp)

        overall_mean_temp = np.nanmean(layer_means)  # Overall mean temperature across all layers
        max_mean_temp_deviation = np.nanmax([abs(mean_temp - overall_mean_temp) for mean_temp in layer_means])  # Maximum deviation

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

        # Update the figure title to include heat flow and max deviation from mean layer temperature
        fig.suptitle(f"Inlet Temp: {inlet_display} | Outlet Temp: {outlet_display} | Coolant Flow: {flow_display} | {heat_flow_display} | Max Deviation from Mean Layer Temp: {max_mean_temp_deviation:.2f}°C", fontsize=14, fontweight='bold')
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

def main(db_path, lookup_table_path, file_id, vmin, vmax):
    # Load the lookup table from Parquet or CSV
    if lookup_table_path.endswith('.parquet'):
        lookup_table = pd.read_parquet(lookup_table_path)
    else:
        lookup_table = pd.read_csv(lookup_table_path)

    sensors_per_module_list = [2, 2, 2, 2, 2, 2]  # Adjust if necessary
    strings_count = 6  # Total number of layers

    # Define cache filenames
    temp_cache_filename = f"temp_data_{file_id}.pkl"
    flow_cache_filename = f"flow_data_{file_id}.pkl"

    # Extract temperatures and sensor identifiers, using caching
    temperatures, sensor_identifiers = extract_temperatures_and_sensor_numbers(
        db_path,
        lookup_table,
        file_id,
        cache_filename=temp_cache_filename
    )

    # Extract inlet, outlet temperatures and coolant flow, using caching
    inlet_temp, outlet_temp, flow = extract_inlet_outlet_flow(
        db_path,
        file_id,
        lookup_table,
        cache_filename=flow_cache_filename
    )

    # Custom sensor order (update with actual sensor numbers and BMS_IDs)
    custom_sensor_order = [
        # Layer 1
        (32, '01'), (31, '01'), (30, '01'), (29, '01'), (28, '01'), (27, '01'), (26, '01'), (25, '01'),
        (17, '01'), (18, '01'), (19, '01'), (20, '01'), (21, '01'), (22, '01'), (23, '01'), (24, '01'),
        (16, '01'), (15, '01'), (14, '01'), (13, '01'), (12, '01'), (11, '01'), (10, '01'), (9, '01'),
        (1, '01'), (2, '01'), (3, '01'), (4, '01'), (5, '01'), (6, '01'), (7, '01'), (8, '01'),

        # Layer 2
        (48, '01'), (47, '01'), (46, '01'), (45, '01'), (44, '01'), (43, '01'), (42, '01'), (41, '01'),
        (33, '01'), (34, '01'), (35, '01'), (36, '01'), (37, '01'), (38, '01'), (39, '01'), (40, '01'),
        (64, '01'), (63, '01'), (62, '01'), (61, '01'), (60, '01'), (59, '01'), (58, '01'), (57, '01'),
        (49, '01'), (50, '01'), (51, '01'), (52, '01'), (53, '01'), (54, '01'), (55, '01'), (56, '01'),

        # Layer 3
        (96, '01'), (95, '01'), (94, '01'), (93, '01'), (92, '01'), (91, '01'), (90, '01'), (89, '01'),
        (81, '01'), (82, '01'), (83, '01'), (84, '01'), (85, '01'), (86, '01'), (87, '01'), (88, '01'),
        (80, '01'), (79, '01'), (78, '01'), (77, '01'), (76, '01'), (75, '01'), (74, '01'), (73, '01'),
        (65, '01'), (66, '01'), (67, '01'), (68, '01'), (69, '01'), (70, '01'), (71, '01'), (72, '01'),
        
        # Layer 4
        (32, '05'), (31, '05'), (30, '05'), (29, '05'), (28, '05'), (27, '05'), (26, '05'), (25, '05'),
        (17, '05'), (18, '05'), (19, '05'), (20, '05'), (21, '05'), (22, '05'), (23, '05'), (24, '05'),
        (16, '05'), (15, '05'), (14, '05'), (13, '05'), (12, '05'), (11, '05'), (10, '05'), (9, '05'),
        (1, '05'), (2, '05'), (3, '05'), (4, '05'), (5, '05'), (6, '05'), (7, '05'), (8, '05'),

        # Layer 5
        (48, '05'), (47, '05'), (46, '05'), (45, '05'), (44, '05'), (43, '05'), (42, '05'), (41, '05'),
        (33, '05'), (34, '05'), (35, '05'), (36, '05'), (37, '05'), (38, '05'), (39, '05'), (40, '05'),
        (64, '05'), (63, '05'), (62, '05'), (61, '05'), (60, '05'), (59, '05'), (58, '05'), (57, '05'),
        (49, '05'), (50, '05'), (51, '05'), (52, '05'), (53, '05'), (54, '05'), (55, '05'), (56, '05'),

        # Layer 6
        (96, '05'), (95, '05'), (94, '05'), (93, '05'), (92, '05'), (91, '05'), (90, '05'), (89, '05'),
        (81, '05'), (82, '05'), (83, '05'), (84, '05'), (85, '05'), (86, '05'), (87, '05'), (88, '05'),
        (80, '05'), (79, '05'), (78, '05'), (77, '05'), (76, '05'), (75, '05'), (74, '05'), (73, '05'),
        (65, '05'), (66, '05'), (67, '05'), (68, '05'), (69, '05'), (70, '05'), (71, '05'), (72, '05'),
    ]


    if len(temperatures) > 0:
        interactive_battery_layout(
            temperatures,
            sensor_identifiers,
            sensors_per_module_list,
            strings_count,
            custom_sensor_order,
            inlet_temp,
            outlet_temp,
            flow,
            vmin,  # Pass vmin
            vmax   # Pass vmax
        )
    else:
        print("No temperature data found.")

if __name__ == "__main__":
    # Load configuration from JSON
    config_data = load_config("config.json")
    
    if config_data:
        db_path = config_data.get("db_path", "mf4_data.db")
        lookup_table_path = config_data.get("lookup_table_path", "db_lookup_table.parquet")
        file_id = config_data.get("file_id", "TCP0014_Run17_01.MF4").strip("'\"")  # Strip any extra quotes
        vmin = config_data.get("vmin", 15.0)
        vmax = config_data.get("vmax", 40.0)

        # Pass the loaded values to the main function
        main(db_path, lookup_table_path, file_id, vmin, vmax)
    else:
        print("Error: Could not load configuration. Exiting.")
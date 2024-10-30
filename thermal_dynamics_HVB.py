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
                sensor_number = int(sensor_numbers[idx])  # Convert to integer
                bms_id = bms_ids[idx]
                sensor_identifier = (sensor_number, bms_id)
                
                # Exclude inlet (101), outlet (102), and flow (103) sensors
                if sensor_identifier in processed_sensors or sensor_number in [101, 102, 103]:
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
    
    mean_temperatures = []
    max_temperatures = []
    min_temperatures = []
    temperature_ranges = []
    std_devs = []

    reordered_layers = []
    reordered_sensor_numbers_layers = []

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

        # Calculate layer-specific metrics
        mean_temperature = np.nanmean(reordered_data_layer)
        max_temperature = np.nanmax(reordered_data_layer)
        min_temperature = np.nanmin(reordered_data_layer)
        temperature_range = max_temperature - min_temperature
        std_dev = np.nanstd(reordered_data_layer)

        # Store metrics
        mean_temperatures.append(mean_temperature)
        max_temperatures.append(max_temperature)
        min_temperatures.append(min_temperature)
        temperature_ranges.append(temperature_range)
        std_devs.append(std_dev)

    # Plot each layer of the battery and add a title for each
    for string_index in range(strings_count):
        ax = axes[string_index]
        ax.clear()

        # Display the background image, fitting it to the subplot
        ax.imshow(background_img, extent=[0, image_width, 0, image_height], aspect='auto', origin='lower', zorder=0)

        # Plot heatmap with some transparency so the background is visible
        heatmap = ax.imshow(reordered_layers[string_index], cmap='coolwarm', interpolation='nearest', vmin=vmin, vmax=vmax, extent=heatmap_extent, alpha=1, origin='lower', zorder=1)

        # Add a title to each subplot to indicate the layer number and its metrics
        mean_temp = mean_temperatures[string_index]
        max_temp = max_temperatures[string_index]
        min_temp = min_temperatures[string_index]
        temp_range = temperature_ranges[string_index]
        std_dev = std_devs[string_index]

        ax.set_title(f'Layer {string_index + 1}\nMean: {mean_temp:.2f}°C | Max: {max_temp:.2f}°C | Min: {min_temp:.2f}°C\nRange: {temp_range:.2f}°C | Std Dev: {std_dev:.2f}°C', fontsize=10, pad=10)

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

def interactive_battery_layout(
    data, sensor_identifiers, sensors_per_module_list, strings_count,
    custom_sensor_order, inlet_temp, outlet_temp, flow, vmin, vmax
):
    total_frames = data.shape[1]

    import matplotlib.gridspec as gridspec

    # Create a figure with a specified size
    fig = plt.figure(figsize=(15, 10))

    # Define a GridSpec with 3 rows and 3 columns
    # Adjust 'height_ratios' to control the height of each row
    gs = gridspec.GridSpec(3, 3, height_ratios=[1, 1, 0.5])  # Last row is shorter

    # Create a list to hold the axes for the battery layers
    axes = []
    for i in range(2):  # Two rows
        for j in range(3):  # Three columns
            ax = fig.add_subplot(gs[i, j])
            axes.append(ax)

    # The bottom row (gs[2, :]) spans all three columns and is reserved for the additional graph
    ax_additional = fig.add_subplot(gs[2, :])

    # Adjust layout to prevent overlapping
    plt.subplots_adjust(hspace=0.01, wspace=0.3, top=0.80)  # Decrease 'top' to 0.80

    cbar_list = [None] * strings_count

    # Initialize text object references
    suptitle_text_obj = None
    subtitle_text_middle_obj = None

    ax_slider = plt.axes([0.20, 0.02, 0.50, 0.04], facecolor='lightgoldenrodyellow')
    slider = Slider(ax_slider, 'Time', 0, total_frames - 1, valinit=0, valstep=1)

    ax_button_play = plt.axes([0.05, 0.02, 0.1, 0.04])
    button_play = Button(ax_button_play, 'Play/Pause')

    ax_button_rw = plt.axes([0.78, 0.02, 0.1, 0.04])
    button_rw = Button(ax_button_rw, 'Rewind')

    ax_button_ff = plt.axes([0.89, 0.02, 0.1, 0.04])
    button_ff = Button(ax_button_ff, 'Fast Forward')

    playing = [False]

    # Prepare time axis (adjust if you have actual time data)
    time = np.arange(total_frames)

    # Compute overall temperature ranges over time
    overall_max_temps = np.nanmax(data, axis=0)
    overall_min_temps = np.nanmin(data, axis=0)
    overall_temp_range_over_time = overall_max_temps - overall_min_temps

    # Compute layer temperature ranges over time
    layer_temp_ranges = np.zeros((strings_count, total_frames))
    for layer in range(strings_count):
        start_idx = sum([sensors_per_module_list[i] * 4 * 4 for i in range(layer)])
        end_idx = start_idx + sensors_per_module_list[layer] * 4 * 4
        layer_data = data[start_idx:end_idx, :]
        layer_max_temps = np.nanmax(layer_data, axis=0)
        layer_min_temps = np.nanmin(layer_data, axis=0)
        layer_temp_ranges[layer, :] = layer_max_temps - layer_min_temps

    # Initialize plots in 'ax_additional'
    line_overall, = ax_additional.plot([], [], label='Overall Cell Temp Range', color='black')
    lines_layers = []
    colors = plt.cm.viridis(np.linspace(0, 1, strings_count))

    for layer in range(strings_count):
        line_layer, = ax_additional.plot([], [], label=f'Layer {layer + 1} Temp Range', color=colors[layer])
        lines_layers.append(line_layer)

    ax_additional.set_xlabel('Time')
    ax_additional.set_ylabel('Temperature Range (°C)')
    ax_additional.set_title('Cell and Layer Temperature Ranges Over Time')
    ax_additional.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0)
    ax_additional.set_xlim(time[0], time[-1])
    ax_additional.set_ylim(0, np.nanmax(overall_temp_range_over_time) * 1.1)

    def update(val):
        nonlocal suptitle_text_obj, subtitle_text_middle_obj

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
            vmin=vmin,
            vmax=vmax,
            fig=fig
        )

        # Calculate overall metrics
        overall_mean_temp = np.nanmean(data[:, t_index])
        overall_max_temp = np.nanmax(data[:, t_index])
        overall_min_temp = np.nanmin(data[:, t_index])
        overall_temp_range = overall_max_temp - overall_min_temp
        overall_std_dev = np.nanstd(data[:, t_index])

        # Calculate the mean temperature for each layer
        layer_means = []
        for layer in range(strings_count):
            start_idx = sum([sensors_per_module_list[i] * 4 * 4 for i in range(layer)])
            end_idx = start_idx + sensors_per_module_list[layer] * 4 * 4
            layer_data = data[start_idx:end_idx, t_index]
            mean_temp = np.nanmean(layer_data)
            layer_means.append(mean_temp)

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

        # Rearranged and updated figure title with new metrics (left-aligned)
        suptitle_text = (
            f"Module Mean Temp: {overall_mean_temp:.2f}°C \n"
            f"Module Max Temp: {overall_max_temp:.2f}°C \nModule Min Temp: {overall_min_temp:.2f}°C \n"
            f"Cell Range: {overall_temp_range:.2f}°C \nStd Dev: {overall_std_dev:.2f}°C\n"
        )

        # Update or create the first text object
        if suptitle_text_obj is None:
            suptitle_text_obj = fig.text(0.03, 0.86, suptitle_text, fontsize=12, fontweight='bold', ha='left')
        else:
            suptitle_text_obj.set_text(suptitle_text)

        # Center the second block of text lower on the figure
        subtitle_text_middle = (
            f"Inlet Temp: {inlet_display} \nOutlet Temp: {outlet_display} \nCoolant Flow: {flow_display} \n{heat_flow_display}"
        )

        # Update or create the second text object
        if subtitle_text_middle_obj is None:
            subtitle_text_middle_obj = fig.text(0.5, 0.91, subtitle_text_middle, fontsize=12, fontweight='bold', ha='center')
        else:
            subtitle_text_middle_obj.set_text(subtitle_text_middle)

        # Update 'ax_additional' plots
        line_overall.set_data(time[:t_index + 1], overall_temp_range_over_time[:t_index + 1])
        for layer in range(strings_count):
            lines_layers[layer].set_data(time[:t_index + 1], layer_temp_ranges[layer, :t_index + 1])

        # Adjust axes limits if necessary
        ax_additional.set_xlim(time[0], time[-1])
        ax_additional.set_ylim(0, np.nanmax(overall_temp_range_over_time) * 1.1)

        fig.canvas.draw_idle()

        # If it's the first time through, create a single colorbar for the whole figure
        if cbar_list[0] is None:
            cbar_ax = fig.add_axes([0.92, 0.3, 0.02, 0.4])
            fig.colorbar(heatmap, cax=cbar_ax)
            cbar_list[0] = True

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
            if slider.val < total_frames - 1:
                slider.set_val(slider.val + 1)
            else:
                slider.set_val(0)  # Reset to start or stop the animation

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
        cache_filename=temp_cache_filename,
        force_refresh=False  # Force refresh to update cache
    )

    # Extract inlet, outlet temperatures and coolant flow, using caching
    inlet_temp, outlet_temp, flow = extract_inlet_outlet_flow(
        db_path,
        file_id,
        lookup_table,
        cache_filename=flow_cache_filename,
        force_refresh=False  # Force refresh to update cache
    )

    # Custom sensor order (update with actual sensor numbers and BMS_IDs)
    custom_sensor_order = [
        # Layer 1
        (1, '01'), (2, '01'), (3, '01'), (4, '01'), (5, '01'), (6, '01'), (7, '01'), (8, '01'),
        (16, '01'), (15, '01'), (14, '01'), (13, '01'), (12, '01'), (11, '01'), (10, '01'), (9, '01'),
        (17, '01'), (18, '01'), (19, '01'), (20, '01'), (21, '01'), (22, '01'), (23, '01'), (24, '01'),
        (32, '01'), (31, '01'), (30, '01'), (29, '01'), (28, '01'), (27, '01'), (26, '01'), (25, '01'),
        
        # Layer 2
        (49, '01'), (50, '01'), (51, '01'), (52, '01'), (53, '01'), (54, '01'), (55, '01'), (56, '01'),
        (64, '01'), (63, '01'), (62, '01'), (61, '01'), (60, '01'), (59, '01'), (58, '01'), (57, '01'),
        (33, '01'), (34, '01'), (35, '01'), (36, '01'), (37, '01'), (38, '01'), (39, '01'), (40, '01'),
        (48, '01'), (47, '01'), (46, '01'), (45, '01'), (44, '01'), (43, '01'), (42, '01'), (41, '01'),

        # Layer 3
        (65, '01'), (66, '01'), (67, '01'), (68, '01'), (69, '01'), (70, '01'), (71, '01'), (72, '01'),
        (80, '01'), (79, '01'), (78, '01'), (77, '01'), (76, '01'), (75, '01'), (74, '01'), (73, '01'),
        (81, '01'), (82, '01'), (83, '01'), (84, '01'), (85, '01'), (86, '01'), (87, '01'), (88, '01'),
        (96, '01'), (95, '01'), (94, '01'), (93, '01'), (92, '01'), (91, '01'), (90, '01'), (89, '01'),
        
        
        
        # Layer 4
        (1, '05'), (2, '05'), (3, '05'), (4, '05'), (5, '05'), (6, '05'), (7, '05'), (8, '05'),
        (16, '05'), (15, '05'), (14, '05'), (13, '05'), (12, '05'), (11, '05'), (10, '05'), (9, '05'),
        (17, '05'), (18, '05'), (19, '05'), (20, '05'), (21, '05'), (22, '05'), (23, '05'), (24, '05'),
        (32, '05'), (31, '05'), (30, '05'), (29, '05'), (28, '05'), (27, '05'), (26, '05'), (25, '05'),

        # Layer 5
        (49, '05'), (50, '05'), (51, '05'), (52, '05'), (53, '05'), (54, '05'), (55, '05'), (56, '05'),
        (64, '05'), (63, '05'), (62, '05'), (61, '05'), (60, '05'), (59, '05'), (58, '05'), (57, '05'),
        (33, '05'), (34, '05'), (35, '05'), (36, '05'), (37, '05'), (38, '05'), (39, '05'), (40, '05'),
        (48, '05'), (47, '05'), (46, '05'), (45, '05'), (44, '05'), (43, '05'), (42, '05'), (41, '05'),

        # Layer 6
        (65, '05'), (66, '05'), (67, '05'), (68, '05'), (69, '05'), (70, '05'), (71, '05'), (72, '05'),
        (80, '05'), (79, '05'), (78, '05'), (77, '05'), (76, '05'), (75, '05'), (74, '05'), (73, '05'),
        (81, '05'), (82, '05'), (83, '05'), (84, '05'), (85, '05'), (86, '05'), (87, '05'), (88, '05'),
        (96, '05'), (95, '05'), (94, '05'), (93, '05'), (92, '05'), (91, '05'), (90, '05'), (89, '05'),
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
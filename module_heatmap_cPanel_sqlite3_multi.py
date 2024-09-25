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
    processed_sensors = set()  # Set to track processed sensors

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        signal_info = lookup_table[lookup_table['File.ID'] == file_id_value]
        relevant_tables = set(signal_info['Table.Name'])

        for index, row in signal_info.iterrows():
            table_name = row['Table.Name']
            signal_name = row['Channel.Name']
            sensor_number = row['SensorNumber']

            if sensor_number in processed_sensors:
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


def plot_battery_layout(data, sensor_numbers, sensors_per_module, strings_count, t_index, total_frames, axes, cbar_list, custom_sensor_order, vmin=15, vmax=30, title="Battery Temperature Layout"):
    # Load the background image
    background_image_path = "/Users/gian/Documents/bat_temp_test/coolingplate_edited.png"
    background_img = plt.imread(background_image_path)
    
    image_height, image_width = background_img.shape[:2]
    
    # White area dimensions in the center where the heatmap should be displayed
    white_area_width = 486
    white_area_height = 212
    x_start = (image_width - white_area_width + 40) / 2
    x_end = x_start + white_area_width
    y_start = (image_height - white_area_height) / 2
    y_end = y_start + white_area_height
    
    # Convert pixel coordinates to 'extent' for imshow (left, right, bottom, top)
    heatmap_extent = [x_start, x_end, y_start, y_end]

    # Extract data for the current time index
    data_at_timestamp = data[:, t_index]

    # Reorder data for each layer using the `custom_sensor_order`
    total_sensors = len(sensor_numbers) // strings_count  # Total sensors per layer
    reordered_layers = []
    reordered_sensor_numbers_layers = []

    for layer in range(strings_count):
        start_idx = layer * total_sensors
        end_idx = start_idx + total_sensors

        layer_sensor_order = custom_sensor_order[start_idx:end_idx]
        
        # Reorder data and sensor numbers for this specific layer
        reordered_data_layer = np.zeros_like(data_at_timestamp[start_idx:end_idx])
        reordered_sensor_numbers_layer = [None] * len(sensor_numbers[start_idx:end_idx])
        
        for idx, sensor_order in enumerate(layer_sensor_order):
            reordered_data_layer[idx] = data_at_timestamp[sensor_order - 1]
            reordered_sensor_numbers_layer[idx] = sensor_numbers[sensor_order - 1]
        
        reordered_layers.append(reordered_data_layer)
        reordered_sensor_numbers_layers.append(reordered_sensor_numbers_layer)

    # Iterate over each string (battery string) for plotting
    for string_index in range(strings_count):
        ax = axes[string_index]
        ax.clear()

        # Display the background image
        ax.imshow(background_img, extent=[0, image_width, 0, image_height], aspect='auto', zorder=1)

        # Create the grid_data for the heatmap
        grid_data = np.zeros((4, 4 * sensors_per_module))  # Initialize grid data
        reordered_data_flat = reordered_layers[string_index].flatten()
        
        # Populate the grid_data with temperature values
        sensor_idx = 0
        for i in range(4):  # Rows
            for j in range(4):  # Columns
                grid_data[i, j * sensors_per_module:(j + 1) * sensors_per_module] = reordered_data_flat[sensor_idx:sensor_idx + sensors_per_module]
                sensor_idx += sensors_per_module

        # Display the heatmap in the center of the whitespace using the calculated extent
        heatmap = ax.imshow(grid_data, cmap='coolwarm', interpolation='nearest', vmin=vmin, vmax=vmax, extent=heatmap_extent, alpha=1.0, zorder=2)

        # Annotate with sensor information now, ensuring perfect overlap
        num_rows, num_cols = grid_data.shape
        cell_width = (x_end - x_start) / num_cols
        cell_height = (y_end - y_start) / num_rows

        # Annotate the sensor data for the current layer
        sensor_idx = 0
        for i in range(num_rows):
            for j in range(num_cols):
                annotation_x = x_start + (j + 0.5) * cell_width
                annotation_y = y_start + (num_rows - i - 0.5) * cell_height
                
                temp = grid_data[i, j]
                original_sensor_number = reordered_sensor_numbers_layers[string_index][sensor_idx]

                ax.text(annotation_x, annotation_y, f'Sensor {original_sensor_number}\n{temp:.1f}°C',
                        ha='center', va='center', color='black', fontsize=8, zorder=3)
                sensor_idx += 1

        if cbar_list[string_index] is None:
            cbar_list[string_index] = ax.figure.colorbar(heatmap, ax=ax)

        ax.set_xlim(0, image_width)
        ax.set_ylim(image_height, 0)  # Reverse y-axis to match image coordinate system
        ax.set_title(f'{title} (Layer {string_index + 1}, Time Index: {t_index + 1} / {total_frames})')

    plt.tight_layout(pad=3.0)

def interactive_battery_layout(data, sensor_numbers, sensors_per_module, strings_count, custom_sensor_order):
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

    # Rufe die update-Funktion auf, um die erste Heatmap sofort anzuzeigen
    update(0)  # Erste Heatmap direkt beim Start zeichnen

    plt.show()

def main(db_path, lookup_table_path, file_id):
    lookup_table = pd.read_csv(lookup_table_path)

    sensors_per_module = 2
    strings_count = 3

    temperatures, sensor_numbers = extract_temperatures_and_sensor_numbers(db_path, lookup_table, file_id)

    custom_sensor_order = [
        32, 31, 30, 29, 28, 27, 26, 25,
        17, 18, 19, 20, 21, 22, 23, 24,
        16, 15, 14, 13, 12, 11, 10, 9,
        1, 2, 3, 4, 5, 6, 7, 8,
        48, 47, 46, 45, 44, 43, 42, 41,
        33, 34, 35, 36, 37, 38, 39, 40,
        64, 63, 62, 61, 60, 59, 58, 57,
        49, 50, 51, 52, 53, 54, 55, 56,
        96, 95, 94, 93, 92, 91, 90, 89,
        81, 82, 83, 84, 85, 86, 87, 88,
        80, 79, 78, 77, 76, 75, 74, 73,
        65, 66, 67, 68, 69, 70, 71, 72
    ]

    if len(temperatures) > 0:
        interactive_battery_layout(temperatures, sensor_numbers, sensors_per_module, strings_count, custom_sensor_order)
    else:
        print("No temperature data found.")

if __name__ == "__main__":
    db_path = "mf4_data.db"
    lookup_table_path = "db_lookup_table.csv"
    file_id = "TCP0014_Run1_01.MF4"
    main(db_path, lookup_table_path, file_id)
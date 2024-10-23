import numpy as np
import matplotlib.pyplot as plt

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
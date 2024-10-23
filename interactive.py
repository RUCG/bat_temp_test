from matplotlib.widgets import Slider, Button
from matplotlib.animation import FuncAnimation
from calculations import calculation_heat_flux
from plotting import plot_battery_layout
import matplotlib.pyplot as plt


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
        
        # Check the current inlet, outlet temperature, and flow
        if len(inlet_temp) > t_index and inlet_temp[t_index] is not None:
            inlet_display = f"{inlet_temp[t_index]:.2f} °C"
        else:
            inlet_display = 'N/A'
            
        if len(outlet_temp) > t_index and outlet_temp[t_index] is not None:
            outlet_display = f"{outlet_temp[t_index]:.2f} °C"
        else:
            outlet_display = 'N/A'
            
        if len(flow) > t_index and flow[t_index] is not None:
            # Assuming flow is in L/min, convert to m^3/s
            flow_m3_s = flow[t_index] / 60000  # Conversion from L/min to m^3/s
            flow_display = f"{flow[t_index]:.2f} L/min"
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
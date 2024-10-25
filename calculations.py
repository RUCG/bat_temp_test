def calculation_heat_flux(volumenstrom, temp_inlet, temp_outlet):
    """
    Berechnet den Wärmestrom Q_HVB durch die Kühlflüssigkeit.

    Parameter:
    - volumenstrom (V'): Volumenstrom der Kühlflüssigkeit in m^3/s
    - temp_inlet (TI): Temperatur Batterie Inlet in °C
    - temp_outlet (TO): Temperatur Batterie Outlet in °C

    Rückgabe:
    - Der berechnete Wärmestrom Q_HVB in Watt (W)
    """
    # Harcoded parameters
    cw = 4186    # Spezifische Wärmekapazität Wasser in J/(kg*K)
    cg = 3350    # Spezifische Wärmekapazität Glycol in J/(kg*K) @ 25°C (antifrost mt-650)
    pw = 0.5     # Anteil Wasser (60%)
    pg = 0.5     # Anteil Glycol (40%)
    rho_w = 1000 # Spezifische Dichte Wasser in kg/m^3
    rho_g = 1070 # Spezifische Dichte Glycol in kg/m^3 @ 25°C (antifrost mt-650)

    # Temperaturdifferenz zwischen Einlass und Auslass
    delta_t = temp_outlet - temp_inlet
    
    # Berechnung des Wärmestroms
    heat_flux = volumenstrom * delta_t * (pw * cw * rho_w + pg * cg * rho_g)

    #print(f"Der berechnete Wärmestrom Q_HVB beträgt: {heat_flux:.2f} W") # Debugging
    
    return heat_flux

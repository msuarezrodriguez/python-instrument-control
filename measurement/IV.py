# measurement/IV.py

import time
import numpy as np
from measurement.live_plot import LivePlotVoltageSource, LivePlotCurrentSource


# =============================================================================
# VOLTAGE-SOURCE I–V SWEEP
# =============================================================================
def voltage_source_iv(
    smu,
    start: float,
    stop: float,
    num_points: int,
    channel: str = "a",
    current_limit: float = 1e-3,
    acquisition_time: float = 0.1,
):
    """
    Perform a voltage-source I–V sweep:
    ----------------------------------------------------------
    - Source a voltage on the given SMU channel.
    - Sweep from 'start' to 'stop' using 'num_points' steps.
    - At each point, measure the resulting current.
    - Display an updating live plot: I vs V.
    - Return arrays: (V_array, I_array)
    ----------------------------------------------------------

    Parameters
    ----------
    smu : Keithley2634B
        The SMU object controlling the source/measure unit.
    start, stop : float
        Sweep limits for voltage (in volts).
    num_points : int
        Number of points in the sweep.
    channel : {"a","b"}
        SMU channel to use.
    current_limit : float
        Compliance current (the SMU will not exceed this).
    acquisition_time : float
        Delay (in seconds) after setting each voltage before measuring.
    """

    print("\n[INFO] Starting VOLTAGE-source I–V sweep...")

    # ---------------------------------------------------------------------
    # LIVE PLOT SETUP
    # ---------------------------------------------------------------------
    # Create a live plot object showing I (y-axis) vs V (x-axis).
    # Updated after every measurement point.
    # ---------------------------------------------------------------------
    plotter = LivePlotVoltageSource()

    # ---------------------------------------------------------------------
    # SMU CONFIGURATION
    # ---------------------------------------------------------------------
    # Set channel as voltage-source with defined current compliance.
    # Then enable output before starting the sweep.
    # ---------------------------------------------------------------------
    smu.configure_voltage_source(channel=channel, current_limit=current_limit)
    smu.enable_output(channel, on=True)

    try:
        V_list = []
        I_list = []

        # -----------------------------------------------------------------
        # SWEEP LOOP
        # -----------------------------------------------------------------
        # np.linspace defines the sweep points.
        # Each point:
        #   1) Set voltage
        #   2) Wait acquisition_time seconds
        #   3) Measure current
        #   4) Update lists and live plot
        # -----------------------------------------------------------------
        for V in np.linspace(start, stop, num_points):
            smu.set_voltage(channel, V)
            time.sleep(acquisition_time)

            I = smu.measure_current(channel)
            V_list.append(V)
            I_list.append(I)

            plotter.update(V, I)

        print("[INFO] Voltage-source I–V sweep finished.")
        return np.array(V_list), np.array(I_list)

    finally:
        # -----------------------------------------------------------------
        # Disable SMU output for safety and close the live plot window.
        # This ensures stable instrument state even if an exception occurs.
        # -----------------------------------------------------------------
        smu.enable_output(channel, on=False)
        plotter.close()


# =============================================================================
# CURRENT-SOURCE I–V SWEEP
# =============================================================================
def current_source_iv(
    smu,
    start: float,
    stop: float,
    num_points: int,
    channel: str = "a",
    voltage_limit: float = 1.0,
    acquisition_time: float = 0.1,
):
    """
    Perform a current-source I–V sweep:
    ----------------------------------------------------------
    - Source a current on the given SMU channel.
    - Sweep from 'start' to 'stop' using 'num_points' steps.
    - At each point, measure the resulting voltage.
    - Display an updating live plot: V vs I.
    - Return arrays: (I_array, V_array)
    ----------------------------------------------------------

    Parameters
    ----------
    smu : Keithley2634B
        The SMU object controlling the source/measure unit.
    start, stop : float
        Sweep limits for current (in amps).
    num_points : int
        Number of points in the sweep.
    channel : {"a","b"}
        SMU channel to use.
    voltage_limit : float
        Compliance voltage (the SMU will not exceed this).
    acquisition_time : float
        Delay (in seconds) after setting each current before measuring.
    """

    print("\n[INFO] Starting CURRENT-source I–V sweep...")

    # ---------------------------------------------------------------------
    # LIVE PLOT SETUP
    # ---------------------------------------------------------------------
    # Create a live plot object showing V (y-axis) vs I (x-axis).
    # Updated after every measurement point.
    # ---------------------------------------------------------------------
    plotter = LivePlotCurrentSource()

    # ---------------------------------------------------------------------
    # SMU CONFIGURATION
    # ---------------------------------------------------------------------
    # Set channel as current-source with voltage compliance.
    # Then enable output before starting sweep.
    # ---------------------------------------------------------------------
    smu.configure_current_source(channel=channel, voltage_limit=voltage_limit)
    smu.enable_output(channel, on=True)

    try:
        I_list = []
        V_list = []

        # -----------------------------------------------------------------
        # SWEEP LOOP
        # -----------------------------------------------------------------
        # np.linspace defines the sweep points.
        # Each point:
        #   1) Set current
        #   2) Wait acquisition_time seconds
        #   3) Measure voltage
        #   4) Update lists and live plot
        # -----------------------------------------------------------------
        for I in np.linspace(start, stop, num_points):
            smu.set_current(channel, I)
            time.sleep(acquisition_time)

            V = smu.measure_voltage(channel)
            I_list.append(I)
            V_list.append(V)

            plotter.update(I, V)

        print("[INFO] Current-source I–V sweep finished.")
        return np.array(I_list), np.array(V_list)

    finally:
        # -----------------------------------------------------------------
        # Disable SMU output for safety and close the live plot window.
        # Ensures the instrument returns to a safe state.
        # -----------------------------------------------------------------
        smu.enable_output(channel, on=False)
        plotter.close()

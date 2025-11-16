# measurement/temp_sweep.py

from __future__ import annotations
import time
from typing import Literal, Dict, Any
import numpy as np

from measurement.live_plot import LivePlotVvsT, LivePlotIvsT

# Type alias for clarity
SourceMode = Literal["current", "voltage"]


# =============================================================================
# INTERNAL: CORE TEMPERATURE SWEEP FUNCTION
# =============================================================================
def _continuous_temp_sweep(
    *,
    smu,
    ls,
    mode: SourceMode,
    channel: str,
    source_value: float,
    t_start: float,
    t_stop: float,
    ramp_rate: float,
    sample_interval: float,
    temp_channel: str = "A",
    temp_loop: int = 1,
    voltage_limit: float = 1.0,
    current_limit: float = 1e-3,
    sample_name: str = "sample",
    go_to_t_start: bool = True,
) -> Dict[str, Any]:
    """
    Perform a continuous temperature sweep without stabilizing at each point.
    -------------------------------------------------------------------------
    Depending on the 'mode', the function performs:

      mode == "current" → source current  → measure V(T)
      mode == "voltage" → source voltage → measure I(T)

    This is the workhorse for:
        • V vs T at fixed I
        • I vs T at fixed V

    It:
      1) Optionally moves to T_start (coarse stabilization)
      2) Sets up a continuous ramp to T_stop at a given rate
      3) Repeatedly measures (V or I) + temperature every 'sample_interval'
      4) Live-plots the results
      5) Returns raw arrays and a metadata dictionary
    """

    direction = "up" if t_stop >= t_start else "down"

    print("\n================ Temperature sweep ================")
    print(f"Mode: {mode!r} on channel {channel!r}, fixed value = {source_value}")
    print(f"T: {t_start} K -> {t_stop} K @ {ramp_rate} K/min")
    print(f"Sampling every {sample_interval} s on LakeShore channel {temp_channel}")

    # -------------------------------------------------------------------------
    # SMU CONFIGURATION + LIVE PLOT
    # -------------------------------------------------------------------------
    # Configure the SMU depending on the chosen mode.
    # Create appropriate live plot (V vs T or I vs T).
    # -------------------------------------------------------------------------
    if mode == "current":
        smu.configure_current_source(channel=channel, voltage_limit=voltage_limit)
        smu.set_current(channel, source_value)
        plotter = LivePlotVvsT(sample_name=sample_name)

    elif mode == "voltage":
        smu.configure_voltage_source(channel=channel, current_limit=current_limit)
        smu.set_voltage(channel, source_value)
        plotter = LivePlotIvsT(sample_name=sample_name)

    else:
        raise ValueError("mode must be 'current' or 'voltage'")

    smu.enable_output(channel, on=True)

    # -------------------------------------------------------------------------
    # OPTIONAL: MOVE TO START TEMPERATURE
    # -------------------------------------------------------------------------
    # This brings the system close to T_start (not strict stabilization).
    # For large jumps in temperature, this ensures a nice clean sweep start.
    # -------------------------------------------------------------------------
    if go_to_t_start:
        print(f"[TEMP] Going to start temperature T_start = {t_start:.3f} K...")
        try:
            ls.go_to_temperature(
                setpoint=t_start,
                loop=temp_loop,
                channel=temp_channel,
                tolerance=0.5,        # loose tolerance: just reach near T_start
                timeout=1800.0,
                check_interval=10.0,
                verbose=True,
            )

            EXTRA_WAIT_AFTER_T_REACHED = 0     # [s]

            print(f"[TEMP] Reached T_start. Waiting extra {EXTRA_WAIT_AFTER_T_REACHED:.0f} s "
              "for additional stabilization...")
            time.sleep(EXTRA_WAIT_AFTER_T_REACHED)

        except TimeoutError as exc:
            print(f"[WARNING] Could not stabilize at T_start: {exc}")
            print("[WARNING] Continuing with ramp anyway.")

    # -------------------------------------------------------------------------
    # SET CONTINUOUS RAMP
    # -------------------------------------------------------------------------
    # This is the core of the measurement: continuous heating/cooling
    # from T_start to T_stop at ramp_rate K/min.
    # -------------------------------------------------------------------------
    ls.set_ramp(loop=temp_loop, rate_K_per_min=ramp_rate, enable=True)
    ls.set_setpoint(loop=temp_loop, value=t_stop)

    # -------------------------------------------------------------------------
    # DATA STORAGE BUFFERS
    # -------------------------------------------------------------------------
    t0 = time.time()
    times: list[float] = []
    temps: list[float] = []
    volts: list[float] = []
    currents: list[float] = []

    # -------------------------------------------------------------------------
    # MAIN LOOP: SAMPLE TEMPERATURE + MEASURE V or I
    # -------------------------------------------------------------------------
    try:
        while True:
            # 1) Read current temperature
            T = ls.get_temperature(temp_channel)

            # 2) Check sweep termination condition
            if direction == "up" and T >= t_stop:
                break
            if direction == "down" and T <= t_stop:
                break

            # 3) Measure appropriate SMU quantity
            if mode == "current":
                # Current is fixed → measure voltage
                V = smu.measure_voltage(channel)
                I = source_value
            else:
                # Voltage is fixed → measure current
                I = smu.measure_current(channel)
                V = source_value

            t_elapsed = time.time() - t0

            # Store data
            times.append(t_elapsed)
            temps.append(T)
            volts.append(V)
            currents.append(I)

            # Print a console update
            print(
                f"t = {t_elapsed:6.1f} s | "
                f"T = {T:7.3f} K | "
                f"V = {V: .6e} V | "
                f"I = {I: .6e} A"
            )

            # Update live plot
            if mode == "current":
                plotter.update(T, V)
            else:
                plotter.update(T, I)

            # Wait for next sample
            time.sleep(sample_interval)

    # -------------------------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------------------------
    finally:
        print("[INFO] Stopping temperature sweep, turning outputs off.")

        try:
            smu.enable_output(channel, on=False)
        except Exception as e:
            print(f"[WARN] Could not disable SMU output: {e}")

        try:
            ls.set_ramp(loop=temp_loop, rate_K_per_min=ramp_rate, enable=False)
        except Exception as e:
            print(f"[WARN] Could not disable LS ramp: {e}")

        try:
            plotter.close()
        except Exception:
            pass

    print("[INFO] Temperature sweep finished.")

    # -------------------------------------------------------------------------
    # RETURN DATA + METADATA
    # -------------------------------------------------------------------------
    return {
        "time_s": np.array(times),
        "T_K": np.array(temps),
        "V_V": np.array(volts),
        "I_A": np.array(currents),
        "meta": {
            "mode": mode,
            "channel": channel,
            "source_value": source_value,
            "t_start": t_start,
            "t_stop": t_stop,
            "ramp_rate": ramp_rate,
            "sample_interval": sample_interval,
            "temp_channel": temp_channel,
            "temp_loop": temp_loop,
            "sample_name": sample_name,
        },
    }


# =============================================================================
# PUBLIC WRAPPERS
# =============================================================================

def run_v_vs_t_current_source(
    smu,
    ls,
    *,
    channel: str,
    current: float,
    t_start: float,
    t_stop: float,
    ramp_rate: float,
    sample_interval: float,
    temp_channel: str = "A",
    temp_loop: int = 1,
    voltage_limit: float = 1.0,
    sample_name: str = "sample",
    go_to_t_start: bool = True,
) -> Dict[str, Any]:
    """
    V vs T sweep with fixed current:
    ----------------------------------------------------------
    • SMU sources current → voltage is measured as T ramps.
    • Internally calls _continuous_temp_sweep(mode="current").
    """
    return _continuous_temp_sweep(
        smu=smu,
        ls=ls,
        mode="current",
        channel=channel,
        source_value=current,
        t_start=t_start,
        t_stop=t_stop,
        ramp_rate=ramp_rate,
        sample_interval=sample_interval,
        temp_channel=temp_channel,
        temp_loop=temp_loop,
        voltage_limit=voltage_limit,
        current_limit=1e-3,   # not used here
        sample_name=sample_name,
        go_to_t_start=go_to_t_start,
    )


def run_i_vs_t_voltage_source(
    smu,
    ls,
    *,
    channel: str,
    voltage: float,
    t_start: float,
    t_stop: float,
    ramp_rate: float,
    sample_interval: float,
    temp_channel: str = "A",
    temp_loop: int = 1,
    current_limit: float = 1e-3,
    sample_name: str = "sample",
    go_to_t_start: bool = True,
) -> Dict[str, Any]:
    """
    I vs T sweep with fixed voltage:
    ----------------------------------------------------------
    • SMU sources voltage → current is measured as T ramps.
    • Internally calls _continuous_temp_sweep(mode="voltage").
    """
    return _continuous_temp_sweep(
        smu=smu,
        ls=ls,
        mode="voltage",
        channel=channel,
        source_value=voltage,
        t_start=t_start,
        t_stop=t_stop,
        ramp_rate=ramp_rate,
        sample_interval=sample_interval,
        temp_channel=temp_channel,
        temp_loop=temp_loop,
        voltage_limit=1.0,
        current_limit=current_limit,
        sample_name=sample_name,
        go_to_t_start=go_to_t_start,
    )


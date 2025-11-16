# main.py

from config.paths import make_data_dir
from instruments.keithley_2634b import Keithley2634B
from instruments.lakeshore_336 import LakeShore336
from measurement.IV import voltage_source_iv, current_source_iv
from measurement.temp_sweep import run_v_vs_t_current_source, run_i_vs_t_voltage_source
from measurement.io_utils import save_iv_data, save_temp_data
import time

# ------------------------
# USER SETTINGS
# ------------------------

USER = "Manuel"
DEVICE = "Pt"
SAMPLE_NAME = "001"

GPIB_ADDRESS = 19            # Keithley SMU GPIB
LAKESHORE_GPIB_ADDRESS = 22  # Lakeshore 336 GPIB

# -------------------------------------------------------------------------
# MEASUREMENT MODES (overview)
# -------------------------------------------------------------------------
# mode = "voltage"
#     → Voltage-source I–V:
#         - Sweep V from start → stop
#         - Measure I(V)
#         - Optional temperature stabilization at a setpoint
#
# mode = "current"
#     → Current-source I–V:
#         - Sweep I from start → stop
#         - Measure V(I)
#         - Optional temperature stabilization at a setpoint
#
# mode = "v_vs_t_current"
#     → V vs T at fixed current:
#         - Source fixed current
#         - Ramp temperature from t_start → t_stop (no stabilization per point)
#         - Measure V(T) continuously
#
# mode = "i_vs_t_voltage"
#     → I vs T at fixed voltage:
#         - Source fixed voltage
#         - Ramp temperature from t_start → t_stop (no stabilization per point)
#         - Measure I(T) continuously
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
# EXAMPLE MEASUREMENT CONFIGURATIONS
# -------------------------------------------------------------------------
# You can edit, duplicate, or remove entries in MEASUREMENTS as needed.
# The examples below show the relevant parameters for each mode.
# -------------------------------------------------------------------------

MEASUREMENTS = [
    # {
    #     # -------------------------------------------------------------
    #     # 1) Voltage-source I–V with temperature stabilization
    #     # -------------------------------------------------------------
    #     "mode": "voltage",
    #     "channel": "a",        # SMU channel: "a" or "b"
    #     "start": -0.1,         # [V] start of voltage sweep
    #     "stop": 0.1,           # [V] end of voltage sweep
    #     "num_points": 11,      # number of points in the sweep
    #     "acq_time": 0.1,       # [s] wait time after setting each V
    #     "limit": 1e-3,         # [A] current compliance

    #     # --- temperature control ---
    #     "temp_control": True,      # if False or missing → ignore all temp settings
    #     "temp_setpoint": 25,       # [K] target temperature
    #     "temp_channel": "A",       # LS336 sensor used to read T (A closest to sample)
    #     "temp_tolerance": 0.1,     # [K] |T - setpoint| <= tolerance
    #     "temp_max_wait": 60,       # [s] max time to wait for stabilization
    #     "temp_loop": 1,            # control loop number (1–4)
    # },
    # {
    #     # -------------------------------------------------------------
    #     # 2) Current-source V–I at room temperature (no stabilization)
    #     # -------------------------------------------------------------
    #     "mode": "current",
    #     "channel": "b",        # SMU channel: "a" or "b"
    #     "start": -1e-6,        # [A] start of current sweep
    #     "stop": 1e-6,          # [A] end of current sweep
    #     "num_points": 21,      # number of points in the sweep
    #     "acq_time": 1.0,       # [s] wait time after setting each I
    #     "limit": 1.0,          # [V] voltage compliance

    #     # --- temperature control ---
    #     "temp_control": False,  # no temperature stabilization for this measurement
    # },
    # {
    #     # -------------------------------------------------------------
    #     # 3) V vs T at fixed current (temperature ramp)
    #     # -------------------------------------------------------------
    #     "mode": "v_vs_t_current",
    #     "channel": "a",          # SMU channel: "a" or "b"
    #     "current": 1e-5,         # [A] fixed source current
    #     "t_start": 10.0,        # [K] starting temperature
    #     "t_stop": 300.0,         # [K] final temperature
    #     "ramp_rate": 5.0,        # [K/min] ramp rate on LS336 loop
    #     "dt": 10.0,               # [s] time between measurement points
    #     "temp_channel": "A",     # LS336 sensor used to read T (A closest to sample)
    #     "temp_loop": 1,          # LS336 control loop number (1–4)
    #     "voltage_limit": 1.0,    # [V] SMU compliance voltage
    #     "go_to_t_start": True,   # True → pre-ramp to t_start before continuous sweep
    # },
    # {
    #     # -------------------------------------------------------------
    #     # 4) I vs T at fixed voltage (temperature ramp)
    #     # -------------------------------------------------------------
    #     "mode": "i_vs_t_voltage",
    #     "channel": "a",          # SMU channel: "a" or "b"
    #     "voltage": 0.1,          # [V] fixed source voltage
    #     "t_start": 300.0,        # [K] starting temperature
    #     "t_stop": 350.0,         # [K] final temperature
    #     "ramp_rate": 1.0,        # [K/min] ramp rate on LS336 loop
    #     "dt": 5.0,               # [s] time between measurement points
    #     "temp_channel": "A",     # LS336 sensor used to read T (A closest to sample)
    #     "temp_loop": 1,          # LS336 control loop number (1–4)
    #     "current_limit": 1e-3,   # [A] SMU current compliance
    #     "go_to_t_start": True,   # True → pre-ramp to t_start before continuous sweep
    #},
    {
        "mode": "current",
        "channel": "a",        # SMU channel: "a" or "b"
        "start": 5e-8,        # [A] start of current sweep
        "stop": 1e-6,          # [A] end of current sweep
        "num_points": 19,      # number of points in the sweep
        "acq_time": 1.0,       # [s] wait time after setting each I
        "limit": 1.0,          # [V] voltage compliance

        # --- temperature control ---
        "temp_control": True,      # if False or missing → ignore all temp settings
        "temp_setpoint": 250,        # [K] target temperature
        "temp_channel": "A",       # LS336 sensor used to read T (A closest to sample)
        "temp_tolerance": 0.1,     # [K] |T - setpoint| <= tolerance
        "temp_max_wait": 15000,       # [s] max time to wait for stabilization
        "temp_loop": 1,            # control loop number (1–4)
    },
    {
        "mode": "current",
        "channel": "a",        # SMU channel: "a" or "b"
        "start": 5e-8,        # [A] start of current sweep
        "stop": 1e-6,          # [A] end of current sweep
        "num_points": 19,      # number of points in the sweep
        "acq_time": 1.0,       # [s] wait time after setting each I
        "limit": 1.0,          # [V] voltage compliance

        # --- temperature control ---
        "temp_control": True,      # if False or missing → ignore all temp settings
        "temp_setpoint": 200,        # [K] target temperature
        "temp_channel": "A",       # LS336 sensor used to read T (A closest to sample)
        "temp_tolerance": 0.1,     # [K] |T - setpoint| <= tolerance
        "temp_max_wait": 15000,       # [s] max time to wait for stabilization
        "temp_loop": 1,            # control loop number (1–4)
    },
    {
        "mode": "current",
        "channel": "a",        # SMU channel: "a" or "b"
        "start": 5e-8,        # [A] start of current sweep
        "stop": 1e-6,          # [A] end of current sweep
        "num_points": 19,      # number of points in the sweep
        "acq_time": 1.0,       # [s] wait time after setting each I
        "limit": 1.0,          # [V] voltage compliance

        # --- temperature control ---
        "temp_control": True,      # if False or missing → ignore all temp settings
        "temp_setpoint": 150,        # [K] target temperature
        "temp_channel": "A",       # LS336 sensor used to read T (A closest to sample)
        "temp_tolerance": 0.1,     # [K] |T - setpoint| <= tolerance
        "temp_max_wait": 15000,       # [s] max time to wait for stabilization
        "temp_loop": 1,            # control loop number (1–4)
    },
    {
        "mode": "current",
        "channel": "a",        # SMU channel: "a" or "b"
        "start": 5e-8,        # [A] start of current sweep
        "stop": 1e-6,          # [A] end of current sweep
        "num_points": 19,      # number of points in the sweep
        "acq_time": 1.0,       # [s] wait time after setting each I
        "limit": 1.0,          # [V] voltage compliance

        # --- temperature control ---
        "temp_control": True,      # if False or missing → ignore all temp settings
        "temp_setpoint": 100,        # [K] target temperature
        "temp_channel": "A",       # LS336 sensor used to read T (A closest to sample)
        "temp_tolerance": 0.1,     # [K] |T - setpoint| <= tolerance
        "temp_max_wait": 15000,       # [s] max time to wait for stabilization
        "temp_loop": 1,            # control loop number (1–4)
    },
    {
        "mode": "current",
        "channel": "a",        # SMU channel: "a" or "b"
        "start": 5e-8,        # [A] start of current sweep
        "stop": 1e-6,          # [A] end of current sweep
        "num_points": 19,      # number of points in the sweep
        "acq_time": 1.0,       # [s] wait time after setting each I
        "limit": 1.0,          # [V] voltage compliance

        # --- temperature control ---
        "temp_control": True,      # if False or missing → ignore all temp settings
        "temp_setpoint": 50,        # [K] target temperature
        "temp_channel": "A",       # LS336 sensor used to read T (A closest to sample)
        "temp_tolerance": 0.1,     # [K] |T - setpoint| <= tolerance
        "temp_max_wait": 15000,       # [s] max time to wait for stabilization
        "temp_loop": 1,            # control loop number (1–4)
    },
    {
        "mode": "current",
        "channel": "a",        # SMU channel: "a" or "b"
        "start": 5e-8,        # [A] start of current sweep
        "stop": 1e-6,          # [A] end of current sweep
        "num_points": 19,      # number of points in the sweep
        "acq_time": 1.0,       # [s] wait time after setting each I
        "limit": 1.0,          # [V] voltage compliance

        # --- temperature control ---
        "temp_control": True,      # if False or missing → ignore all temp settings
        "temp_setpoint": 10,        # [K] target temperature
        "temp_channel": "A",       # LS336 sensor used to read T (A closest to sample)
        "temp_tolerance": 0.1,     # [K] |T - setpoint| <= tolerance
        "temp_max_wait": 15000,       # [s] max time to wait for stabilization
        "temp_loop": 1,            # control loop number (1–4)
    },
]


def main():
    # -------------------------------------------------------------------------
    # INITIAL SETUP
    # -------------------------------------------------------------------------
    # Create data directories if needed and print the data path.
    # This ensures that all saved files (IV or T-sweeps) go into the proper
    # structure defined in config/paths.py.
    # -------------------------------------------------------------------------
    DATA_DIR = make_data_dir(USER, DEVICE)
    print("Data directory:", DATA_DIR)

    smu = None   # Keithley 2634B (SMU)
    ls = None    # LakeShore 336 (Temperature controller)

    try:
        # ---------------------------------------------------------------------
        # CONNECT TO INSTRUMENTS
        # ---------------------------------------------------------------------
        # 1. Connect to Keithley 2634B SMU
        #    - Always required for any measurement.
        # ---------------------------------------------------------------------
        print(f"\n[INFO] Connecting to Keithley at GPIB {GPIB_ADDRESS}...")
        smu = Keithley2634B.from_gpib(GPIB_ADDRESS)
        print("Keithley IDN:", smu.get_idn())

        # ---------------------------------------------------------------------
        # 2. Connect to LakeShore 336 (optional)
        #    - Required only if:
        #         • temperature stabilization for IV is needed
        #         • temperature sweeps (V vs T or I vs T) are used
        #    - If not found, ls=None and all temperature functionalities
        #      will be skipped automatically.
        # ---------------------------------------------------------------------
        print(f"\n[INFO] Connecting to LakeShore 336 at GPIB {LAKESHORE_GPIB_ADDRESS}...")
        try:
            ls = LakeShore336.from_gpib(LAKESHORE_GPIB_ADDRESS)
            print("LakeShore IDN:", ls.get_idn())
        except Exception as exc:
            print(f"[WARNING] Could not connect to LakeShore 336: {exc}")
            ls = None

        # ---------------------------------------------------------------------
        # CONFIGURE LAKESHORE (ONLY IF CONNECTED)
        # ---------------------------------------------------------------------
        # This configures:
        #   • Output 1 in closed-loop mode using sensor A
        #   • Heater range
        #   • A default ramp (1 K/min)
        #
        # These settings are used for:
        #   • Temperature stabilization before IV curves
        #   • Continuous ramps for V vs T and I vs T sweeps
        #
        # If the Lakeshore is not connected, all temperature functionality
        # will be automatically skipped.
        # ---------------------------------------------------------------------
        if ls is not None:
            print("\n[INFO] Configuring LakeShore loop 1 / output 1...")

            # Closed-loop PID control on output 1, using sensor A
            ls.set_output_mode(
                output=1,
                mode="closed loop",
                input_channel="A",
                powerup_enable=False,   # after power cycle: heater stays OFF
            )

            # Heater power range
            # Use "low" if unsure — "high" only if you know the cryostat/heater well.
            ls.set_heater_range(output=1, heater_range="high")

            # Define a default ramp rate but KEEP IT DISABLED by default.
            # Ramps will be explicitly enabled only inside the T-sweep functions.
            ls.set_ramp(loop=1, rate_K_per_min=1.0, enable=False)

            # Read back settings for verification
            mode_info = ls.get_output_mode(1)
            hrange = ls.get_heater_range(1, as_text=True)
            print("[INFO] LakeShore output 1 mode:", mode_info)
            print("[INFO] LakeShore output 1 heater range:", hrange)

        # ---------------------------------------------------------------------
        # BEGIN MEASUREMENT SEQUENCE
        # ---------------------------------------------------------------------
        # From here on, we iterate over the MEASUREMENTS list.
        # Each measurement entry (dict) defines:
        #   - mode: "voltage", "current", "v_vs_t_current", "i_vs_t_voltage"
        #   - IV parameters OR temperature-sweep parameters
        #   - optional temp stabilization for IV modes
        #
        # The logic for each mode is handled below this block.
        # ---------------------------------------------------------------------

        # ----------------- Measurement loop --------------------

        try:

            for idx, m in enumerate(MEASUREMENTS, start=1):
                print(f"\n================ Measurement #{idx} ================")

                mode = m["mode"]
                ch = m.get("channel", "a")

                # -------------------------------------------------------------
                # 1. TEMPERATURE STABILIZATION  (only for IV modes)
                # -------------------------------------------------------------
                #
                # This block is ONLY used for:
                #   - mode == "voltage"  (voltage-source I–V)
                #   - mode == "current"  (current-source I–V)
                #
                # It sets a temperature setpoint and waits until the LS336 stabilizes.
                #
                # IMPORTANT:
                # This block must NOT be used for temperature sweeps
                # (v_vs_t_current or i_vs_t_voltage),
                # because those sweeps require a continuous temperature ramp
                # WITHOUT stabilization at each point.
                # -------------------------------------------------------------

                if mode in ("voltage", "current") and m.get("temp_control", False):
                    if ls is None:
                        print("[WARNING] temp_control=True but LakeShore is not connected → skipping temperature stabilization.")
                    else:
                        setpoint = m["temp_setpoint"]
                        temp_ch = m.get("temp_channel", "A")
                        tol = m.get("temp_tolerance", 0.1)
                        max_wait = m.get("temp_max_wait", 900.0)
                        loop = m.get("temp_loop", 1)

                        try:
                            final_T = ls.go_to_temperature(
                                setpoint=setpoint,
                                loop=loop,
                                channel=temp_ch,
                                tolerance=tol,
                                timeout=max_wait,
                                check_interval=5.0,
                                verbose=True,
                            )

                            EXTRA_WAIT_AFTER_T_REACHED = 60     # [s]

                            print(f"[TEMP] Reached T_start. Waiting extra {EXTRA_WAIT_AFTER_T_REACHED:.0f} s "
                                "for additional stabilization...")
                            time.sleep(EXTRA_WAIT_AFTER_T_REACHED)

                        except TimeoutError as exc:
                            print(f"[WARNING] Temperature did not stabilize: {exc}")
                            # your decision: continue anyway or skip the measurement
                            # continue
                # -------------------------------------------------------------
                # End of temperature stabilization block
                # -------------------------------------------------------------

                # -------------------------------------------------------------
                # 2. CLASSIC I–V or V–I MEASUREMENTS
                # -------------------------------------------------------------
                if mode == "voltage":
                    V, I = voltage_source_iv(
                        smu,
                        start=m["start"],
                        stop=m["stop"],
                        num_points=m["num_points"],
                        acquisition_time=m["acq_time"],
                        current_limit=m["limit"],
                        channel=ch,
                    )
                    save_iv_data(DATA_DIR, SAMPLE_NAME, m, V, I, mode_label="I_vs_V")

                elif mode == "current":
                    I_arr, V_arr = current_source_iv(
                        smu,
                        start=m["start"],
                        stop=m["stop"],
                        num_points=m["num_points"],
                        acquisition_time=m["acq_time"],
                        voltage_limit=m["limit"],
                        channel=ch,
                    )
                    save_iv_data(DATA_DIR, SAMPLE_NAME, m, I_arr, V_arr, mode_label="V_vs_I")

                # -------------------------------------------------------------
                # 3. TEMPERATURE SWEEP MODES (V vs T and I vs T)
                # -------------------------------------------------------------
                # IMPORTANT:
                # In these modes we explicitly DO NOT stabilize temperature.
                # A continuous ramp is used instead.
                # -------------------------------------------------------------

                elif mode == "v_vs_t_current":
                    if ls is None:
                        print("[ERROR] LakeShore not connected → cannot run V vs T.")
                        continue

                    result = run_v_vs_t_current_source(
                        smu,
                        ls,
                        channel=ch,
                        current=m["current"],
                        t_start=m["t_start"],
                        t_stop=m["t_stop"],
                        ramp_rate=m["ramp_rate"],
                        sample_interval=m["dt"],
                        temp_channel=m.get("temp_channel", "A"),
                        temp_loop=m.get("temp_loop", 1),
                        voltage_limit=m.get("voltage_limit", 1.0),
                        sample_name=SAMPLE_NAME,
                        go_to_t_start=m.get("go_to_t_start", True),
                    )

                    save_temp_data(
                        DATA_DIR,
                        SAMPLE_NAME,
                        m,
                        result,
                        mode_label="V_vs_T",
                    )

                elif mode == "i_vs_t_voltage":
                    if ls is None:
                        print("[ERROR] LakeShore not connected → cannot run I vs T.")
                        continue

                    result = run_i_vs_t_voltage_source(
                        smu,
                        ls,
                        channel=ch,
                        voltage=m["voltage"],
                        t_start=m["t_start"],
                        t_stop=m["t_stop"],
                        ramp_rate=m["ramp_rate"],
                        sample_interval=m["dt"],
                        temp_channel=m.get("temp_channel", "A"),
                        temp_loop=m.get("temp_loop", 1),
                        current_limit=m.get("current_limit", 1e-3),
                        sample_name=SAMPLE_NAME,
                        go_to_t_start=m.get("go_to_t_start", True),
                    )

                    save_temp_data(
                        DATA_DIR,
                        SAMPLE_NAME,
                        m,
                        result,
                        mode_label="I_vs_T",
                    )

                # -------------------------------------------------------------
                # 4. Unknown mode
                # -------------------------------------------------------------
                else:
                    print(f"[WARNING] Unknown mode {mode!r}, skipping.")

        except KeyboardInterrupt:
            print("\n[WARNING] Measurement aborted by user (Ctrl+C).")

            

    finally:
        print("\n[INFO] Shutting down instruments...")

        if smu is not None:
            try:
                smu.all_outputs_off()
            except Exception:
                pass
            try:
                smu.clear_status()
            except Exception:
                pass
            smu.close()

        if ls is not None:
            try:
                ls.clear_status()
            except Exception:
                pass
            ls.close()


if __name__ == "__main__":
    main()


# measurement/io_utils.py

import os
import datetime
from typing import Sequence, Dict, Any


# =============================================================================
# SAVE IV DATA
# =============================================================================
def save_iv_data(
    base_dir: str,
    sample_name: str,
    measurement: dict,
    x: Sequence[float],
    y: Sequence[float],
    mode_label: str,
) -> str:
    """
    Save data from classic I–V or V–I sweeps.

    This is used for:
        - mode="voltage": V sweep, measure I(V)
        . mode="current": I sweep, measure V(I)

    The file contains:
        - complete measurement metadata
        - header with column labels
        - tab-separated numerical data

    Parameters
    ----------
    base_dir : str
        Root directory where data files will be written.
    sample_name : str
        Identifier for the sample. Appears in the filename.
    measurement : dict
        The entry in MEASUREMENTS defining this sweep.
    x, y : sequence of float
        Sweep vectors:
            voltage mode: x = voltage, y = current
            current mode: x = current, y = voltage

    Returns
    -------
    path : str
        Full absolute path to the saved file.
    """

    # Determine labeling
    mode = measurement["mode"]                  # "voltage" or "current"
    channel = measurement.get("channel", "a")
    temp = measurement.get("temp_setpoint", "RT")

    # Timestamp for file tracking
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Simple filename style: sample_T[K].txt
    filename = f"{sample_name}_{mode_label}_{temp}K.txt"
    path = os.path.join(base_dir, filename)

    # Column headers based on mode
    if mode == "voltage":
        col_header = "V[V]\tI[A]"
    else:
        col_header = "I[A]\tV[V]"

    # -------------------------------------------------------------------------
    # Write file
    # -------------------------------------------------------------------------
    with open(path, "w") as f:
        # Basic metadata
        f.write(f"# Sample: {sample_name}\n")
        f.write(f"# Mode: {mode_label}\n")
        f.write(f"# Timestamp: {timestamp}\n")

        # Dump measurement parameters for reproducibility
        for key, value in measurement.items():
            f.write(f"# {key} = {value}\n")

        f.write(f"{col_header}\n")

        # Numerical data
        for xi, yi in zip(x, y):
            f.write(f"{xi:.6e}\t{yi:.6e}\n")

    print(f"[INFO] Saved data to {path}")
    return path



# =============================================================================
# SAVE TEMPERATURE SWEEP DATA (V vs T or I vs T)
# =============================================================================
def save_temp_data(
    base_dir: str,
    sample_name: str,
    measurement: Dict[str, Any],
    data: Dict[str, Any],
    mode_label: str,
) -> str:
    """
    Save data from temperature sweeps (V vs T or I vs T).

    This function is used in:
        - V vs T with fixed I
        - I vs T with fixed V

    The file includes:
        - complete measurement metadata from MEASUREMENTS
        - metadata from the sweep engine in temp_sweep.py
        - raw time, temperature, voltage, and current data

    Parameters
    ----------
    base_dir : str
        Directory where the file will be stored.
    sample_name : str
        Sample identifier for filenames.
    measurement : dict
        The MEASUREMENTS entry that launched this sweep.
    data : dict
        Output dictionary from temp_sweep:
           { "time_s", "T_K", "V_V", "I_A", "meta": {...} }
    mode_label : str
        Short tag for filenames, e.g. "V_vs_T_Ifixed".

    Returns
    -------
    path : str
        Full path of the saved text file.
    """

    channel = measurement.get("channel", "a")
    t_start = measurement.get("t_start", data["meta"].get("t_start", 0.0))
    t_stop = measurement.get("t_stop", data["meta"].get("t_stop", 0.0))
    temp_channel = measurement.get("temp_channel", data["meta"].get("temp_channel", "A"))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # More descriptive filename than IV sweeps
    filename = (
        f"{sample_name}_{mode_label}_"
        f"{t_start:.0f}-{t_stop:.0f}K.txt"
    )
    path = os.path.join(base_dir, filename)

    # Extract arrays
    time_s = data["time_s"]
    T_K = data["T_K"]
    V_V = data["V_V"]
    I_A = data["I_A"]

    # -------------------------------------------------------------------------
    # Write temperature sweep file
    # -------------------------------------------------------------------------
    with open(path, "w") as f:
        # Basic metadata
        f.write(f"# Sample: {sample_name}\n")
        f.write(f"# Mode: {mode_label}\n")
        f.write(f"# Timestamp: {timestamp}\n")

        # Dump measurement parameters for reproducibility
        f.write("# Measurement config:\n")
        for key, value in measurement.items():
            f.write(f"#   {key} = {value}\n")

        # Column header
        f.write("time_s\tT[K]\tV[V]\tI[A]\n")

        # Numerical data
        for t, T, V, I in zip(time_s, T_K, V_V, I_A):
            f.write(f"{t:.6e}\t{T:.6e}\t{V:.6e}\t{I:.6e}\n")

    print(f"[INFO] Saved temperature sweep data to {path}")
    return path

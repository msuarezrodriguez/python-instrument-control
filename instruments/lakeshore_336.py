# instruments/lakeshore_336.py

from __future__ import annotations
import time
from typing import Union

from qcodes.instrument import VisaInstrument


class LakeShore336(VisaInstrument):
    """
    Minimal QCoDeS driver for the Lake Shore Model 336 temperature controller.

    Focus:
      - Read temperature from inputs A–D
      - Get / set control loop setpoint (loops 1–4)
      - Get / set heater range (outputs 1–2)
      - Configure basic closed-loop control (OUTMODE)
      - Enable/disable setpoint ramp (RAMP)
      - Manual heater output for open-loop operation (MOUT)

    NOTE
    ----
    We DO NOT send *RST on init, to avoid wiping sensor curves and setup.
    Only *CLS (clear status) is issued.
    If you want a full reset, you should call reset() manually.
    """

    # Valid sensor channels
    _channels = ("A", "B", "C", "D")

    # Heater range code ↔ text map (RANGE command)
    _heater_range_to_code = {
        "off": 0,
        "low": 1,
        "medium": 2,
        "med": 2,
        "high": 3,
        "max": 3,  # alias for high
    }
    _heater_range_from_code = {
        v: k for k, v in _heater_range_to_code.items() if v in (0, 1, 2, 3)
    }

    # Output mode map (OUTMODE command)
    # 0 = Off, 1 = Closed Loop PID, 2 = Zone, 3 = Open Loop,
    # 4 = Monitor out, 5 = Warmup supply
    _mode_to_code = {
        "off": 0,
        "closed loop": 1,
        "closed_loop": 1,
        "pid": 1,
        "zone": 2,
        "open loop": 3,
        "open_loop": 3,
        "monitor": 4,
        "monitor out": 4,
        "warmup": 5,
        "warm-up": 5,
    }
    _mode_from_code = {
        0: "off",
        1: "closed loop",
        2: "zone",
        3: "open loop",
        4: "monitor",
        5: "warmup",
    }

    # Input channel code map for OUTMODE (control input)
    # 0 = None, 1 = A, 2 = B, 3 = C, 4 = D, 5–8 are D2–D5 (scanner)
    _input_to_code = {
        None: 0,
        "none": 0,
        "A": 1, "a": 1,
        "B": 2, "b": 2,
        "C": 3, "c": 3,
        "D": 4, "d": 4,
    }
    _input_from_code = {
        0: "none",
        1: "A",
        2: "B",
        3: "C",
        4: "D",
        5: "D2",
        6: "D3",
        7: "D4",
        8: "D5",
    }

    # =========================================================================
    # INITIALIZATION
    # =========================================================================
    def __init__(self, name: str, address: str, **kwargs) -> None:
        """
        Construct the instrument with a VISA address.

        Parameters
        ----------
        name : str
            QCoDeS instrument name.
        address : str
            VISA resource string, e.g. "GPIB0::22::INSTR".
        """
        super().__init__(name=name, address=address, **kwargs)

        # Do NOT reset here — most labs prefer to keep 336 configuration
        # self.write("*RST")
        self.write("*CLS")  # clear status/event registers

    # ----------------------------------------------------------------------
    # Alternative constructor: from GPIB address
    # ----------------------------------------------------------------------
    @classmethod
    def from_gpib(
        cls,
        gpib_address: int,
        gpib_bus: int = 0,
        name: str = "lakeshore_336",
    ) -> "LakeShore336":
        """
        Construct instrument from a plain GPIB address.

        Example
        -------
        ls = LakeShore336.from_gpib(22)
        """
        visa_address = f"GPIB{gpib_bus}::{gpib_address}::INSTR"
        return cls(name=name, address=visa_address)

    # =========================================================================
    # BASIC HELPERS
    # =========================================================================
    def get_idn(self) -> str:
        """
        Return identification string (*IDN?).
        """
        return self.ask("*IDN?")

    def clear_status(self) -> None:
        """
        Clear status/event registers (*CLS).
        """
        self.write("*CLS")

    # =========================================================================
    # TEMPERATURE READINGS
    # =========================================================================
    def get_temperature(self, channel: str = "A") -> float:
        """
        Read temperature (Kelvin) from the given input channel using KRDG?.

        Parameters
        ----------
        channel : {"A", "B", "C", "D"}
            Input sensor channel to query.

        Returns
        -------
        float
            Temperature in Kelvin.
        """
        ch = channel.upper()
        if ch not in self._channels:
            raise ValueError(f"Invalid channel {channel!r}. Must be one of {self._channels}.")

        resp = self.ask(f"KRDG? {ch}")
        # Typically returns a single float as a string
        return float(resp)

    def get_sensor_units(self, channel: str = "A") -> float:
        """
        Read raw sensor units from the given channel using SRDG?.

        Useful if you want to work directly in Ohms/Volts instead of Kelvin.

        Parameters
        ----------
        channel : {"A", "B", "C", "D"}

        Returns
        -------
        float
            Raw sensor reading.
        """
        ch = channel.upper()
        if ch not in self._channels:
            raise ValueError(f"Invalid channel {channel!r}. Must be one of {self._channels}.")

        resp = self.ask(f"SRDG? {ch}")
        return float(resp)

    # =========================================================================
    # SETPOINT AND RAMP
    # =========================================================================
    def get_setpoint(self, loop: int = 1) -> float:
        """
        Get setpoint of a control loop (1–4) using SETP?.

        Units are the preferred units of the control input (usually Kelvin).
        """
        resp = self.ask(f"SETP? {int(loop)}")
        return float(resp)

    def set_setpoint(self, loop: int = 1, value: float = 300.0) -> None:
        """
        Set setpoint of a control loop (1–4) using SETP.

        Parameters
        ----------
        loop : int
            Control loop index (1–4).
        value : float
            Setpoint value in the units of the control input (usually K).
        """
        self.write(f"SETP {int(loop)},{float(value)}")

    def get_ramp(self, loop: int = 1) -> tuple[float, bool]:
        """
        Query ramp parameters for a given loop using RAMP?.

        Returns
        -------
        (rate_K_per_min, enabled)
        """
        resp = self.ask(f"RAMP? {int(loop)}")
        # Manual: "rate, state"
        parts = resp.split(",")
        rate = float(parts[0])
        enabled = bool(int(parts[1])) if len(parts) > 1 else False
        return rate, enabled

    def set_ramp(self, loop: int = 1, rate_K_per_min: float = 1.0, enable: bool = True) -> None:
        """
        Configure the setpoint ramp for a control loop using RAMP.

        Parameters
        ----------
        loop : int
            Control loop index (1–4).
        rate_K_per_min : float
            Ramp rate in K/min (see manual, typically 0.1–100 K/min).
        enable : bool
            True → ramp on, False → ramp off.
        """
        state = 1 if enable else 0
        self.write(f"RAMP {int(loop)},{float(rate_K_per_min)},{state}")

    # =========================================================================
    # HEATER RANGE (RANGE) AND MANUAL OUTPUT (MOUT)
    # =========================================================================
    def get_heater_range(self, output: int = 1, as_text: bool = False) -> Union[int, str]:
        """
        Query heater range with RANGE?.

        Parameters
        ----------
        output : int
            Heater output index (1 or 2).
        as_text : bool
            If False → return integer code (0=off, 1=low, 2=medium, 3=high).
            If True  → return text ('off', 'low', 'medium', 'high').

        Returns
        -------
        int or str
        """
        resp = self.ask(f"RANGE? {int(output)}")
        code = int(resp)

        if as_text:
            return self._heater_range_from_code.get(code, f"unknown({code})")
        return code

    def set_heater_range(self, output: int = 1, heater_range: Union[int, str] = "off") -> None:
        """
        Set heater range via RANGE command.

        Parameters
        ----------
        output : int
            Heater output index (1 or 2).
        heater_range : int or str
            Either an integer (0–3) or one of:
                'off', 'low', 'medium', 'high'.
        """
        if isinstance(heater_range, str):
            key = heater_range.lower()
            if key not in self._heater_range_to_code:
                raise ValueError(
                    f"Invalid heater_range {heater_range!r}. "
                    f"Use one of {list(self._heater_range_to_code.keys())} or an integer 0–3."
                )
            code = self._heater_range_to_code[key]
        else:
            code = int(heater_range)

        self.write(f"RANGE {int(output)},{code}")

    def set_manual_output(self, output: int = 1, percent: float = 0.0) -> None:
        """
        Set manual heater output via MOUT.

        Parameters
        ----------
        output : int
            Heater output index (1 or 2).
        percent : float
            Manual output level, 0–100 (% of full scale on the selected range).

        Notes
        -----
        Only meaningful in Open Loop mode.
        """
        self.write(f"MOUT {int(output)},{float(percent)}")

    # =========================================================================
    # OUTPUT MODE AND CONTROL INPUT (OUTMODE)
    # =========================================================================
    def get_output_mode(self, output: int = 1) -> dict:
        """
        Query output mode using OUTMODE?.

        Returns
        -------
        dict
            Dictionary with:
              - mode_code  (int)
              - mode_text  (str)
              - input_code (int)
              - input_text (str)
              - powerup_enable (bool)
        """
        resp = self.ask(f"OUTMODE? {int(output)}")
        parts = resp.split(",")
        if len(parts) < 3:
            raise RuntimeError(f"Unexpected OUTMODE? response: {resp!r}")

        mode_code = int(parts[0])
        input_code = int(parts[1])
        powerup = bool(int(parts[2]))

        mode_text = self._mode_from_code.get(mode_code, f"unknown({mode_code})")
        input_text = self._input_from_code.get(input_code, f"unknown({input_code})")

        return {
            "mode_code": mode_code,
            "mode_text": mode_text,
            "input_code": input_code,
            "input_text": input_text,
            "powerup_enable": powerup,
        }

    def set_output_mode(
        self,
        output: int = 1,
        mode: str = "closed loop",
        input_channel: Union[str, None] = "A",
        powerup_enable: bool = False,
    ) -> None:
        """
        Configure the heater output mode via OUTMODE.

        Parameters
        ----------
        output : int
            Heater output index (1 or 2).
        mode : str
            One of: 'off', 'closed loop', 'zone', 'open loop',
                    'monitor', 'warmup'.
        input_channel : str or None
            'A', 'B', 'C', 'D' or None (no sensor).
        powerup_enable : bool
            If True  → output state restored after power cycle.
            If False → output forced OFF on powerup.
        """
        # Mode
        key = mode.lower()
        if key not in self._mode_to_code:
            raise ValueError(
                f"Invalid mode {mode!r}. Use one of {list(self._mode_to_code.keys())}."
            )
        mode_code = self._mode_to_code[key]

        # Input channel
        if isinstance(input_channel, str):
            inp_key = input_channel
        else:
            inp_key = input_channel

        if inp_key not in self._input_to_code:
            raise ValueError(
                f"Invalid input_channel {input_channel!r}. "
                f"Use one of {['A','B','C','D', None]} for this simple driver."
            )
        input_code = self._input_to_code[inp_key]

        pwr = 1 if powerup_enable else 0

        self.write(f"OUTMODE {int(output)},{mode_code},{input_code},{pwr}")

    # =========================================================================
    # CONVENIENCE: WAIT FOR TEMPERATURE / GO TO TEMPERATURE
    # =========================================================================
    def wait_for_temperature(
        self,
        channel: str = "A",
        target: float | None = None,
        tolerance: float = 0.1,
        timeout: float = 600.0,
        check_interval: float = 5.0,
        loop: int = 1,
        verbose: bool = True,
    ) -> float:
        """
        Wait until the temperature on `channel` is within `tolerance` (K)
        of `target`, or until `timeout` (s) is reached.

        Parameters
        ----------
        channel : {"A", "B", "C", "D"}
            Sensor channel to monitor.
        target : float or None
            Target temperature (K). If None, use current loop setpoint.
        tolerance : float
            Allowed deviation (absolute, in K).
        timeout : float
            Maximum allowed waiting time in seconds.
        check_interval : float
            Time between temperature checks (s).
        loop : int
            Control loop index whose setpoint is used if target is None.
        verbose : bool
            If True, print progress messages.

        Returns
        -------
        float
            Final measured temperature (K).

        Raises
        ------
        TimeoutError
            If temperature does not reach target ± tolerance within timeout.
        """
        ch = channel.upper()
        if ch not in self._channels:
            raise ValueError(f"Invalid channel {channel!r}. Must be one of {self._channels}.")

        if target is None:
            target = self.get_setpoint(loop=loop)

        if verbose:
            print(
                f"[LakeShore336] Waiting for T({ch}) → {target:.3f} K "
                f"(tolerance ±{tolerance:.3f} K, timeout {timeout:.1f} s)..."
            )

        t0 = time.time()
        last_T = None

        while True:
            now = time.time()
            if now - t0 > timeout:
                raise TimeoutError(
                    f"Temperature did not reach {target:.3f} K ±{tolerance:.3f} K "
                    f"within {timeout:.1f} s (last T = {last_T})."
                )

            T = self.get_temperature(ch)
            last_T = T

            if verbose:
                dt = T - target
                print(f"[LakeShore336] T({ch}) = {T:.3f} K (Δ = {dt:+.3f} K)")

            if abs(T - target) <= tolerance:
                if verbose:
                    print(f"[LakeShore336] Target reached within tolerance: {T:.3f} K")
                return T

            time.sleep(check_interval)

    def go_to_temperature(
        self,
        setpoint: float,
        loop: int = 1,
        channel: str = "A",
        tolerance: float = 0.1,
        timeout: float = 600.0,
        check_interval: float = 5.0,
        verbose: bool = True,
    ) -> float:
        """
        Convenience helper to move to a target temperature:

          1) Set SETP of the given loop.
          2) Wait until T(channel) is within tolerance of setpoint.

        Parameters
        ----------
        setpoint : float
            Target temperature in Kelvin.
        loop : int
            Control loop to set the setpoint on.
        channel : {"A", "B", "C", "D"}
            Sensor channel to monitor.
        tolerance, timeout, check_interval, verbose :
            Passed directly to wait_for_temperature().

        Returns
        -------
        float
            Final measured temperature (K).
        """
        if verbose:
            print(
                f"[LakeShore336] Setting setpoint of loop {loop} to {setpoint:.3f} K "
                f"and waiting for stabilization..."
            )

        self.set_setpoint(loop=loop, value=setpoint)
        return self.wait_for_temperature(
            channel=channel,
            target=setpoint,
            tolerance=tolerance,
            timeout=timeout,
            check_interval=check_interval,
            loop=loop,
            verbose=verbose,
        )

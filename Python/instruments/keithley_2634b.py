from qcodes.instrument import VisaInstrument


class Keithley2634B(VisaInstrument):
    """
    Minimal QCoDeS driver for the Keithley 2634B SMU.

    This wrapper provides:
        • Simple voltage-source mode (with current compliance)
        • Simple current-source mode (with voltage compliance)
        • Convenience methods to set/read V and I
        • Output ON/OFF control
        • Basic error queue inspection

    NOTE:
        The instrument is reset on initialization with *RST.
        This clears previous settings/programs on the SMU.
    """

    # =========================================================================
    # INITIALIZATION HELPERS
    # =========================================================================
    def __init__(self, name: str, address: str, **kwargs) -> None:
        """
        Construct the instrument with a VISA address.

        Parameters
        ----------
        name : str
            Internal QCoDeS name for this instrument instance.
        address : str
            VISA resource string, e.g. "GPIB0::19::INSTR".
        """
        super().__init__(name=name, address=address, **kwargs)

        # Full instrument reset and status clear
        # If you want to preserve custom scripts, remove *RST.
        self.write("*RST")
        self.write("*CLS")

    @classmethod
    def from_gpib(
        cls,
        gpib_address: int,
        gpib_bus: int = 0,
        name: str = "keithley_2634b",
    ):
        """
        Convenience constructor using just a GPIB address.

        Example
        -------
        smu = Keithley2634B.from_gpib(19)
        """
        visa_address = f"GPIB{gpib_bus}::{gpib_address}::INSTR"
        return cls(name=name, address=visa_address)

    # =========================================================================
    # BASIC QUERIES
    # =========================================================================
    def get_idn(self) -> str:
        """
        Return the identification string of the instrument (*IDN?).
        """
        return self.ask("*IDN?")

    # =========================================================================
    # VOLTAGE-SOURCE MODE
    # =========================================================================
    def configure_voltage_source(self, channel: str = "a", current_limit: float = 1e-3) -> None:
        """
        Configure a channel ('a' or 'b') as a DC voltage source
        with a given current compliance (in A).

        Parameters
        ----------
        channel : {"a", "b"}
            SMU channel to configure.
        current_limit : float
            Current compliance in amperes.
        """
        ch = channel.lower()
        self.write(f"smu{ch}.source.func = smu{ch}.OUTPUT_DCVOLTS")
        self.write(f"smu{ch}.source.limiti = {current_limit}")
        self.write(f"smu{ch}.source.autorangev = smu{ch}.AUTORANGE_ON")

        # Ensure output is OFF after configuration for safety
        self.enable_output(ch, on=False)

    def set_voltage(self, channel: str = "a", value: float = 0.0) -> None:
        """
        Set source voltage of a given channel (in volts).
        """
        ch = channel.lower()
        self.write(f"smu{ch}.source.levelv = {value}")

    def measure_current(self, channel: str = "a") -> float:
        """
        Measure current (A) from a given channel.

        Returns
        -------
        float
            Measured current in amperes.
        """
        ch = channel.lower()
        response = self.ask(f"print(smu{ch}.measure.i())")
        return float(response)

    # =========================================================================
    # CURRENT-SOURCE MODE
    # =========================================================================
    def configure_current_source(self, channel: str = "a", voltage_limit: float = 1.0) -> None:
        """
        Configure a channel ('a' or 'b') as a DC current source
        with a given voltage compliance (in V).

        Parameters
        ----------
        channel : {"a", "b"}
            SMU channel to configure.
        voltage_limit : float
            Voltage compliance in volts.
        """
        ch = channel.lower()
        self.write(f"smu{ch}.source.func = smu{ch}.OUTPUT_DCAMPS")
        self.write(f"smu{ch}.source.limitv = {voltage_limit}")
        self.write(f"smu{ch}.source.autorangei = smu{ch}.AUTORANGE_ON")

        # Ensure output is OFF after configuration for safety
        self.enable_output(ch, on=False)

    def set_current(self, channel: str = "a", value: float = 0.0) -> None:
        """
        Set source current of a given channel (in amperes).
        """
        ch = channel.lower()
        self.write(f"smu{ch}.source.leveli = {value}")

    def measure_voltage(self, channel: str = "a") -> float:
        """
        Measure voltage (V) from a given channel.

        Returns
        -------
        float
            Measured voltage in volts.
        """
        ch = channel.lower()
        response = self.ask(f"print(smu{ch}.measure.v())")
        return float(response)

    # =========================================================================
    # OUTPUT CONTROL
    # =========================================================================
    def enable_output(self, channel: str = "a", on: bool = True) -> None:
        """
        Enable or disable source output for a given channel.

        Parameters
        ----------
        channel : {"a", "b"}
            SMU channel to control.
        on : bool
            True → output ON, False → output OFF.
        """
        ch = channel.lower()
        state = f"smu{ch}.OUTPUT_ON" if on else f"smu{ch}.OUTPUT_OFF"
        self.write(f"smu{ch}.source.output = {state}")

    def all_outputs_off(self) -> None:
        """
        Turn off all outputs on both channels for safety.
        """
        self.write("smua.source.output = smua.OUTPUT_OFF")
        self.write("smub.source.output = smub.OUTPUT_OFF")

    # =========================================================================
    # ERROR QUEUE HELPERS
    # =========================================================================
    def get_next_error(self) -> str:
        """
        Read the next entry in the error queue.

        Returns
        -------
        str
            A string like '0,\"No error\"' or '-213,\"Setting conflict\"'.

        Notes
        -----
        The instrument-side command 'errorqueue.next()' returns a table
        {code, message}; wrapping it inside print(...) sends a text line
        back via VISA that we capture as a string.
        """
        return self.ask("print(errorqueue.next())")

    def print_error_queue(self) -> None:
        """
        Print all errors currently in the error queue until 'No error'.

        Useful for debugging when the instrument refuses settings
        or measurement calls.
        """
        while True:
            entry = self.get_next_error()
            print("Error queue entry:", entry)

            # Parse the code in the first field
            try:
                code_str = entry.split(",")[0]
                code = int(code_str)
            except Exception:
                # If parsing fails, do not risk an infinite loop
                break

            if code == 0:
                # 0 → "No error" → end of queue
                break

    def clear_errors(self) -> None:
        """
        Clear all errors from the instrument error queue.

        This repeatedly calls get_next_error() until it returns code 0.
        """
        while True:
            entry = self.get_next_error()

            try:
                code_str = entry.split(",")[0]
                code = int(code_str)
            except Exception:
                break

            if code == 0:
                # Reached "No error"
                break



# measurement/live_plot.py

import matplotlib.pyplot as plt

# =============================================================================
# BASE CLASS FOR LIVE PLOTS
# =============================================================================
class LivePlotIV:
    """
    Generic live plot engine for real-time experimental data.

    This class is used as the backbone for:
        - I–V and V–I sweeps
        - V–T and I–T sweeps

    It provides:
        - interactive matplotlib figure
        - dynamic autoscaling
        - optional pause before closing (pause_on_finish)
    """

    def __init__(self, xlabel: str, ylabel: str, title: str, pause_on_finish: float = 1.0):
        """
        Initialize a live-updating plot.

        Parameters
        ----------
        xlabel, ylabel : str
            Axis labels for the plot.
        title : str
            Window/figure title.
        pause_on_finish : float
            Seconds to keep the plot open after measurement ends.
            Use 0.0 to close immediately.
        """
        plt.ion()  # Interactive mode ON

        # Create figure + empty line
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], marker="o", linestyle="-")

        # Labels + formatting
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        self.fig.tight_layout()

        # Buffers
        self.xdata = []
        self.ydata = []

        self.pause_on_finish = pause_on_finish

    # -------------------------------------------------------------------------
    # Update plot with a new data point
    # -------------------------------------------------------------------------
    def update(self, x, y):
        """
        Append one (x, y) point to the curve and redraw.

        Called continuously during sweeps:
            • x = V, y = I   (voltage-source mode)
            • x = I, y = V   (current-source mode)
            • x = T, y = V   (V vs T mode)
            • x = T, y = I   (I vs T mode)
        """
        self.xdata.append(x)
        self.ydata.append(y)

        # Update line
        self.line.set_data(self.xdata, self.ydata)

        # Rescale axes dynamically
        self.ax.relim()
        self.ax.autoscale_view()

        # Force redraw
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    # -------------------------------------------------------------------------
    # Close plot once the measurement finishes
    # -------------------------------------------------------------------------
    def close(self):
        """
        Pause for 'pause_on_finish' seconds (optional),
        then close the live plot window.
        """
        if self.pause_on_finish > 0:
            plt.pause(self.pause_on_finish)
        plt.close(self.fig)



# =============================================================================
# LIVE PLOTS FOR I–V AND V–I SWEEPS
# =============================================================================

class LivePlotVoltageSource(LivePlotIV):
    """
    Live plot for voltage-source I–V sweeps.
        x = Voltage [V]
        y = Current [A]
    """

    def __init__(self, pause_on_finish: float = 1.0):
        super().__init__(
            xlabel="Voltage [V]",
            ylabel="Current [A]",
            title="Voltage-source I–V (live)",
            pause_on_finish=pause_on_finish,
        )


class LivePlotCurrentSource(LivePlotIV):
    """
    Live plot for current-source V–I sweeps.
        x = Current [A]
        y = Voltage [V]
    """

    def __init__(self, pause_on_finish: float = 1.0):
        super().__init__(
            xlabel="Current [A]",
            ylabel="Voltage [V]",
            title="Current-source V–I (live)",
            pause_on_finish=pause_on_finish,
        )



# =============================================================================
# LIVE PLOTS FOR TEMPERATURE SWEEPS
# =============================================================================

class LivePlotVvsT(LivePlotIV):
    """
    Live plot for V(T) during temperature sweeps at fixed current.
        x = T[K]
        y = V[V]
    """

    def __init__(self, sample_name: str = "", pause_on_finish: float = 1.0):
        title = "V–T (current-source, live)"
        if sample_name:
            title += f" – {sample_name}"

        super().__init__(
            xlabel="Temperature [K]",
            ylabel="Voltage [V]",
            title=title,
            pause_on_finish=pause_on_finish,
        )


class LivePlotIvsT(LivePlotIV):
    """
    Live plot for I(T) during temperature sweeps at fixed voltage.
        x = T[K]
        y = I[A]
    """

    def __init__(self, sample_name: str = "", pause_on_finish: float = 1.0):
        title = "I–T (voltage-source, live)"
        if sample_name:
            title += f" – {sample_name}"

        super().__init__(
            xlabel="Temperature [K]",
            ylabel="Current [A]",
            title=title,
            pause_on_finish=pause_on_finish,
        )


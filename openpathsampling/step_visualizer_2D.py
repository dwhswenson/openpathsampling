import time
import matplotlib
import matplotlib.pyplot as plt

import openpathsampling as paths
import logging
logger = logging.getLogger(__name__)

def add_trajectory(ax, x, y, color, accepted=True, **kwargs):
    ax.plot(x, y, color=color, **kwargs)  # trajectory
    face_color = color if accepted else 'none'
    ax.plot(x[-1], y[-1], marker='o', markeredgecolor=color,
            markerfacecolor=face_color)  # "arrowhead"
    return ax

class MCStepNumberArtist(object):
    def __init__(self, x, y, prefix=None, suffix=None, **kwargs):
        self.x = x
        self.y = y
        self.kwargs = kwargs
        if prefix is None:
            prefix = ""
        if suffix is None:
            suffix = ""
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, ax, step):
        stepnum = step.mccycle
        ax.text(self.x, self.y, self.prefix + str(stepnum) + self.suffix,
                **self.kwargs)


class StepVisualizer2D(object):
    def __init__(self, network, cv_x, cv_y, xlim, ylim, output_directory=None):
        self.network = network
        self.cv_x = cv_x
        self.cv_y = cv_y
        self.xlim = xlim
        self.ylim = ylim
        self.output_directory = output_directory
        self.background = None
        self._save_bg_axes = None
        self.extra_artists = []

        self.fig = None

        self.extent = self.xlim + self.ylim

        self.add_lines = [] # keeps state

        default_colors = {0 : 'r', 1 : 'b', 2 : 'g', 3 : 'y', 4 : 'm', 5 : 'c'}
        self.ensemble_colors = {}
        for transition in self.network.sampling_transitions:
            for i in range(len(transition.ensembles)):
                ens = transition.ensembles[i]
                self.ensemble_colors[ens] = default_colors[i % 6]
        for special_type in self.network.special_ensembles:
            for ens in self.network.special_ensembles[special_type].keys():
                self.ensemble_colors[ens] = 'k'

    def draw_arrowhead(self, sample, accepted=True):
        if accepted:
            face_color = self.ensemble_colors[sample.ensemble]
        else:
            face_color = 'none'
        # for now, our "arrowheads" are just circles
        frame = sample.trajectory[-1]
        self.ax.plot(
            self.cv_x(frame), self.cv_y(frame), marker='o',
            markeredgecolor=self.ensemble_colors[sample.ensemble],
            markerfacecolor=face_color,
            zorder=5
        )

    def _draw_list_of_samples(self, list_of_samples, accepted, linewidth,
                              zorder):
        for sample in list_of_samples:
            if sample.ensemble in self.ensemble_colors:
                self.ax = add_trajectory(
                    ax=self.ax,
                    x=self.cv_x(sample.trajectory),
                    y=self.cv_y(sample.trajectory),
                    accepted=accepted,
                    color=self.ensemble_colors[sample.ensemble],
                    linewidth=linewidth,
                    zorder=zorder
                )


    def draw_samples(self, samples, accepted=True):
        self.draw_background()
        self._draw_list_of_samples(samples, accepted, linewidth=2, zorder=2)
        return self.fig

    def draw_trials(self, change):
        if self.fig != self.background:
            self.draw_background()
        self._draw_list_of_samples(change.trials, accepted=False,
                                   linewidth=1, zorder=3)

        return self.fig


    def draw_background(self):
        # draw the background
        if self.background is not None:
            if self._save_bg_axes is None:
                self._save_bg_axes = self.background.axes
            self.fig = self.background
            for ax in self.fig.axes:
                self.fig.delaxes(ax)
            for ax in self._save_bg_axes:
                self.fig.add_axes(ax)
            self.ax = self.fig.axes[0].twinx()
            self.ax.cla()
        else:
            self.fig, self.ax = plt.subplots()

        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim)


    def draw(self, mcstep):
        self.draw_samples(mcstep.active)
        self.draw_trials(mcstep.change)
        for artist in self.extra_artists:
            artist(self.ax, mcstep)
        return self.fig


    def draw_ipynb(self, mcstep):
        try:
            import IPython.display
        except ImportError:
            logger.info("Not in IPython")
        else:
            IPython.display.clear_output(wait=True)
            fig = self.draw(mcstep)
            IPython.display.display(fig);
            plt.close()  # prevents crap in the output

    def replay_ipynb(self, steps, delay=0.1):
        for step in steps:
            self.draw_ipynb(step)
            time.sleep(delay)

    def draw_png(self, mcstep):
        pass

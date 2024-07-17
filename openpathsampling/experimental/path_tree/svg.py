import xml.etree.ElementTree as ET
from .options import canonicalize_mover
from .plotter import PathTreePlotter

def _stringify_values(dct):
    # also known as "XML is stupid"
    return {k: str(v) for k, v in dct.items()}

class SVGLines(PathTreePlotter):
    def __init__(self, options=None, hscale=10, vscale=10):
        super().__init__(options)
        self.hscale = hscale
        self.vscale = vscale

    def _reset(self):
        self.trajectories = []
        self.connectors = []
        self.min_x = float("inf")
        self.max_x = float("-inf")

    # @staticmethod
    # def step_basics(step, options):
    #     mover = canonicalize_mover(step.mover)
    #     mover_options = options.movers[mover]
    #     color = mover_options.color
    #     plot_segments = mover_options.get_left_right(step)
    #     return mover, color, plot_segments

    def draw_trajectory(self, row, step):
        plot_segments, color = self.get_step_plot_details(step)
        for left, right in plot_segments:
            if left < self.min_x:
                self.min_x = left
            if right > self.max_x:
                self.max_x = right

            attrib = {
                "width": (right - left) * self.hscale,
                "height": self.vscale // 2,
                "x": left * self.hscale,
                "y": row * self.vscale,
                "fill": color
            }
            elem = ET.Element("rect", attrib=_stringify_values(attrib))
            self.trajectories.append(elem)

    def draw_connector(self, x, bottom, top, step):
        attrib = {
            "x1": x * self.hscale,
            "y1": (bottom + 0.25) * self.vscale,
            "x2": x * self.hscale,
            "y2": (top + 0.5) * self.vscale,
            "style": "stroke:black",
        }
        elem = ET.Element("line", attrib=_stringify_values(attrib))
        self.connectors.append(elem)

    def build_svg(self):
        attrib = {
            "height": self.vscale * (len(self.trajectories) + 1),
            "width": self.hscale * (self.max_x - self.min_x),
            "xmlns": "http://www.w3.org/2000/svg"
        }
        root = ET.Element("svg", attrib=_stringify_values(attrib))
        for traj in self.trajectories:
            root.append(traj)
        for cnx in self.connectors:
            root.append(cnx)
        return root

    def draw(self, path_tree):
        self._reset()
        self.draw_trajectories(path_tree.path_tree_steps)
        root = self.build_svg()
        return ET.tostring(root)
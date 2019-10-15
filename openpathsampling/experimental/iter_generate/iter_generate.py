import sys
import openpathsampling as paths

from openpathsampling.engines.dynamics_engine import (
    EngineError, EngineNaNError, EngineMaxLengthError
)

import logging
logger = logging.getLogger(__name__)

def monkey_patch_all(paths):
    """Monkey patch the OPS namespace with this module"""
    DynamicsEngine = paths.engines.DynamicsEngine
    DynamicsEngine.iter_generate = iter_generate
    DynamicsEngine.generate = generate

    OpenMMEngine = paths.engines.openmm.Engine
    OpenMMEngine.snapshot_error_handler = openmm_custom_error_handler
    OpenMMEngine.validate_snapshot = openmm_validate_snapshot
    return paths

def openmm_validate_snapshot(self, snapshot, trajectory):
    if not self.is_valid_snapshot(snapshot):
        raise EngineNaNError("Engine generated NaN", trajectory)

def openmm_custom_error_handler(self, error, trajectory):
    e = sys.exc_info()
    se = str(e).lower()
    if 'nan' in se and ('particle' in se or 'coordinates' in se):
        # TODO: set message
        msg = 'nan'
        return EngineNaNError(msg, trajectory)
    return error

# TODO: move this to utils
def trajectorify(thing):
    """
    Take a snapshot, trajectory, or iterable, and make a trajectory of it
    """
    if hasattr(thing, '__iter__'):
        iterable = thing
    elif isinstance(thing, paths.engines.BaseSnapshot):
        iterable = [thing]
    else:
        raise RuntimeError("Can't make a trajectory out of " + str(thing))

    return paths.Trajectory(iterable)

def _clear_cache(snapshot):
    # clears the snapshot cache; handles errors for other snapshot types
    # Note that the implementation here may change; might add clear_cache()
    # method for *all* snapshots (no-op in some cases)
    try:
        snapshot.clear_cache()
    except AttributeError as e:
        if "clear_cache" not in str(e):
            raise e


def iter_generate(self, initial, running=None, direction=+1,
                  max_length=None):
    """
    Generator that returns the trajectory as it grows

    Parameters
    ----------
    initial : :class:`.Snapshot` or :class:`.Trajectory`
        initial conditions to run dynamics from
    running : list of callable
        conditions that return true if the trajectory should continue to run
    direction : +1 or -1
        whether to run the dynamics forward (+1) or backward (-1) in time
    max_length : int or None
        the maximum length to allow; default (None) will use the engine's
        `n_frames_max`.

    Yields
    ------
    :class:`.Trajectory` :
        the trajectory
    """
    trajectory = trajectorify(initial)

    # things that depend on direction
    get_snapshot = {+1 : lambda t: t[-1],
                    -1 : lambda t: t[0].reversed}[direction]
    add_frame = {+1: lambda s, t: t.append(s),
                 -1: lambda s, t: t.insert(0, s.reversed)}[direction]

    if max_length is None:
        max_length = self.options['n_frames_max']


    self.current_snapshot = get_snapshot(trajectory)

    stop = self.stop_conditions(trajectory=trajectory,
                                continue_conditions=running,
                                trusted=False)

    errors = []
    snapshot = None
    while not stop:
        # this will be once we have the external engine merged
        _clear_cache(snapshot)

        if len(trajectory) == max_length:
            raise EngineMaxLengthError(
                "Hit maximum trajectory length: %d frames" % max_length,
                trajectory
            )

        try:
            with self.interrupter():
                snapshot = self.generate_next_frame()
                self.validate_snapshot(snapshot, trajectory)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt. Shutting down simulation")
            self.stop(trajectory)
            raise
        except Exception as e:
            # if there's an error, shut down the trajectory
            logger.info("Error in dynamics")
            self.stop(trajectory)
            handled = self.snapshot_error_handler(e, trajectory)
            yield trajectory
            raise handled

        add_frame(snapshot, trajectory)  # depends on direction
        # now this is trusted
        yield trajectory
        stop = self.stop_conditions(trajectory=trajectory,
                                    continue_conditions=running,
                                    trusted=True)


def generate(self, snapshot, running=None, direction=+1):
    trajectory = None
    generator = self.iter_generate(initial=snapshot,
                                   running=running,
                                   direction=direction)
    for trajectory in generator:
        pass

    return trajectory

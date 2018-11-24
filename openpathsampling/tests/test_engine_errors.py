import pytest
from .test_helpers import CalvinistDynamics, make_1d_traj

from openpathsampling.engines.dynamics_engine import (EngineMaxLengthError,
                                                      EngineNaNError)

class CountRunsContinuation(object):
    """Stores whether it has been run. Always returns True (continue traj).
    """
    def __init__(self):
        self.has_run = 0

    def __call__(self, trajectory, trusted):
        self.has_run += 1
        return True

class TestEngineErrors(object):
    def setup(self):
        self.max_length_start = 0.1
        self.nan_start = 1.1
        self.other_start = 2.1
        self.engine = CalvinistDynamics(
            predestination = [self.max_length_start, 0.2, 0.3, 0.4, 0.5,
                              self.nan_start, 1.2, float('nan'),
                              self.other_start, 2.2]
        )
        self.engine.did_stop = False
        self.engine.options['n_frames_max'] = 3
        self.running = CountRunsContinuation()

    def test_max_length_fail(self):
        init_traj = make_1d_traj([0.0]*3 + [self.max_length_start])
        with pytest.raises(EngineMaxLengthError) as excinfo:
            traj = self.engine.generate(init_traj, [self.running])
            # TODO: test error message
        # note that even here, we check the stopping criteria -- not needed?
        assert self.running.has_run == 1
        assert self.engine.did_stop

    def test_max_length_stop(self):
        self.engine.options['on_max_length'] = 'stop'
        init_traj = make_1d_traj([0.0, self.max_length_start])
        traj = self.engine.generate(init_traj, [self.running])
        assert len(traj) == self.engine.options['n_frames_max']
        assert self.running.has_run == 2
        assert self.engine.did_stop

    def test_max_length_retry(self):
        self.engine.options['on_max_length'] = 'retry'
        self.engine.options['retries_when_max_length'] = 1
        pass

    def test_nan_fail(self):
        init_traj = make_1d_traj([self.nan_start])
        with pytest.raises(EngineNaNError) as excinfo:
            traj = self.engine.generate(init_traj, [self.running])
            # TODO: test error message
        assert self.running.has_run == 2
        assert self.engine.did_stop

    def test_nan_retry(self):
        pass

    def test_max_length_and_nan(self):
        # max length overrides nan
        pass

    def test_other_error(self):
        init_traj = make_1d_traj([self.other_start])
        with pytest.raises(IndexError):
            self.engine.generate(init_traj, [self.running])
        assert self.running.has_run == 2
        assert self.engine.did_stop

    def test_max_length_and_other(self):
        # other error should override retry?
        pass

    def test_nan_and_other(self):
        # other error should override retry?
        pass

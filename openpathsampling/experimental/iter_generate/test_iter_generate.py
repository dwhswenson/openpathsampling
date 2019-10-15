import pytest

import openpathsampling.tests.test_openmm_engine as test_openmm_engine
import openpathsampling.tests.test_dynamicsengine as test_dynamics_engine


setup_module = test_openmm_engine.setup_module

import openpathsampling as paths
from iter_generate import *

def setup_module():
    import openpathsampling as paths
    paths = monkey_patch_all(paths)
    test_openmm_engine.setup_module()

class TestDynamicsEngine(test_dynamics_engine.TestDynamicsEngine):
    pass

class TestOpenMMEngine(test_openmm_engine.TestOpenMMEngine):
    def test_fail_length(self):
        with pytest.raises(paths.engines.EngineMaxLengthError):
            super().test_fail_length()

    def test_retry_length(self):
        pytest.skip("New iter_generate does not do retries")

    def test_fail_nan(self):
        with pytest.raises(paths.engines.EngineNaNError):
            super().test_fail_nan()

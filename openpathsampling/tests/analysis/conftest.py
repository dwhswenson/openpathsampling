import pytest
import openpathsampling as paths

@pytest.fixture
def tis_network():
    paths.InterfaceSet._reset()
    cv = paths.FunctionCV("x", lambda s: s.xyz[0][0])
    state_A = paths.CVDefinedVolume(cv, float("-inf"), 0)
    state_B = paths.CVDefinedVolume(cv, 1.0, float("inf"))
    interfaces = paths.VolumeInterfaceSet(cv, float("-inf"), [0.0, 0.3, 0.6])
    network = paths.MISTISNetwork([(state_A, interfaces, state_B)])
    return network

@pytest.fixture
def scheme(tis_network):
    engine = paths.engines.NoEngine({'n_spatial': 3, 'n_atoms': 1})
    scheme = paths.DefaultScheme(network=tis_network, engine=engine)
    scheme.move_decision_tree()  # to build the movers
    return scheme



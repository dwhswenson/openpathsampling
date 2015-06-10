__author__ = 'jan-hendrikprinz'

import mdtraj as md
import simtk.unit as u
import numpy as np
import openpathsampling as paths

from collections import OrderedDict
import weakref

import sys


def refresh_output(output_str):
    try:
        import IPython.display
        IPython.display.clear_output(wait=True)
    except ImportError:
        pass
    print(output_str)
    sys.stdout.flush()


def updateunits(func):
    def inner(self, *args, **kwargs):
        my_units = {
            'length' : u.nanometer,
            'velocity' : u.nanometer / u.picoseconds,
            'energy' : u.kilojoules_per_mole
        }

        if 'units' in kwargs and kwargs['units'] is not None:
            my_units.update(kwargs['units'])

        kwargs['units'] = my_units

        return func(self, *args, **kwargs)

    return inner


@updateunits
def snapshot_from_pdb(pdb_file, units = None):
    """
    Construct a Snapshot from the first frame in a pdb file without velocities

    Parameters
    ----------
    pdb_file : str
        The filename of the .pdb file to be used

    Returns
    -------
    Snapshot
        the constructed Snapshot

    """
    pdb = md.load(pdb_file)

    velocities = np.zeros(pdb.xyz[0].shape)

    snapshot = paths.Snapshot(
        coordinates=u.Quantity(pdb.xyz[0], units['length']),
        velocities=u.Quantity(velocities, units['velocity']),
        box_vectors=u.Quantity(pdb.unitcell_vectors[0], units['length']),
        potential_energy=u.Quantity(0.0, units['energy']),
        kinetic_energy=u.Quantity(0.0, units['energy']),
        topology=paths.MDTrajTopology(pdb.topology)
    )

    return snapshot

def trajectory_from_mdtraj(mdtrajectory):
    """
    Construct a Trajectory object from an mdtraj.Trajectory object

    Parameters
    ----------
    mdtrajectory : mdtraj.Trajectory
        Input mdtraj.Trajectory

    Returns
    -------
    Trajectory
        the constructed Trajectory instance
    """
    trajectory = paths.Trajectory()
    empty_momentum = paths.Momentum()
    for frame_num in range(len(mdtrajectory)):
        # mdtraj trajectories only have coordinates and box_vectors
        coord = u.Quantity(mdtrajectory.xyz[frame_num], u.nanometers)
        if mdtrajectory.unitcell_vectors is not None:
            box_v = u.Quantity(mdtrajectory.unitcell_vectors[frame_num],
                             u.nanometers)
        else:
            box_v = None
        config = paths.Configuration(coordinates=coord, box_vectors=box_v)

        snap = paths.Snapshot(
            configuration=config,
            momentum=empty_momentum,
            topology=paths.MDTrajTopology(mdtrajectory.topology)
        )
        trajectory.append(snap)

    return trajectory

@updateunits
def empty_snapshot_from_openmm_topology(topology, units):
    """
    Return an empty snapshot from an openmm.Topology object using the specified units.

    Parameters
    ----------
    topology : openmm.Topology
        the topology representing the structure and number of atoms
    units : dict of {str : simtk.unit.Unit }
        representing a dict of string representing a dimension ('length', 'velocity', 'energy') pointing the
        the simtk.unit.Unit to be used

    Returns
    -------
    Snapshot
        the complete snapshot with zero coordinates and velocities

    """
    n_atoms = topology.n_atoms

    snapshot = paths.Snapshot(
        coordinates=u.Quantity(np.zeros((n_atoms, 3)), units['length']),
        velocities=u.Quantity(np.zeros((n_atoms, 3)), units['velocity']),
        box_vectors=u.Quantity(topology.setUnitCellDimensions(), units['length']),
        potential_energy=u.Quantity(0.0, units['energy']),
        kinetic_energy=u.Quantity(0.0, units['energy']),
        topology=paths.MDTrajTopology(md.Topology.from_openmm(topology))
    )

    return snapshot

def units_from_snapshot(snapshot):
    """
    Returns a dict of simtk.unit.Unit instances that represent the used units in the snapshot

    Parameters
    ----------
    snapshot : Snapshot
        the snapshot to be used

    Returns
    -------
    units : dict of {str : simtk.unit.Unit }
        representing a dict of string representing a dimension ('length', 'velocity', 'energy') pointing the
        the simtk.unit.Unit to be used
    """

    units = {}
    if snapshot.coordinates is not None:
        if hasattr(snapshot.coordinates, 'unit'):
            units['length'] = snapshot.coordinates.unit
        else:
            units['length'] = u.Unit({})

    if snapshot.potential_energy is not None:
        if hasattr(snapshot.potential_energy, 'unit'):
            units['energy'] = snapshot.potential_energy.unit
        else:
            units['energy'] = u.Unit({})

    if snapshot.velocities is not None:
        if hasattr(snapshot.velocities, 'unit'):
            units['velocity'] = snapshot.velocities.unit
        else:
            units['velocity'] = u.Unit({})

    return units

def to_openmm_topology(obj):
    """
    Contruct an openmm.Topology file out of a Snapshot or Configuration object. This uses the
    mdtraj.Topology in the Configuration as well as the box_vectors.

    Parameters
    ----------
    obj : Snapshot or Configuration
        the object to be used in the topology construction

    Returns
    -------
    openmm.Topology
        an object representing an openmm.Topology
    """
    if obj.topology is not None:
        if hasattr(obj.topology, 'md'):
            openmm_topology = obj.topology.md.to_openmm()
            box_size_dimension = np.linalg.norm(obj.box_vectors.value_in_unit(u.nanometer), axis=1)
            openmm_topology.setUnitCellDimensions(box_size_dimension)

            return openmm_topology
    else:
        return None

class LRUCache(OrderedDict):
    """
    Implements a simple Least Recently Used Cache

    Very simple using collections.OrderedDict. The size can be change during
    run-time
    """
    def __init__(self, size_limit):
        self._size_limit = size_limit
        OrderedDict.__init__(self)
        self._check_size_limit()

    @property
    def size_limit(self):
        return self._size_limit

    @size_limit.setter
    def size_limit(self, new_size):
        if new_size < self.size_limit:
          self._check_size_limit()

        self._size_limit = new_size

    def __setitem__(self, key, value, **kwargs) :
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        if self.size_limit is not None:
            while len(self) > self.size_limit:
                self.popitem(last=False)

class WeakLRUCache(OrderedDict):
    """
    Implements a cache that keeps weak references to all elements

    In addition it uses a simple Least Recently Used Cache to make sure a portion
    of the last used elements are still present. Usually this number is 100.

    """
    def __init__(self, size_limit=100):
        """
        Parameters
        ----------
        size_limit : int
            integer that defines the size of the LRU cache. Default is 100.
        """
        OrderedDict.__init__(self)

        self._size_limit = size_limit
        self._weak_cache = weakref.WeakValueDictionary()

    @property
    def size_limit(self):
        return self._size_limit

    def __getitem__(self, item):
        try:
            return OrderedDict.__getitem__(self, item)
        except(KeyError):
            return self._weak_cache[item]

    @size_limit.setter
    def size_limit(self, new_size):
        if new_size < self.size_limit:
          self._check_size_limit()

        self._size_limit = new_size

    def __setitem__(self, key, value, **kwargs) :
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        if self.size_limit is not None:
            while len(self) > self.size_limit:
                self._weak_cache.__setitem__(*self.popitem(last=False))

class WeakCache(weakref.WeakValueDictionary):
    """
    Implements a cache that keeps weak references to all elements
    """

class WeakLimitCache(dict):
    """
    Implements a cache that keeps weak references to all elements

    In addition it uses a simple Least Recently Used Cache to make sure a portion
    of the last used elements are still present. Usually this number is 100.

    """
    def __init__(self, size_limit=100):
        """
        Parameters
        ----------
        size_limit : int
            integer that defines the size of the LRU cache. Default is 100.
        """
        dict.__init__(self)

        self._size_limit = size_limit
        self._weak_cache = weakref.WeakValueDictionary()

    @property
    def size_limit(self):
        return self._size_limit

    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except(KeyError):
            return self._weak_cache[item]

    @size_limit.setter
    def size_limit(self, new_size):
        if new_size < self.size_limit:
          self._check_size_limit()

        self._size_limit = new_size

    def __setitem__(self, key, value, **kwargs) :
        if self.size_limit is not None:
            if len(self) == self.size_limit:
                self._weak_cache[key] = value
            else:
                dict.__setitem__(self, key, value)

    def _check_size_limit(self):
        if self.size_limit is not None:
            while len(self) > self.size_limit:
                self._weak_cache.__setitem__(*self.popitem())
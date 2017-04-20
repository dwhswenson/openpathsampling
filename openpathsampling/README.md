# OpenPathSampling: Source code overview

OpenPathSampling consists of several subpackages. This provides an overview
of where various aspects of the code are located.

* `analysis/`: Analyzing the output of OPS simulations
* `data_representation/`: In-memory storage of simulation data (`Sample`,
  `SampleSet`, `MoveChange`, etc.)
* `engines/`: Support for various dynamics engines, including `Trajectory`
  and `Snapshot` classes.
* `ensembles/`: Classes representing path ensembles
* `high_level/`: Classes related to the high-level `TransitionNetwork` and
  `MoveScheme`/`MoveStrategy` objects. NOTE: For externally contributed path
  movers, the `MoveStrategy` should be part of the path mover file, and
  stored in `pathmovers/`.
* `netcdfplus/`: The general NetCDF+ storage (to file) framework.
* `numerics/`: Miscellaneous numerical methods (our histogram class; our
  value-dict-to-function class, etc.)
* `pathmovers/`: Monte Carlo movers in path space
* `resources/`: Non-code resources, e.g. logging configuration files and
  default CSS file for visualization
* `storage/`: OPS-specific storage subclasses (based on NetCDF+)

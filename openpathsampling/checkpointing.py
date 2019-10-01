from functools import wraps
import inspect
import os.path
import shutil
import json

import sys


def has_uuid(obj):
    return hasattr(obj, '__uuid__')

def get_uuid(obj):
    return getattr(obj, '__uuid__', None)

def as_uuid(obj):
    """Returns the UUID if it has one, otherwise assumes input *is* the UUID

    Parameters
    ----------
    obj : UUID (int) or object with a UUID
        the thing to extract a UUID from

    Returns
    -------
    int :
        the UUID
    """
    return getattr(obj, '__uuid__', obj)


# TODO: something else to simplify labelling?
def _uuid_label(obj, sublabel):
    return str(get_uuid(obj)) + '-' + sublabel

def _instance_method_label(method):
    return _uuid_label(method.__self__, method.__name__)

def _numbered_label(label, number):
    return label + '-' + str(number)


class Checkpointer(object):
    def __init__(self):
        self.sequence_number = 0
        self.data_sequence = 0
        self._data = {}

    def _data_method_label(self, method):
        return _numbered_label(_instance_method_label(method),
                               self.data_sequence)

    def _data_label(self, obj, data_label):
        return _numbered_label(_uuid_label(obj, data_label),
                               self.data_sequence)

    def _update_basename(self, method):
        self.sequence_number += 1
        self.basename = _numbered_label(_instance_method_label(method),
                                        self.sequence_number)
        return self.basename

    def delete_checkpoint(self):
        pass

    def data_method(self, method):
        """Decorator for checkpointing results of data creation methods.

        Caches results of the given method in the checkpoint file; this
        ensures reproducibility of stochastic parts of the simulation.
        """
        raise NotImplementedError()

    def data(self, data, obj, data_label):
        """Store pure data objects in the checkpoint files.
        """
        raise NotImplementedError()

    def checkpointed(self, method):
        raise NotImplementedError()

    def _add_checkpoint_kwarg(self, method):
        # this handles old things without the checkpoints argument
        # REMOVE IN 2.0: replace wrapping with just `return method`
        # This is a fancy trick: injects itself into the next frame if
        # the function has a checkpoints argument. Otherwise, nothing.

        argname = 'checkpoints'  # in case we change it later
        func_args = getfullargspec(method).args

        @wraps(method)
        def wrapped(*args, **kwargs):
            if argname in func_args:
                kwargs.update({argname: self})
            return method(*args, **kwargs)

        return wrapped


class DummyCheckpoints(Checkpointer):
    """Turn off checkpointing
    """
    def __init__(self, directory=None):
        pass

    def data_method(self, method):
        return method

    def data(self, data, obj, data_label):
        return data

    def checkpointed(self, method):
        return self._add_checkpoint_kwarg(method)

    def create_writer(self):
        return self


class StepCheckpointBase(Checkpointer):
    """Per-step information about checkpointing.

    This is the object that is used internally. Usually the user won't need
    to use this, because :class:`.Checkpointing` is a factory that creates
    instances of this.

    Parameters
    ----------
    directory : str
        Directory where the checkpoint files will be kept. Must not exist
        before this is made.
    """
    def __init__(self, directory):
        super(StepCheckpoints, self).__init__()
        self.directory = directory
        os.makedirs(self.directory)

    def checkpoint_basename(self, obj, method, sequence_number=None):
        """Directory and basename for data related to a checkpoint file.

        The basename is of the format $DIRECTORY/$UUID-$METHOD-$NUMBER where
        the $UUID is the UUID of an object, the $METHOD is the name of the
        method being checkpointed, and the $NUMBER is the number in sequence
        of checkpoints in this step.

        Extensions can be added by client code.

        Parameters
        ----------
        obj : UUID-containing object or UUID
            the object or UUID for the UUID part of the filename
        method : str
            name of the method to be checkpointed
        sequence_number : int or None
            if None, the internal counter is used to set the sequence
            number

        Returns
        -------
        str :
            the basename for checkpoint files
        """
        if sequence_number is None:
            sequence_number = self.sequence_number
        fname = (str(as_uuid(obj)) + "-" + str(method) + "-"
                 + str(sequence_number))
        return os.path.join(self.directory, fname)

    def load_checkpoint(self, obj, method, storage, uuid_labels,
                        sequence_number=None):
        pass

    def delete_checkpoint(self):
        """Removes all files from the checkpoint.

        Warning
        -------

        Do not put other files in the directory for a checkpoint while the
        simulation is running! All files will be deleted when the step
        completes and is saved to disk.
        """
        shutil.rmtree(self.directory)


class StepCheckpointWriter(StepCheckpointBase):
    def data_method(self, method):
        label = self.data_method_label(method)

        @wraps(method)
        def wrapper(*args, **kwargs):
            if label not in self._data:
                self._data[label] = method(*args, **kwargs)
            return self._data[label]

        self.data_sequence += 1

        return wrapper

    def data(self, data):
        label = self.data_label(obj, data_label)
        self._data[label] = data
        self.data_sequence += 1
        return data

    def checkpointed(self, method):
        pass

    def write(self):
        pass



class Checkpointing(object):
    """User-facing class for checkpoint management.

    Parameters
    ----------
    root_dir : str
        The name of the directory in which checkpoint data should be stored.
        Default input (None) uses a directory '.ops_checkpoints' within the
        current working directory.
    """
    Writer = StepCheckpoints
    def __init__(self, root_dir=None):
        if root_dir is None:
            root_dir = '.ops_checkpoints'
        self.root_dir = root_dir

    def make_checkpoint_writer(self, simulation, step):
        """Create the actual checkpoint writer; one per simulation step.

        Parameters
        ----------
        simulation : object with UUID
            Usually the :class:`.PathSimulator`. The UUID of this object is
            used as the outer directory in which checkpoints are kept.
        step : int
            The step number; used for an inner directory to store checkpoint
            files.

        Returns
        -------
        class:`.StepCheckpoints` :
            object to manage checkpoints for this simulation step
        """
        directory = os.path.join(self.root_dir, str(get_uuid(simulation)),
                                 str(step))
        return self.Writer(directory)

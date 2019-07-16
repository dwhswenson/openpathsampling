import os.path
import shutil
import json

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


class StepCheckpoints(object):
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
        self.directory = directory
        self.sequence_number = 0
        os.mkdir(self.directory)

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

    def write_checkpoint(self, obj, method, checkpoint_data, next_checkpoint):
        dct = {'data': dict(checkpoint_data),
               'next': dict(next_checkpoint)}  # make copies
        for key, value in dct['data'].items():
            if has_uuid(value):
                dct['data'][key] = get_uuid(value)

        if dct['next']:
            dct['next']['object'] = get_uuid(dct['next']['object'])

        dct = {'method': str(method),
               'data': savable_dict}

        with open(self.checkpoint_basename(obj, method) + ".json", 'w') as f:
            f.write(json.dumps(dct))

        self.sequence_number += 1

    def load_checkpoint(self, obj, method, storage, uuid_labels,
                        sequence_number=None):
        basename = self.checkpoint_basename(obj, method, sequence_number)
        with open(basename + ".json", 'r') as f:
            dct = json.load(f)

        for label in uuid_labels:
            # does this correctly get by UUID?
            dct['data'][label] = storage.load(dct['data'][label])

        dct_next = dct['next']
        if dct_next:
            dct_next['object'] = storage.load(dct_next['object'])

        if sequence_number is None:
            self.sequence_number += 1

    def delete_checkpoint(self):
        """Removes all files from the checkpoint.

        Warning
        -------

        Do not put other files in the directory for a checkpoint while the
        simulation is running! All files will be deleted when the step
        completes and is saved to disk.
        """
        shutil.rmtree(self.directory)


class Checkpointing(object):
    """User-facing class for checkpoint management.
    """
    Writer = StepCheckpoints
    def __init__(self, root_dir=None):
        if root_dir is None:
            root_dir = '.ops_checkpoints'
        self.root_dir = root_dir

    def make_checkpoint_writer(self, simulation, step):
        directory = os.path.join(root_dir, str(get_uuid(simulation)),
                                 str(step))
        return self.Writer(directory)


import os.path
import json

def has_uuid(obj):
    return hasattr(obj, '__uuid__')

def get_uuid(obj):
    return getattr(obj, '__uuid__', None)


class StepCheckpoints(object):
    """A separate Checkpi
    """
    def __init__(self, directory):
        self.directory = directory
        self.sequence_number = 0
        os.mkdir(self.directory)

    def checkpoint_basename(self, obj, method, sequence_number=None):
        if sequence_number is None:
            sequence_number = self.sequence_number
        fname = str(get_uuid(obj)) + str(method) + str(sequence_number)
        return os.path.join(self.directory, str(get_uuid(obj)) + str(method))

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


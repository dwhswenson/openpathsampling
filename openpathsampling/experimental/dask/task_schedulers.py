from openpathsampling.netcdfplus import StorableNamedObject

try:
    import dask
    import dask.distributed
except ImportError:
    HAS_DASK = False
else:
    HAS_DASK = True

from openpathsampling.experimental.storage.serialization_helpers import (
    get_uuid, has_uuid, encode_uuid, decode_uuid, encoded_uuid_re
)

from openpathsampling.experimental import storage
serialization = storage.ops_storage.ops_class_info


class TaskScheduler(StorableNamedObject):
    def wrap_task(self, task, *args, **kwargs):
        return task(*args, **kwargs)

    def wrap_hook(self, hook, *args, **kwargs):
        # hook wrap with fire_and_forget in dask! only care about
        # side-effects
        return hook(*args, **kwargs)

def serialize(*args, **kwargs):
    def serialize_to_dict(obj):
        if isinstance(obj, StorableObject):
            return (obj.__class__, obj.to_dict())
        else:
            return (obj.__class__, obj)

    outargs = [serialize_to_dict(arg) for arg in args]
    outkwargs = {k: serialize_to_dict(kwargs[k]) for k in kwargs}
    return outargs, outkwargs

def deserialize(*args, **kwargs):
    def deserialize_from_dict(cls_, serialized):
        if issubclass(cls_, StorableObject):
            return cls_.from_dict(dct)
        else:
            return serialized

    outargs = [deserialize_from_dict(*arg) for arg in args]
    outkwargs = {k: deserialized_from_dict(*kwarg[k]) for k in kwargs}
    return outargs, outkwargs

def deserialze_and_task(task, *serialized_args, **serialized_kwargs):
    args, kwargs = deserialize(*serialized_args, **serialized_kwargs)
    return task(*args, **kwargs)

def serialize_args_kwargs(args, kwargs):
    to_serialize = []
    arg_uuids = []
    kwarg_uuids = {}
    for arg in args:
        if has_uuid(arg):
            to_serialize.append(arg)
            arg_uuids.append(encode_uuid(arg))
        else:
            arg_uuids.append(arg)

    for key, kwarg in kwargs.items():
        if has_uuid(kwarg):
            to_serialize.append(kwarg)
            kwarg_uuids[key] = encode_uuid(kwarg)
        else:
            kwarg_uuids[key] = kwarg

    serialized = serialization.serialize(to_serialize)
    return arg_uuid, kwarg_uuids, serialized


class DaskTaskScheduler(TaskScheduler):
    def __init__(self, client):
        import dask.distributed  # raise ImportError if missing
        self.client = client

    def wrap_task(self, task, *args, **kwargs):
        print task
        return self.client.submit(task, *args, pure=False, **kwargs)

    def wrap_method(self, instance, method_name):
        # need wrap_method because we typically can't pickle
        # sim.single_step (because of some weird issues in cloudpickling of
        # CVs)
        def run_step(self, serialized_instance, method_name, *args,
                     **kwargs):
            # deserialize instance
            # method = getattr(deserialized, method_name)
            # method(*args, **kwargs)
            pass

        # serialize instance
        # wrap the run step method
        # self.client.submit(


    def wrap_hook(self, hook, *args, **kwargs):
        for arg in args:
            if has_uuid(arg):
                to_serialize.append(arg)
                arg_uuids
        return self.client.submit(hook, *args, **kwargs)


from __future__ import absolute_import
import pytest
# from nose.tools import (assert_equal, assert_not_equal, assert_almost_equal,
                        # raises, assert_true)
# from nose.plugins.skip import Skip, SkipTest

from openpathsampling.tests.test_helpers import (
    true_func, assert_equal_array_array, make_1d_traj, data_filename,
    assert_items_equal
)

import openpathsampling as paths

from openpathsampling.experimental.dask.task_schedulers import *

import logging
logging.getLogger('openpathsampling.initialization').setLevel(logging.CRITICAL)
logging.getLogger('openpathsampling.ensemble').setLevel(logging.CRITICAL)
logging.getLogger('openpathsampling.storage').setLevel(logging.CRITICAL)
logging.getLogger('openpathsampling.netcdfplus').setLevel(logging.CRITICAL)

def mock_task(argument, kwargument):
    return argument + kwargument

class MockHook(object):
    def __init__(self):
        self.val = None

    def hook(self, argument, kwargument):
        self.val = argument + kwargument

class TestTaskScheduler(object):
    def setup(self):
        self.sched = TaskScheduler()

    def test_wrap_task(self):
        assert self.sched.wrap_task(mock_task, 1, kwargument=2) == 3

    def test_wrap_hook(self):
        assert self.sched.wrap_hook(mock_task, 1, kwargument=2) == 3


class TestDaskTaskScheduler(object):
    @staticmethod
    def setup_test_cluster(distributed, n_workers=4, n_attempts=3):
        """Set up a test cluster using dask.distributed. Try up to
        n_attempts times, and skip the test if all attempts fail."""
        # taken from contact map
        cluster = None
        for _ in range(n_attempts):
            try:
                cluster = distributed.LocalCluster(n_workers=n_workers)
            except AttributeError:
                # should never get here, because should have already skipped
                pytest.skip("dask.distributed not installed")
            except distributed.TimeoutError:
                continue
            else:
                return cluster
        # only get here if all retries fail
        pytest.skip("Failed to set up distributed LocalCluster")

    def setup(self):
        dask = pytest.importorskip('dask')  # pylint: disable=W0612
        distributed = pytest.importorskip('dask.distributed')
        cluster = self.setup_test_cluster(distributed, n_workers=4)
        client = distributed.Client(cluster)
        self.sched = DaskTaskScheduler(client)

    def test_wrap_task(self):
        wrapped = self.sched.wrap_task(mock_task, 1, kwargument=2)
        assert isinstance(wrapped, dask.distributed.Future)
        assert wrapped.result() == 3

    def test_wrap_hook(self):
        # TODO: modify hooks to allow stored state as output?
        hook = MockHook()
        self.sched.wrap_hook(hook.hook, 1, kwargument=2)

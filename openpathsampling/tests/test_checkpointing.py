import pytest
from openpathsampling.checkpointing import *

from unittest import mock
import tempfile
import os

class TestStepCheckpoints(object):
    def setup(self):
        self.uuid_obj = mock.NonCallableMock(__uuid__="foo")
        tmpdir = tempfile.mkdtemp()
        self.directory = os.path.join(tmpdir, "checkpoints")
        self.checkpoints = StepCheckpoints(self.directory)

    @pytest.mark.parametrize('sequence_number,expected',
                             [(None, 'foo-bar-0'), (5, 'foo-bar-5')],
                             ids=["None", "5"])
    def test_checkpoint_basename(self, sequence_number, expected):
        basename = self.checkpoints.checkpoint_basename(
            obj=self.uuid_obj,
            method='bar',
            sequence_number=sequence_number
        )
        full_expected = os.path.join(self.directory, expected)
        assert basename == full_expected

    def test_delete_checkpoint(self):
        assert os.path.isdir(self.checkpoints.directory)
        self.checkpoints.delete_checkpoint()
        assert not os.path.isdir(self.checkpoints.directory)

    # TODO: add more tests for reading/writing


class TestCheckpointing(object):
    def setup(self):
        self.tmpdir = tempfile.mkdtemp()
        self.sim = mock.NonCallableMock(__uuid__="SIM-UUID")
        self.checkpointing = Checkpointing(root_dir=self.tmpdir)

    def test_default_init(self):
        checkpointing = Checkpointing()
        assert checkpointing.root_dir == ".ops_checkpoints"

    def test_init(self):
        assert self.checkpointing.root_dir == self.tmpdir

    def test_make_checkpoint_writer(self):
        writer = self.checkpointing.make_checkpoint_writer(self.sim, 10)
        writer_dir = writer.directory
        head, number_dir = os.path.split(writer_dir)
        root, sim_dir = os.path.split(head)
        assert root == self.checkpointing.root_dir
        assert sim_dir == get_uuid(self.sim)
        assert number_dir == str(10)



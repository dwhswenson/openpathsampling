'''
@author: David W.H. Swenson
'''

from builtins import range
from builtins import object
import pytest
from .test_helpers import assert_items_equal, assert_same_items

from openpathsampling.engines.trajectory import Trajectory
from openpathsampling.ensemble import LengthEnsemble
from openpathsampling.sample import *
from openpathsampling.sample import Sample


class TestSampleSet(object):
    def setup_method(self):
        self.ensA = LengthEnsemble(1)
        self.ensB = LengthEnsemble(2)
        traj0A = Trajectory([0.5])
        traj1A = Trajectory([1.0])
        traj2B = Trajectory([0.5, 0.75])
        traj2B_ = Trajectory([0.8, 0.9])
        self.s0A = Sample(replica=0, trajectory=traj0A, ensemble=self.ensA)
        self.s1A = Sample(replica=1, trajectory=traj1A, ensemble=self.ensA)
        self.s2B = Sample(replica=2, trajectory=traj2B, ensemble=self.ensB)
        self.s2B_ = Sample(replica=2, trajectory=traj2B_, ensemble=self.ensB)
        self.testset = SampleSet([self.s0A, self.s1A, self.s2B])

    def test_equality(self):
        testset2 = SampleSet([self.s0A, self.s1A, self.s2B])
        assert self.testset == testset2

    def test_initialization(self):
        self.testset.consistency_check()

    def test_iter(self):
        samps = [self.s0A, self.s1A, self.s2B]
        for samp in self.testset:
            assert samp in samps

    def test_contains(self):
        samps = [self.s0A, self.s1A, self.s2B]
        for samp in samps:
            assert samp in self.testset

    def test_len(self):
        assert len(self.testset) == 3

    def test_getitem_ensemble(self):
        assert self.testset[self.ensB] == self.s2B
        # TODO: add test that we pick at random for ensA

    def test_getitem_replica(self):
        assert self.testset[0] == self.s0A
        assert self.testset[1] == self.s1A
        assert self.testset[2] == self.s2B
        # TODO: add test that we pick at random

    def test_setitem_ensemble(self):
        ensC = LengthEnsemble(3)
        traj3C = Trajectory([-0.5, -0.25, 0.1])
        s3C = Sample(replica=3, trajectory=traj3C, ensemble=ensC)
        self.testset[ensC] = s3C
        self.testset.consistency_check()
        assert len(self.testset) == 4

    def test_setitem_replace_ensemble(self):
        self.testset[self.ensB] = self.s2B_
        assert self.s2B not in self.testset
        assert self.s2B_ in self.testset
        assert self.testset[2] == self.s2B_
        assert self.testset[self.ensB] == self.s2B_
        # TODO add test that we replace at random

    def test_setitem_replica(self):
        ensC = LengthEnsemble(3)
        traj3C = Trajectory([-0.5, -0.25, 0.1])
        s3C = Sample(replica=3, trajectory=traj3C, ensemble=ensC)
        self.testset[3] = s3C
        self.testset.consistency_check()
        assert len(self.testset) == 4

    def test_setitem_replace_replica(self):
        self.testset[2] = self.s2B_
        assert self.s2B not in self.testset
        assert self.s2B_ in self.testset
        assert self.testset[2] == self.s2B_
        # TODO add test that we replace at random

    def test_illegal_assign_ensemble(self):
        with pytest.raises(SampleKeyError):
            self.testset[self.ensA] = self.s2B_

    def test_illegal_assign_replica(self):
        with pytest.raises(SampleKeyError):
            self.testset[0] = self.s2B_

    def test_setitem_itemexists_ensemble(self):
        # exact sample is already there
        testset2 = SampleSet([self.s0A, self.s1A, self.s2B])
        # if we accidentally hit the statistical code, repeating 100 times
        # reduces odds of getting the same replacement each time
        for i in range(100):
            self.testset[self.ensA] = self.s0A
            self.testset.consistency_check()
            assert len(self.testset) == 3
            assert_items_equal(self.testset, testset2)

    def test_setitem_itemexists_replica(self):
        testset = SampleSet([self.s0A, self.s1A, self.s2B, self.s2B_])
        testset2 = SampleSet([self.s0A, self.s1A, self.s2B, self.s2B_])
        testset[2] = self.s2B
        testset.consistency_check()
        assert len(testset) == 4
        assert_items_equal(testset, testset2)

    def test_additem(self):
        testset2 = SampleSet([self.s0A, self.s1A, self.s2B, self.s2B_])
        self.testset.append(self.s2B_)
        assert self.s2B_ in self.testset
        assert len(self.testset) == 4
        self.testset.consistency_check()
        assert_items_equal(self.testset, testset2)

    def test_additem_itemexists(self):
        # exact sample is already there
        testset2 = SampleSet([self.s0A, self.s1A, self.s2B])
        self.testset.append(self.s2B)
        self.testset.consistency_check()
        assert len(self.testset) == 3
        assert_items_equal(self.testset, testset2)

    def test_del_sample(self):
        del self.testset[self.s2B]
        assert len(self.testset) == 2
        assert self.ensB not in list(self.testset.ensemble_dict.keys())
        assert self.ensA in list(self.testset.ensemble_dict.keys())
        assert 2 not in list(self.testset.replica_dict.keys())
        assert 0 in list(self.testset.replica_dict.keys())

    def test_del_ensemble(self):
        pytest.skip()

    def test_del_replica(self):
        pytest.skip()

    def test_apply_samples(self):
        pytest.skip()

    def test_extend(self):
        testset = SampleSet([self.s0A])
        testset.extend([self.s1A])
        assert len(testset) == 2
        assert self.s1A in testset
        testset.consistency_check()

        testset.extend(SampleSet([self.s2B]))
        assert len(testset) == 3
        assert self.s2B in testset
        testset.consistency_check()

        testset.extend(self.s2B_)
        assert len(testset) == 4
        assert self.s2B_ in testset
        testset.consistency_check()

    def test_replica_list(self):
        assert_items_equal(self.testset.replica_list(), [0, 1, 2])
        self.testset.append(self.s2B_)
        assert_items_equal(self.testset.replica_list(), [0, 1, 2])

    def test_ensemble_list(self):
        assert_same_items(self.testset.ensemble_list(), [self.ensA, self.ensB])

    def test_all_from_ensemble(self):
        assert_items_equal(self.testset.all_from_ensemble(self.ensA),
                           [self.s0A, self.s1A])
        assert_items_equal(self.testset.all_from_ensemble(self.ensB),
                           [self.s2B])

    def test_all_from_replica(self):
        assert_items_equal(self.testset.all_from_replica(2), [self.s2B])
        self.testset.append(self.s2B_)
        assert_items_equal(self.testset.all_from_replica(2), [self.s2B, self.s2B_])

    def test_consistency_fail_size_ensdict(self):
        del self.testset.ensemble_dict[self.ensB]
        with pytest.raises(AssertionError):
            self.testset.consistency_check()

    def test_consistency_fail_size_repdict(self):
        del self.testset.replica_dict[0]
        with pytest.raises(AssertionError):
            self.testset.consistency_check()

    def test_consistency_fail_sample_in_ensdict(self):
        pytest.skip()

    def test_consistency_fail_sample_in_repdict(self):
        pytest.skip()

    def test_consistency_fail_duplicate_samples(self):
        pytest.skip()

    def test_sanity(self):
        self.testset.sanity_check()

    def test_sanity_insane(self):
        traj0A = self.s0A.trajectory
        ensB = self.s2B.ensemble
        bad_samp = Sample(replica=0, trajectory=traj0A, ensemble=ensB)
        testset = SampleSet([bad_samp])
        with pytest.raises(AssertionError):
            testset.sanity_check()


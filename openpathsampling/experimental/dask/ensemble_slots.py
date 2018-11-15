import random
from openpathsampling.netcdfplus import StorableNamedObject
import numpy as np

import logging
logger = logging.getLogger(__name__)

from .serialize_wrapping import serialize_wrap, unwrap
from openpathsampling.experimental.storage.serialization_helpers import \
        get_uuid

def select_movers(scheme, n_steps):
    """Select movers from a scheme (skipping RandomChoice of move tree)

    Parameters
    ----------
    scheme : :class:`.MoveScheme`
        move scheme; must be one that has ``choice_probability`` or
        ``real_schoice_probability`` set
    n_step : int
        number of trial moves to generate

    Returns
    -------
    list of :class:`.PathMover`
        moves to perform, in order
    """
    movers, probs = zip(*list(scheme.real_choice_probability.items()))
    mover_uuids = {get_uuid(m): m for m in movers}
    mover_uuid_array = np.array([get_uuid(m) for m in movers])
    preselected_uuids = [np.random.choice(mover_uuid_array, p=probs)
                         for i in range(n_steps)]
    preselected_movers = [mover_uuids[u] for u in preselected_uuids]
    return preselected_movers

def serialized_ensemble_slots_from_sample_set(sample_set):
    ensemble_slots = ensemble_slots_from_sample_set(sample_set)
    return {get_uuid(ens): serialize_wrap(slot)
            for (ens, slot) in ensemble_slots.items()}

def select_samples_from_slots(s_slot_list):
    logger.info("Selecting samples")
    slots = [unwrap(s_slot) for s_slot in s_slot_list]
    samples = [slot.choose() for slot in slots]
    return serialize_wrap(samples)

def move_task(s_mover, s_samples):
    mover = unwrap(s_mover)
    samples = unwrap(s_samples)
    logger.info("Performing MC move " + mover.name)
    change = mover.move_core(samples)
    return serialize_wrap(change)

def update_slots(s_change, s_input_samples, s_slot):
    change = unwrap(s_change)
    input_samples = unwrap(s_input_samples)
    slot = unwrap(s_slot)
    logger.info("Updating the slots")
    slot.update(input_samples, change)
    return serialize_wrap(slot)

def unwrap_serialized_ensemble_slots(s_ensemble_slots):
    ensemble_slots = {}
    for ens_uuid, s_slot in s_ensemble_slots.items():
        slot = unwrap(s_slot)
        if get_uuid(slot.ensemble) != ens_uuid:
            raise RuntimeError("Unexpected ensemble")
        ensemble_slots[slot.ensemble] = slot
    return ensemble_slots

def ensemble_slots_from_sample_set(sample_set):
    """Create dict of ensemble slot objects from a sample set

    Parameters
    ----------
    sample_set : :class:`.SampleSet`
        sample set with all the ensembles

    Returns
    -------
    dict
        mapping :class:`.Ensemble` to :class:`.EnsembleSlot` based on the
        input sample set
    """
    # just a one-liner
    return {ens: EnsembleSlot(ens, sample_set.all_from_ensemble(ens))
            for ens in sample_set.ensembles}


class EnsembleSlot(StorableNamedObject):
    """
    Container object to hold samples associated with a specific ensemble.

    Parameters
    ----------
    ensemble : class:`.Ensemble`
        the ensemble for samples contained in this EnsembleSlot
    samples : iterable of :class:`.Sample`
        the samples which are associated with the given ensemble
    """
    def __init__(self, ensemble, samples):
        super(EnsembleSlot, self).__init__()
        self.ensemble = ensemble
        self.samples = samples
        if self.invalid():
            raise ValueError("Bad samples for EnsembleSlot with ensemble "
                             "{}: {} (ensembles: {})".format(
                                 repr(self.ensemble), self.samples,
                                 [s.ensemble for s in self.samples]
                             ))

    def select_samples(self, samples):
        """Select samples for this ensemble

        Parameters
        ----------
        samples : iterable of :class:`.Sample`
            all possible samples

        Returns
        -------
        list of :class:`.Sample`
            all samples from list with the ensemble for this slot
        """
        return [s for s in samples if s.ensemble == self.ensemble]

    def choose(self):
        """Select a random sample from this EnsembleSlot

        Returns
        -------
        :class:`.Sample`
            randomly selected sample from this EnsembleSlot
        """
        return random.choice(self.samples)


    def update(self, input_samples, change):
        """Update this sample based on input and output samples.

        Removes all input samples for this slot's ensemble; appends all
        output samples for this slot's ensemble.

        Parameters
        ----------
        input_samples : iterable of :class:`.Sample`
            samples that were used as input to a move (must already be
            present in this EnsembleSlot)
        change : :class:`.MoveChange`
            move change for the results
        """
        if not change.accepted:
            return self  # early skip out

        my_input = self.select_samples(input_samples)
        my_output = self.select_samples(change.results)

        for sample in my_input:
            self.samples.remove(sample)

        for sample in my_output:
            self.samples.append(sample)

        return self

    def invalid(self):
        """List any samples in self.samples with incorrect ensemble.

        Returns
        -------
        list
            samples that are not valid; a valid EnsembleSlot will return an
            empty list
        """
        return [s for s in self.samples if s.ensemble != self.ensemble]

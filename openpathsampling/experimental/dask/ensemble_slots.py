import random

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


class EnsembleSlot(object):
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


    def update(self, input_samples, output_samples):
        """Update this sample based on input and output samples.

        Removes all input samples for this slot's ensemble; appends all
        output samples for this slot's ensemble.

        Parameters
        ----------
        input_samples : iterable of :class:`.Sample`
            samples that were used as input to a move (must already be
            present in this EnsembleSlot)
        output_samples : iterable of :class:`.Sample`
            samples that came as the output of a move (after update, this
            slot will old these sample)
        """
        my_input = self.select_samples(input_samples)
        my_output = self.select_samples(output_samples)

        for sample in my_input:
            self.samples.remove(sample)

        for sample in my_output:
            self.samples.append(sample)

    def invalid(self):
        """List any samples in self.samples with incorrect ensemble.

        Returns
        -------
        list
            samples that are not valid; a valid EnsembleSlot will return an
            empty list
        """
        return [s for s in self.samples if s.ensemble != self.ensemble]

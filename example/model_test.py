""" Script to test the ML model. Takes a database of candidates from a GA
    search with target values set in atoms.info['key_value_pairs'][key] and
    returns the errors for a random test and training dataset.
"""
from __future__ import print_function

import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

from ase.ga.data import DataConnection
from atoml.data_setup import get_unique, get_train
from atoml.fingerprint_setup import normalize, return_fpv
from atoml.particle_fingerprint import ParticleFingerprintGenerator
from atoml.predict import FitnessPrediction


# Connect database generated by a GA search.
db = DataConnection('gadb.db')

# Get all relaxed candidates from the db file.
print('Getting candidates from the database')
all_cand = db.get_all_relaxed_candidates(use_extinct=False)

# Setup the test and training datasets.
testset = get_unique(candidates=all_cand, testsize=500, key='raw_score')
trainset = get_train(candidates=all_cand, trainsize=500,
                     taken_cand=testset['taken'], key='raw_score')

# Get the list of fingerprint vectors and normalize them.
print('Getting the fingerprint vectors')
fpv = ParticleFingerprintGenerator(get_nl=False, max_bonds=13)
test_fp = return_fpv(testset['candidates'], [fpv.bond_count_fpv])
train_fp = return_fpv(trainset['candidates'], [fpv.bond_count_fpv])
nfp = normalize(train=train_fp, test=test_fp)

# Set up the prediction routine.
krr = FitnessPrediction(ktype='gaussian',
                        kwidth=0.5,
                        regularization=0.001)

# Do the predictions.
cvm = krr.get_covariance(train_fp=nfp['train'])
cinv = np.linalg.inv(cvm)
print('Making the predictions')
pred = krr.get_predictions(train_fp=nfp['train'],
                           test_fp=nfp['test'],
                           cinv=cinv,
                           train_target=trainset['target'],
                           test_target=testset['target'],
                           get_validation_error=True,
                           get_training_error=True)

# Print the error associated with the predictions.
print('Training error:', pred['training_rmse']['average'])
print('Model error:', pred['validation_rmse']['average'])

pred['actual'] = testset['target']
index = [i for i in range(len(test_fp))]
df = pd.DataFrame(data=pred, index=index)
with sns.axes_style("white"):
    sns.regplot(x='actual', y='prediction', data=df)
plt.title('Validation RMSE: {0:.3f}'.format(
    pred['validation_rmse']['average']))
plt.show()
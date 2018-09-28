
# coding: utf-8

# In[1]:


from modelgym.models import CtBClassifier, LGBMClassifier
from modelgym.utils import XYCDataset
from modelgym.trainers import TpeTrainer
from modelgym.metrics import Accuracy
from modelgym.report import Report
from modelgym.utils import ModelSpace
from hyperopt import hp
import numpy as np
from sklearn.datasets import load_breast_cancer
from pathlib import Path
from wonderlandClient import ModelGymClient
from skopt.space import Integer, Categorical, Real
from modelgym.trainers import TpeTrainer, GPTrainer, RFTrainer, RandomTrainer
from modelgym.metrics import Accuracy, RocAuc, F1
import math


# In[2]:


client = ModelGymClient()
for param, val in client.config.items():
        print(param+":", val)


# In[3]:


from wonderlandClient import generate_data
tmp_file_path = Path("~/repo-storage-test/test/DATA/temp_data_145earu.csv").expanduser()
generate_data(tmp_file_path)


# In[4]:


data = load_breast_cancer()
y = np.array([data.target])
dataset = np.concatenate((data.data, y.T), axis=1)
n_features = len(data.data[0])
file = Path("~/repo-storage/test/DATA/temp_data_145earu.csv").expanduser()
np.savetxt(file, dataset,
           fmt='%.2f',
           header=','.join([str(x) for x in range(n_features)] + ['y']),
           delimiter=',')


# In[5]:


catboost_space = [Integer(low=100, high=500, name='iterations'),
 Integer(low=1, high=11, name='depth'),
 Real(low=math.exp(-5), high=1e-1, prior='log-uniform', name='learning_rate'),
 Real(low=0, high=1, prior='uniform', transform='identity', name='rsm'),
 Categorical(categories=('Newton', 'Gradient'), prior=None, name='leaf_estimation_method'),
 Integer(low=1, high=10, name='l2_leaf_reg'),
 Real(low=0, high=2, prior='uniform', transform='identity', name='bagging_temperature')]

model_ctb = ModelSpace(CtBClassifier,
                   space=catboost_space,
                   space_update=False)


# In[6]:


lgbm_space = [Real(low=math.exp(-7), high=1, prior='log-uniform', name='learning_rate'),
                 Integer(low=round(math.exp(1)), high=round(math.exp(7)), name='num_leaves'),
                 Real(low=0.5, high=1, name='feature_fraction'),
                 Real(low=0.5, high=1, name='bagging_fraction'),
                 Integer(low=1, high=round(math.exp(6)), name='min_data_in_leaf'),
                 Real(low=math.exp(-16), high=math.exp(5), prior='log-uniform', name='min_sum_hessian_in_leaf'),
                 Real(low=math.exp(-16), high=math.exp(2), prior='log-uniform', name='lambda_l1'),
                 Real(low=math.exp(-16), high=math.exp(2), prior='log-uniform', name='lambda_l2')]

model_lgbm = ModelSpace(LGBMClassifier,
                   space=lgbm_space,
                   space_update=False)
trainer = GPTrainer(model_ctb)


# In[7]:


best = trainer.crossval_optimize_params(RocAuc(), tmp_file_path, cv=3,
                                        opt_evals=1, metrics=[RocAuc()],
                                        verbose=False, workers=1, client=client, timeout=400)


# In[8]:


print(trainer.get_best_results())


# In[9]:


best_model = trainer.get_best_model()
best_model


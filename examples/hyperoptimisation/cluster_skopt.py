
# coding: utf-8

# In[1]:


from modelgym.models import CtBClassifier, LGBMClassifier
from modelgym.utils import XYCDataset
from modelgym.trainers import TpeTrainer
from modelgym.metrics import Accuracy
from modelgym.report import Report
from modelgym.utils import ModelSpace
from hyperopt import hp
from pathlib import Path
import numpy as np
from wonderlandClient import ModelGymClient
from skopt.space import Integer, Categorical, Real
from modelgym.trainers import TpeTrainer, GPTrainer, RFTrainer, RandomTrainer
from modelgym.metrics import Accuracy, RocAuc, F1
import math


# ## ModelGymClient 
# 
# ModelGymClient connects to the wonderland server during initialization. By default it uses config file "~/.wonder/config.yaml", but you can specify your own config.
# 

# In[2]:


client = ModelGymClient()
for param, val in client.config.items():
        print(param+":", val)


# ## Prepare data
# 
# Data have to be in format *.csv, a target column have to be called 'y'

# In[3]:


#standard sample
from sklearn.datasets import load_breast_cancer
import pandas as pd

data = load_breast_cancer()
y = pd.DataFrame(data=data.target, columns=["y"])                 
X = pd.DataFrame(data=data.data)
df = pd.concat([X, y], axis=1)


# ## Hyperparamaters range
# 
# You don't have to specify all parameters, but then you have to be sure that they have right default values

# In[19]:


#Catboost model space 
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


# In[20]:


#Lightgbm model space
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


# In[21]:


#trainer with optimization algorithm GP
trainer = GPTrainer(model_lgbm)


# ## Training
# 
# 

# In[22]:


best = trainer.crossval_optimize_params(opt_metric=RocAuc(),          #optimizing metrics 
                                        dataset=df,   #data or path to the data 
                                        cv=3, 
                                        opt_evals=5,        #number of optimization iterations
                                        metrics=[RocAuc()], #all calculated metrics
                                        workers=1,          #number of parallel jobs on the same iteration
                                        client=client,      #only for cluster optimization 
                                        timeout=400)        #timeout for 1 job 


# In[9]:


print(trainer.get_best_results())


# In[10]:


best_model = trainer.get_best_model()
best_model


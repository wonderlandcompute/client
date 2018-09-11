from wonderlandClient import (
    Job,
    new_client,
    ListJobsRequest
)

import base64
import os
import json
import shutil
import pandas as pd
import pickle
import numpy as np
from pathlib import Path
import modelgym.metrics
from modelgym.utils import XYCDataset
from hyperopt import STATUS_OK, STATUS_FAIL
from modelgym.utils.evaluation import crossval_fit_eval

MODEL_FILE = "model.pickle"

# TODO implement non-modegym learning.
# TODO combine MODEL_CLASSES and MODEL_PATH into one obj with the following struct model={'CtBClassifier':{model: 'CtBClassifier', path: 'path_to_exported_model.pickle'}}

MODEL_CLASSES = {
    'CtBClassifier': modelgym.models.CtBClassifier,
    'CtBRegressor': modelgym.models.CtBRegressor,
    'XGBClassifier': modelgym.models.XGBClassifier,
    'XGBRegressor': modelgym.models.XGBRegressor,
    'LGBMClassifier': modelgym.models.LGBMClassifier,
    'LGBMRegressor': modelgym.models.LGBMRegressor,
    'RFClassifier': modelgym.models.RFClassifier,
}

# TODO add non-modelgym metrics(need to rework modegym's function).
PREDEFINED_METRICS = {
    # classification metrics
    "accuracy": modelgym.metrics.Accuracy,
    "f1": modelgym.metrics.F1,
    "recall": modelgym.metrics.Recall,
    "log_loss": modelgym.metrics.Logloss,
    "precision": modelgym.metrics.Precision,
    "roc_auc": modelgym.metrics.RocAuc,

    # regression metrics
    # "mae": mean_absolute_error,
    "mse": modelgym.metrics.Mse,
    # "r2": r2_score,
}


def get_metric_function(metric):
    """Returns a predefined metric function object if metric corresponds to one,
    otherwise returns deserialized function object."""
    metric_function = PREDEFINED_METRICS.get(metric)

    if not metric_function:
        metric_function = pickle.loads(base64.b64decode(metric))

    return metric_function


def assess_model(metrics, model, train_objects, train_target):
    """Evaluates provided metrics for a trained model."""
    model_results = []
    prediction = model.predict(XYCDataset(train_objects))

    for metric in metrics:
        metric_function = get_metric_function(metric)
        score = metric_function(train_target, prediction)
        model_results.append(np.asscalar(score))

    return model_results


def cleanup_catboost():
    """Removes Catboost-generated files from current directory."""


    print("Removing Catboost-generated test/ and train/ folder !")
    shutil.rmtree('test', ignore_errors=True)
    shutil.rmtree('train', ignore_errors=True)

    os.remove('learn_error.tsv')
    os.remove('meta.tsv')
    os.remove('time_left.tsv')




def load_data(csv_path):
    """Loads train data from CSV file specified by its path. The target column must be 'y' """
    dataframe = pd.read_csv(csv_path)
    train_target = dataframe['y'].values
    train_objects = dataframe.drop(['y'], axis=1).values
    return train_target, train_objects



import time

SLEEP_TIME = 1 # seconds

stub = new_client()


def process_job(job):
    input = json.loads(job.input)
    data = input["data"]
    output_file = input["output_file"]
    models_info = input["models_info"]
    try:
        out_folder = Path(output_file).parent
        train_target, train_objects = load_data(data)
        dataset = XYCDataset(train_objects, train_target)
        with open(models_info, "rb") as f:
            models = json.load(f)
        cv = dataset.cv_split(models['cv'])
        model_objects = []

        for model in models['models']:

            if MODEL_CLASSES.get(model['type']):
                metrics = [PREDEFINED_METRICS.get(metric)() for metric in models['metrics']]
                result = crossval_fit_eval(model_type=MODEL_CLASSES[model['type']],
                                           params=model.get('params'),
                                           cv=cv,
                                           metrics=[PREDEFINED_METRICS.get(metric)() for metric in models['metrics']],
                                           verbose=None)

                res_model = MODEL_CLASSES[model['type']](params=model.get('params')).fit(dataset)
                with open(out_folder / MODEL_FILE, 'wb') as f:
                    pickle.dump(res_model, f)

            else:
                raise NotImplementedError('Classifier %s is not supported')

        result["status"] = STATUS_OK
        losses = [cv_result[metrics[-1].name]
                  for cv_result in result["metric_cv_results"]]
        result["loss_variance"] = np.std(losses)

        cleanup_catboost()

    except Exception as ex:
        result = {
            "status": STATUS_FAIL,
            "error": 1,
            "error_type": str(type(ex)),
            "error_description": str(ex),
        }


    ##!!
    job.output = str(float(job.input)**2)
    job.status = Job.COMPLETED
    stub.ModifyJob(job)
    return result


def main():
    while True:
        #time.sleep(5)
        pulled_jobs = stub.PullPendingJobs(ListJobsRequest(how_many=100))
        for job in pulled_jobs.jobs:
            process_job(job)
            print("Processed:\n{}".format(job))

if __name__ == '__main__':
    main()
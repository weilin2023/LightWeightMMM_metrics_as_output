# -*- coding: utf-8 -*-
"""LightWeightMMM_IG_Awareness.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1xcBah1ss8pKuZCyhTDHgaqJMk6bk3Yih
"""

!pip install --upgrade pip
!pip install --upgrade git+https://github.com/google/lightweight_mmm.git

import pandas as pd
from lightweight_mmm import preprocessing, lightweight_mmm, plot, optimize_media
import jax.numpy as jnp
from sklearn.metrics import mean_absolute_percentage_error
import jax.numpy as jnp
import numpyro
from lightweight_mmm import lightweight_mmm
from lightweight_mmm import optimize_media
from lightweight_mmm import plot
from lightweight_mmm import preprocessing
from lightweight_mmm import utils

from google.colab import drive
drive.mount('/content/drive')

ins_data = pd.read_csv("/content/instagram_processed_data.csv", usecols=["Impressions", "Reach", "Engaged Users", "Fan Growth", "Views", "Cost", "Consideration"])

ins_data.describe

ins_data.shape

ins_data = ins_data[:485]

media_data = ins_data[["Impressions"]].to_numpy()

cost_data = ins_data[["Cost"]].to_numpy()

sales_data = ins_data[["Consideration"]].to_numpy()

extra_features_data = ins_data[["Reach", "Engaged Users", "Fan Growth", "Views"]].to_numpy()

media_data

extra_features_data

media_data

media_data_train = media_data[:388]
media_data_test = media_data[388:]
target_data_train = sales_data[:388]
target_data_test = sales_data[388:]
cost_data_train = cost_data[:388].sum(axis=0)
#cost_data_train = cost_data_train.reshape(-1, 1)
cost_data_test = cost_data[388:].sum(axis=0)
#cost_data_test = cost_data_test.reshape(-1, 1)
extra_features_data_train = extra_features_data[:388]
extra_features_data_test = extra_features_data[388:]

cost_data_train

media_scaler = preprocessing.CustomScaler(divide_operation=jnp.mean)
target_scaler = preprocessing.CustomScaler(
    divide_operation=jnp.mean)
cost_scaler = preprocessing.CustomScaler(divide_operation=jnp.mean)
extra_features_scaler = preprocessing.CustomScaler(divide_operation=jnp.mean)

media_data_train_scaled = media_scaler.fit_transform(media_data_train)
target_train_scaled = target_scaler.fit_transform(target_data_train)
costs_scaled = cost_scaler.fit_transform(cost_data_train)
extra_features_scaled = extra_features_scaler.fit_transform(extra_features_data_train)

media_data_test_scaled = media_scaler.transform(media_data_test)
extra_features_test_scaled = extra_features_scaler.fit_transform(extra_features_data_test)

costs_scaled

media_data_train_scaled

number_warmup=1000
number_samples=1000

mmm = lightweight_mmm.LightweightMMM(model_name="carryover")



mmm.fit(
    media=media_data_train_scaled,
    media_prior=costs_scaled,
    target=target_train_scaled,
    extra_features=extra_features_scaled,
    number_warmup=number_warmup,
    number_samples=number_samples,
    degrees_seasonality=3,
    weekday_seasonality=True,
    seasonality_frequency=365,
    seed=1)

adstock_models = ["adstock", "hill_adstock", "carryover"]
degrees_season = [1,2,3]

#adstock_models = ["hill_adstock"]
#degrees_season = [1]


for model_name in adstock_models:
    for degrees in degrees_season:
        mmm = lightweight_mmm.LightweightMMM(model_name=model_name)
        mmm.fit(media=media_data_train_scaled,
                media_prior=costs_scaled,
                target=target_train_scaled,
                extra_features=extra_features_scaled,
                number_warmup=1000,
                number_samples=1000,
                number_chains=1,

                seed=1)

        prediction = mmm.predict(
        media=media_data_test_scaled,
        extra_features=extra_features_test_scaled,
        target_scaler=target_scaler,
        seed=1)
        p = prediction.mean(axis=0)

        mape = mean_absolute_percentage_error(target_data_test, p)
        print(f"model_name={model_name} degrees={degrees} MAPE={mape} samples={p[:3]}")
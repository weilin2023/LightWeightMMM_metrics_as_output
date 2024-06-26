# -*- coding: utf-8 -*-
"""GoogleLMMM.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1q31X3NcLJWd_LWXb3YBDOx0yM7lY-zB6

# Google LightweightMMM
https://github.com/google/lightweight_mmm
"""

# Commented out IPython magic to ensure Python compatibility.
# Install LightweightMMM
# %pip install lightweight_mmm

# run this if you run into issues
!pip install numpy==1.23.5

"""Note: make sure to restart runtime to use new versions of libraries"""

# Import jax.numpy and numpyro
import jax.numpy as jnp
import numpyro
numpyro.set_host_device_count(2)

# Import the relevant modules of the library
from lightweight_mmm import lightweight_mmm
from lightweight_mmm import optimize_media
from lightweight_mmm import plot
from lightweight_mmm import preprocessing
from lightweight_mmm import utils

"""## Simulating the data for modeling"""

# 104 weeks of training data + 13 weeks of test data
data_size = 104 + 13
n_media_channels = 3
n_extra_features = 1
n_geos = 2

# simulate the data
media_data, extra_features, target, costs = utils.simulate_dummy_data(
    data_size=data_size,
    n_media_channels=n_media_channels,
    n_extra_features=n_extra_features,
    geos=n_geos)

# 117 rows, 3 media channels, 2 geos
media_data.shape

# split train and test data
split_point = data_size - 13

# media data
media_data_train = media_data[:split_point, ...]
media_data_test = media_data[split_point:, ...]

# extra features
extra_features_train = extra_features[:split_point, ...]
extra_features_test = extra_features[split_point:, ...]

# target
target_train = target[:split_point]

# create the scalers
media_scaler = preprocessing.CustomScaler(divide_operation=jnp.mean)
extra_features_scaler = preprocessing.CustomScaler(divide_operation=jnp.mean)
target_scaler = preprocessing.CustomScaler(divide_operation=jnp.mean)
cost_scaler = preprocessing.CustomScaler(divide_operation=jnp.mean)

# scale the data
media_data_train = media_scaler.fit_transform(media_data_train)
extra_features_train = extra_features_scaler.fit_transform(extra_features_train)
target_train = target_scaler.fit_transform(target_train)
costs = cost_scaler.fit_transform(costs)

# training the model
mmm = lightweight_mmm.LightweightMMM(model_name="carryover")

mmm.fit(
    media=media_data_train,
    media_prior=costs,
    target=target_train,
    extra_features=extra_features_train,
    number_warmup=2000,
    number_samples=2000,
    number_chains=2)

# check the summary
# rhats should be < 1.1
mmm.print_summary()

# plot the posterior distributions of the media effects
channel_names = ['facebook', 'tiktok', 'google']
plot.plot_media_channel_posteriors(media_mix_model=mmm, channel_names=channel_names)

# check the model predicts training data
# passing the scaler gives unscaled results
plot.plot_model_fit(mmm, target_scaler=target_scaler)

# scale the test media data to make predictions on unseen data
media_data_test = media_scaler.transform(media_data_test)
extra_features_test = extra_features_scaler.transform(extra_features_test)
new_predictions = mmm.predict(media=media_data_test,
                              extra_features=extra_features_test)
new_predictions.shape

# plot the prediction vs actual charts
target_test = target_scaler.transform(target[split_point:])
plot.plot_out_of_sample_model_fit(out_of_sample_predictions=new_predictions,
                                 out_of_sample_target=target_test)

# estimate media effects with their respective credibility intervals
media_effect, roi_hat = mmm.get_posterior_metrics(target_scaler=target_scaler, cost_scaler=cost_scaler)

# plot media effects
plot.plot_bars_media_metrics(metric=media_effect, metric_name="Media Effect")

# plot media roi
plot.plot_bars_media_metrics(metric=roi_hat, metric_name="ROI hat")

# plot response curves for channels
plot.plot_response_curves(
    media_mix_model=mmm, target_scaler=target_scaler, media_scaler=media_scaler)

"""## Budget Optimization"""

# if you used impressions for media variables, this should be an array of average CPMs
# if you used spend then just put an array of 1s like we did here
prices = jnp.ones(mmm.n_media_channels)

# starting with the same average weekly budget and average values for extra features
n_time_periods = 10
budget = jnp.sum(media_data.mean(axis=0)) * n_time_periods
extra_features_forecast = extra_features_scaler.transform(extra_features_test)[:n_time_periods]

# run budget optimization
solution = optimize_media.find_optimal_budgets(
    n_time_periods=n_time_periods,
    media_mix_model=mmm,
    extra_features=extra_features_forecast,
    budget=budget,
    prices=prices,
    media_scaler=media_scaler,
    target_scaler=target_scaler,)

# both values should be almost equal
budget, jnp.sum(solution.x * prices)

for x in range(len(solution.x)):
    share = round(solution.x[x] / jnp.sum(solution.x * prices)*100, 2)
    print(channel_names[x], ": ", share, "%")


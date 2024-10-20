# -*- coding: utf-8 -*-
"""Time Series Anomaly Detection via Isolation Forest

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/#fileId=https%3A//storage.googleapis.com/kaggle-colab-exported-notebooks/time-series-anomaly-detection-via-isolation-forest-ce310f22-70bc-46ad-a706-78677aba27b1.ipynb%3FX-Goog-Algorithm%3DGOOG4-RSA-SHA256%26X-Goog-Credential%3Dgcp-kaggle-com%2540kaggle-161607.iam.gserviceaccount.com/20241020/auto/storage/goog4_request%26X-Goog-Date%3D20241020T112415Z%26X-Goog-Expires%3D259200%26X-Goog-SignedHeaders%3Dhost%26X-Goog-Signature%3Da45abb08934bd71c296f1debf1bd45eba838c87b1e75e5718ce96884e7e141cb78d6c3b1ec2d9e170ef37b060231bffb4b36b143a4be9abfc06b3b714df751ab052935078dc000d3d9ac977110ed8ae1c685ab0ff11addffdedda124c488cac8fcb02101c72ea01bf3416097038e2662a8bf9186e6b61ec80c3d75f95442ca3f807c3a45cbbbcd3c884ed3c88490fdfc46eace231929295bf7ef8f4c2b74429d62750fac23a977038f40c4508d72d186c34efaa3bc3fa335fe9ff834912ca997051051325642b3138077e8bf5f5e94dfdfa53d34efdaaf10b4d4233fc798bc14457866fd83b2129fbffaae58eb97f6db524041a4a7c8ff1c48b317014352cb5d

## **Importing Libraries**
"""

# Import code
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import holoviews as hv
from holoviews import opts
hv.extension('bokeh')
from bokeh.models import HoverTool
from IPython.display import HTML, display
from sklearn.impute import SimpleImputer
from sklearn.ensemble import IsolationForest
from sklearn import tree
import matplotlib.pyplot as plt

# Ignore warnings
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv('/kaggle/input/realKnownCause/realKnownCause/nyc_taxi.csv', parse_dates=['timestamp'])
df.head()

df.describe()

df.isnull().sum()

print('Start time: ', df['timestamp'].min())
print('End time: ', df['timestamp'].max())
print('Time difference: ', df['timestamp'].max()-df['timestamp'].min())

"""## **Data Visualization**
Let's now visualize the data to get a better understanding of it. We use resampling on the data to be able to see patterns of different frequencies.
"""

Hourly = hv.Curve(df.set_index('timestamp').resample('H').mean()).opts(
    opts.Curve(title="New York City Taxi Passenger Number Hourly", xlabel="", ylabel="Demand",
               width=700, height=300,tools=['hover'],show_grid=True))

Daily = hv.Curve(df.set_index('timestamp').resample('D').mean()).opts(
    opts.Curve(title="New York City Taxi Passenger Number Daily", xlabel="", ylabel="Demand",
               width=700, height=300,tools=['hover'],show_grid=True))

Weekly = hv.Curve(df.set_index('timestamp').resample('W').mean()).opts(
    opts.Curve(title="New York City Taxi Passenger Number Weekly", xlabel="Date", ylabel="Demand",
               width=700, height=300,tools=['hover'],show_grid=True))

(Hourly + Daily + Weekly).opts(shared_axes=False).cols(1)

"""## **Modeling**
We first split our data into train and test sets and we will then only use the train set for model training and algorithmic design decisions:
"""

# resample data and split data into train (~2/3 of data) and test (~1/3 of data) sets
df_model1 = df.set_index('timestamp').resample('D').mean().reset_index()
df_train_split1, df_test_split1 = np.split(df_model1, [int(0.65 *len(df_model1))])

df_train_split1.head()

df_test_split1.head()

df_visualize = df.set_index('timestamp').resample('D').mean()
df_visualize_train, _ = np.split(df_visualize, [int(0.65 *len(df_visualize))])

(hv.Distribution(df_visualize_train)
.opts(opts.Distribution(title="Value Distribution Training Data",
                        xlabel="Value",
                        ylabel="Density",
                        width=700, height=300,
                        show_grid=True)
     ))

# define model features
features = ['value']
df_train1 = df_train_split1[features]
df_test1 = df_test_split1[features]

model = IsolationForest(random_state=0, contamination=0.03)
model.fit(df_train1)
outliers_train = pd.Series(model.predict(df_train1)).apply(lambda x: 1 if x == -1 else 0).to_numpy()
anomaly_score_train = model.decision_function(df_train1)

# add prediction results to data frame for visualization purposes
df_train_split1 = df_train_split1.assign(outliers = outliers_train)
df_train_split1 = df_train_split1.assign(anomaly_score = anomaly_score_train)
df_train_split1.head()

df_train_split1['outliers'].sum()

# unfortunately the timestamps in these plots are broken and I was not able fix them within a reasonable amount of time
# thats why, we have to live with this for now...
tooltips = [
    ('Timestamp', '@timestamp'),
    ('Value', '@value'),
    ('Outliers', '@outliers'),
    ('Anomaly_Score', '@anomaly_score')
]
hover = HoverTool(tooltips=tooltips)
hv.Points(df_train_split1.query("outliers == 1")).opts(size=8, color='#ff0000') * hv.Points(df_train_split1.query("outliers == 0")).opts(size=8, color='#048c2d') * hv.Curve(df_train_split1).opts(opts.Curve(title="New York City Taxi Passenger Number - Anomalies and Normal Data", xlabel="", ylabel="Number Passengers" , height=300, responsive=True,tools=[hover,'box_select', 'lasso_select', 'tap'],show_grid=True))

frequencies, edges = np.histogram(anomaly_score_train, 50)
hv.Histogram((edges, frequencies)).opts(width=800, height=300,tools=['hover'], xlabel='Anomaly Score')

df_train_split1[df_train_split1.anomaly_score < 0]

"""We would like to cut away the anomalies on 2014-07-04 as well as 2014-07-05. For this, we can e.g. set the threshold to -0.017:"""

threshold=-0.017
hover = HoverTool(tooltips=tooltips)
hv.Points(df_train_split1.query("anomaly_score < {}".format(threshold))).opts(size=8, color='#ff0000') * hv.Curve(df_train_split1).opts(opts.Curve(title="New York City Taxi Passenger Number Anomalies", xlabel="", ylabel="Number Passengers" , height=300, responsive=True,tools=[hover,'box_select', 'lasso_select', 'tap'],show_grid=True))

"""That looks good :). Let's now try the model together with the finetuned threshold on the test data to see how good it generalizes to new data:"""

outliers_test = pd.Series(model.predict(df_test1)).apply(lambda x: 1 if x == -1 else 0).to_numpy()
anomaly_score_test = model.decision_function(df_test1)

# add prediction results to data for visualization purposes
df_test_split1 = df_test_split1.assign(outliers = outliers_test)
df_test_split1 = df_test_split1.assign(anomaly_score = anomaly_score_test)
df_test_split1.head()

"""Let's visualize the test data and highlight the detected anomalies in red:"""

hover = HoverTool(tooltips=tooltips)
hv.Points(df_test_split1.query("anomaly_score < {}".format(threshold))).opts(size=8, color='#ff0000') * hv.Curve(df_test_split1).opts(opts.Curve(title="New York City Taxi Passenger Number Anomalies", xlabel="", ylabel="Number Passengers" , height=300, responsive=True,tools=[hover,'box_select', 'lasso_select', 'tap'],show_grid=True))

fig, axes = plt.subplots(nrows = 1,ncols = 1,figsize = (4,4), dpi=800)
tree.plot_tree(model.estimators_[0],
               feature_names = df_train1.columns,
               max_depth=2,
               filled = True)
plt.show()
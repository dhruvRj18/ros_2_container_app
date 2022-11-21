# import libraries
from tabnanny import verbose
import pandas as pd
import numpy as np
from numpy.random import seed
import datetime
import tensorflow as tf
from keras.layers import Input, Dropout, Dense, LSTM, TimeDistributed, RepeatVector
from keras.models import Sequential
from keras import regularizers

import json
import json_numpy
from google.oauth2 import service_account
from google.cloud import storage
from google.cloud import bigquery
import db_dtypes
import base64

json_numpy.patch()
key_path = "key1.json"
credentials = service_account.Credentials.from_service_account_file(
    filename=key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"],
)





client = bigquery.Client(credentials=credentials, project=credentials.project_id,)
storage_client = storage.Client(credentials=credentials, project=credentials.project_id,)
bucket = storage_client.bucket("ros2")

query = """SELECT * FROM `neural-foundry-368217.ros.rosdata` WHERE shape IS NOT null
 LIMIT 1000"""

query_job = client.query(query)


list_a = []
for row in query_job:
  temp = dict()
  temp["__numpy__"] = row["__numpy__"]
  temp["dtype"] = row["dtype"]
  temp["shape"] = [(x if x < 128 else x - 256) for x in base64.b64decode(b'CgY=')]
  print(f"temp : {type(temp)}")
  temp = json.dumps(temp)
  payload = json.loads(temp)
  print(f"payload: {payload}")
  print(f"payload type: {type(payload)}")
 
  list_a.append(payload)

train_df= pd.DataFrame(columns=[])
for i in range(len(list_a)):
      temp_df = pd.DataFrame(list_a[i])
      train_df = train_df.append(temp_df)

# # train = pd.read_csv('UR5_position_good.csv', dtype=np.float32)
# # train = train[7500:35000]

X_train = train_df.to_numpy()
# reshape inputs for LSTM [samples, timesteps, features]
X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
print("Training data shape:", X_train.shape)

# define the autoencoder network model
def autoencoder_model(X):
  model = Sequential()
  model.add(LSTM(32, activation='relu', input_shape=(X.shape[1], X.shape[2]), return_sequences=True))
  model.add(LSTM(16, activation='relu', return_sequences=False))
  model.add(RepeatVector(X.shape[1]))
  model.add(LSTM(16, activation='relu', return_sequences=True))
  model.add(LSTM(32, activation='relu', return_sequences=True))
  model.add(TimeDistributed(Dense(X.shape[2])))
  return model

# create the autoencoder model
tf.random.set_seed(1234)
model = autoencoder_model(X_train)
model.compile(optimizer='adam', loss='mae')

# fit the model to the data
nb_epochs = 10
batch_size = 500
history = model.fit(X_train, X_train, epochs=nb_epochs, batch_size=batch_size, validation_split=0.05).history

x = datetime.datetime.now()
model_name = "Model " + x.strftime("%d-%b-%Y %X")
model_file = model_name+".h5"
model.save(model_file)
blob = bucket.blob(f"/models/{model_file}")
blob.upload_from_filename(model_file)

X_train_sample = X_train
X_train_pred = model.predict(X_train_sample)
loss_mae = np.mean(np.abs(X_train_pred-X_train_sample), axis = 1)
threshold = loss_mae.max()
anomaly = loss_mae > threshold
print("Anomalies: ", np.count_nonzero(anomaly))
print(threshold)
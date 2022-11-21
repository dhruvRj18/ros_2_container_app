
from google.cloud import pubsub_v1
import json

import tensorflow as tf
from keras.utils.vis_utils import plot_model
import threading
# import libraries
import pandas as pd
import numpy as np

import json_numpy
json_numpy.patch()

from google.cloud import storage
from google.oauth2 import service_account

key_path = "key1.json"
credentials = service_account.Credentials.from_service_account_file(
    filename=key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path("neural-foundry-368217","Ros-sub")

# Loading the autoencoder model
storage_client = storage.Client()
bucket = storage_client.bucket("ros2")
blob = bucket.blob("/models/Model 14-Nov-2022 19:17:07.h5")
model_file_temp = blob.download_to_filename("Model 14-Nov-2022 19:17:07.h5")
model = tf.keras.models.load_model("Model 14-Nov-2022 19:17:07.h5")
if model is not None:
    print("Got the model")
else:
    print("no model found")

def callback(message:pubsub_v1.subscriber.message.Message)-> None:
    #print(f"Rece {type(json.loads(message.data))}")
    if (message) is None:
        print("not received")
    in_sample =  json.loads(message.data)
    #print("before: ", in_sample.shape)
    in_sample = in_sample.reshape(in_sample.shape[0], 1, in_sample.shape[1])
    #print("after: ", in_sample.shape)
    out_sample = model.predict(in_sample, verbose=0)
    difference = in_sample - out_sample
    loss_mae = np.mean(np.abs(difference), axis = 1)
    anomaly = loss_mae > 0.021026134
    print("Anomalies: ", np.count_nonzero(anomaly))
    message.ack()



stream = subscriber.subscribe(subscription_path,callback=callback)
print(f"sub path - {subscription_path}")

with subscriber:
    stream.result()
    
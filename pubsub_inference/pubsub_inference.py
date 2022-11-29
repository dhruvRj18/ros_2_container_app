
from google.cloud import pubsub_v1
import json

import tensorflow as tf
from keras.utils.vis_utils import plot_model
import threading
# import libraries
import pandas as pd
import numpy as np

import json_numpy
from google.cloud import bigquery

json_numpy.patch()

from google.cloud import storage
from google.oauth2 import service_account

key_path = "key1.json"
credentials = service_account.Credentials.from_service_account_file(
    filename=key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

project_name = "nomadic-autumn-369912"

#BigQuery client
bigQ_client = bigquery.Client()
table_id = f"{project_name}.ros.grafana"


subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_name,"Ros-sub")

# Loading the autoencoder model
storage_client = storage.Client()
bucket = storage_client.bucket("ros2_data")
blob = bucket.blob("/models/Model 29-Nov-2022 21:14:29.h5")
model_file_temp = blob.download_to_filename("Model 29-Nov-2022 21:14:29.h5")
model = tf.keras.models.load_model("Model 29-Nov-2022 21:14:29.h5")
if model is not None:
    print("Got the model")
else:
    print("no model found")

def callback(message:pubsub_v1.subscriber.message.Message)-> None:
    #print(f"Rece {type(json.loads(message.data))}")
    if (message) is None:
        print("not received")
    in_sample =  json.loads(message.data)
    row=[]
    for i in in_sample:
        for a in range(len(i)):
            time = f"{message.publish_time}"
            time = time.replace(" ","T")
            row_ = {"should_lift":i[0],"elbow":i[1],"wrist1":i[2],"wrist2":i[3],"wrist3":i[4],"shoulder_pan":i[5],"timestamp":time}
            
    in_sample = in_sample.reshape(in_sample.shape[0], 1, in_sample.shape[1])
    out_sample = model.predict(in_sample, verbose=0)
    difference = in_sample - out_sample
    loss_mae = np.mean(np.abs(difference), axis = 1)
    anomaly = loss_mae > 0.021026134
    print(f"anomaly : {type(anomaly)}")
    if( np.count_nonzero(anomaly) >0):
        row_["anomaly"]=True
    else:
        row_["anomaly"]=False
    row.append(row_)
    errors = bigQ_client.insert_rows_json(table_id, row)  # Make an API request.
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))
    print("Anomalies: ", np.count_nonzero(anomaly))
    message.ack()



stream = subscriber.subscribe(subscription_path,callback=callback)
print(f"sub path - {subscription_path}")

with subscriber:
    stream.result()
    
import argparse
import json
import os
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from google.oauth2 import service_account
import base64

logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

key_path = "key1.json"
credentials = service_account.Credentials.from_service_account_file(
    filename=key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
project_name = "nomadic-autumn-369912"

INPUT_TOPIC= f"projects/{project_name}/topics/Ros2"
BIGQUERY_TABLE = f"{project_name}:ros.rosdata"
BIGQUERY_SCHEMA = "timestamp:TIMESTAMP,__numpy__:STRING,dtype:STRING,shape:BYTES"

class CustomParsing(beam.DoFn):
    """ Custom ParallelDo class to apply a custom transformation """

    def to_runner_api_parameter(self, unused_context):
        # Not very relevant, returns a URN (uniform resource name) and the payload
        return "beam:transforms:custom_parsing:custom_v0", None

    def process(self, element: bytes, timestamp=beam.DoFn.TimestampParam, window=beam.DoFn.WindowParam):
        """
        Simple processing function to parse the data and add a timestamp
        For additional params see:
        https://beam.apache.org/releases/pydoc/2.7.0/apache_beam.transforms.core.html#apache_beam.transforms.core.DoFn
        """
        parsed = json.loads(element.decode("utf-8"))
        parsed["timestamp"] = timestamp.to_rfc3339()
        print(f"par before: {parsed['shape']}")
        parsed["shape"] = base64.b64encode(bytes(x % 64 for x in parsed["shape"]))
        print(f"par after: {parsed['shape']}")
        yield parsed

def run():
    # Parsing arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_topic",
        help=f'Input PubSub topic of the form "projects/{project_name}/topics/Ros2."',
        default=INPUT_TOPIC,
    )
    parser.add_argument(
        "--output_table", help="Output BigQuery Table", default=BIGQUERY_TABLE
    )
    parser.add_argument(
        "--output_schema",
        help="Output BigQuery Schema in text format",
        default=BIGQUERY_SCHEMA,
    )
    known_args, pipeline_args = parser.parse_known_args()

    # Creating pipeline options
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(StandardOptions).streaming = True

    # Defining our pipeline and its steps
    with beam.Pipeline(options=pipeline_options) as p:
       lines= (
            p
            | "ReadFromPubSub" >> beam.io.gcp.pubsub.ReadFromPubSub(
                topic=known_args.input_topic
            )
            | "CustomParse" >> beam.ParDo(CustomParsing())
            | "WriteToBigQuery" >> beam.io.WriteToBigQuery(
                known_args.output_table,
                schema=known_args.output_schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                ignore_unknown_columns=True
            )
        )


if __name__ == "__main__":
    run()
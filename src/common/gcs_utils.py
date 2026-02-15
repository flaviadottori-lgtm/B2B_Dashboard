from google.cloud import storage
import os

def upload_to_gcs(bucket: str, blob_name: str, local_path: str):
    client = storage.Client()
    bucket_obj = client.bucket(bucket)
    blob = bucket_obj.blob(blob_name)
    blob.upload_from_filename(local_path)

def file_exists_gcs(bucket: str, blob_name: str) -> bool:
    client = storage.Client()
    bucket_obj = client.bucket(bucket)
    blob = bucket_obj.blob(blob_name)
    return blob.exists()

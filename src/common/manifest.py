import json
from google.cloud import storage

def write_manifest(bucket: str, blob_name: str, manifest: dict):
    client = storage.Client()
    bucket_obj = client.bucket(bucket)
    blob = bucket_obj.blob(blob_name)
    blob.upload_from_string(json.dumps(manifest, ensure_ascii=False, indent=2), content_type='application/json')

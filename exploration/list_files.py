import boto3
from botocore import UNSIGNED
from botocore.config import Config

s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))

# list what's actually in the works folder
result = s3.list_objects_v2(Bucket="openalex", Prefix="data/works/", Delimiter="/")

for obj in result.get("CommonPrefixes", []):
    print(obj["Prefix"])


result2 = s3.list_objects_v2(Bucket="openalex", Prefix="data/works/updated_date=2016-06-24/")

for obj in result2.get("Contents", []):
    print(obj["Key"])
import os
import threading
import time
import boto3

from boto.s3.connection import S3Connection
from boto.cloudfront.distribution import Distribution

from flask import Blueprint

blueprint = Blueprint("s3", __name__)

@blueprint.record_once
def record(setup_state):
    app = setup_state.app

    blueprint.s3_access_key = app.config["AWS_ASSET_ACCESS_KEY"]
    blueprint.s3_secret_key = app.config["AWS_ASSET_SECRET_KEY"]
    with open(os.path.join(os.path.dirname(app.root_path), "pk-APKAIQD6FQE7UOMX3R2Q.pem")) as private_key_file:
        blueprint.cloudfront_private_key = private_key_file.read()
    
    blueprint.dynamo_client = boto3.client('dynamodb',
        aws_access_key_id = app.config["AWS_ASSET_ACCESS_KEY"],
        aws_secret_access_key = app.config["AWS_ASSET_SECRET_KEY"],
        region_name = 'us-east-1')

def sign(bucket, path, https, expiry=631138519):
    c = S3Connection(blueprint.s3_access_key, blueprint.s3_secret_key)
    return c.generate_url(
        expires_in=long(expiry),
        method='GET',
        bucket=bucket,
        key=path,
        query_auth=True,
        force_http=(not https)
    )

def prepopulate_cloudfront_url_cache():
    c = S3Connection(blueprint.s3_access_key, blueprint.s3_secret_key)
    bucket = c.get_bucket('eastern-toys-assets')
    result_set = bucket.list()
    for result in result_set:
        asset_path = result.name
        if not asset_path.endswith('/'):
            cloudfront_sign(str(asset_path))
    print " * Done prepopulating Cloudfront URL cache"

def cloudfront_sign(asset_path, expiry=1485864000):
    dynamo_item = blueprint.dynamo_client.get_item(
        TableName = 'cloudfront_signed',
        Key = {
            'asset_path': {
                'S': asset_path + ',' + str(expiry)
            }
        }
    )

    cached_url = dynamo_item.get('Item', {}).get('signed_url', {}).get('S',None)
    if cached_url:
        return cached_url

    dist = Distribution(domain_name='d1gy1csjh89rhq.cloudfront.net')
    key_pair_id = 'APKAIQD6FQE7UOMX3R2Q'

    http_resource = 'https://assets.monsters-et-manus.com/' + asset_path
    http_signed_url = dist.create_signed_url(http_resource, key_pair_id, expiry, private_key_string=blueprint.cloudfront_private_key)
    
    blueprint.dynamo_client.put_item(
        TableName = 'cloudfront_signed',
        Item = {
            'asset_path': {
                'S': asset_path + ',' + str(expiry)
            },
            'signed_url': {
                'S': http_signed_url
            }
        }
    )

    return http_signed_url

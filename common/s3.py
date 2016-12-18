import optparse
import os
import sys
import time

from boto.s3.connection import S3Connection
from boto.cloudfront.distribution import Distribution

from flask import g

from werkzeug.contrib.cache import SimpleCache

def sign(bucket, path, access_key, secret_key, https, expiry=631138519):
    c = S3Connection(access_key, secret_key)
    return c.generate_url(
        expires_in=long(expiry),
        method='GET',
        bucket=bucket,
        key=path,
        query_auth=True,
        force_http=(not https)
    )

CLOUDFRONT_URL_CACHE = SimpleCache()

def cloudfront_sign(app, access_key, secret_key, asset_path, expiry=1485864000):
    cache_key = (access_key, secret_key, asset_path, expiry)
    cached_url = CLOUDFRONT_URL_CACHE.get(cache_key)
    if cached_url:
        return cached_url

    if 'cloudfront_private_key' not in g:
        with open(os.path.join(os.path.dirname(app.root_path), "pk-APKAIQD6FQE7UOMX3R2Q.pem")) as private_key_file:
            g.cloudfront_private_key = private_key_file.read()

    dist = Distribution(domain_name='d1gy1csjh89rhq.cloudfront.net')
    key_pair_id = 'APKAIQD6FQE7UOMX3R2Q'

    http_resource = 'https://assets.monsters-et-manus.com/' + asset_path
    http_signed_url = dist.create_signed_url(http_resource, key_pair_id, expiry, private_key_string=g.cloudfront_private_key)

    CLOUDFRONT_URL_CACHE.set(cache_key, http_signed_url, timeout=int(expiry - time.time()))

    return http_signed_url

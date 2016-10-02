import optparse
import sys

from boto.s3.connection import S3Connection

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
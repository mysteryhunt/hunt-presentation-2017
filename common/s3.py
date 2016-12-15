import optparse
import os
import sys

from boto.s3.connection import S3Connection
from boto.cloudfront.distribution import Distribution

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
    
def cloudfront_sign(app, access_key, secret_key, asset_path, expiry=1485864000):
  dist = Distribution(domain_name='d1gy1csjh89rhq.cloudfront.net')
  key_pair_id = 'APKAIQD6FQE7UOMX3R2Q'
  priv_key_file = os.path.join(os.path.dirname(app.root_path), "pk-APKAIQD6FQE7UOMX3R2Q.pem")
  
  http_resource = 'https://assets.monsters-et-manus.com/' + asset_path
  http_signed_url = dist.create_signed_url(http_resource, key_pair_id, expiry, private_key_file=priv_key_file)
  return http_signed_url

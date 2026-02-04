#!/bin/sh

cd
export AWS_DEFAULT_REGION=gra
export AWS_ENDPOINT_URL=https://s3.gra.io.cloud.ovh.net/
export AWS_ACCESS_KEY_ID=`cat /run/ds-pods-secrets/s3_tests_access_key_id`
export AWS_SECRET_ACCESS_KEY=`cat /run/ds-pods-secrets/s3_tests_secret_access_key`

exec "$@"
This is otvl_general

## releases

- 0.7: Estore grpc
- 0.7.1: adding protobuf dependency
- 0.7.2: adding cache or stream
- 0.7.3: adding cache or stream with hashes
- 0.8: reading entities in DB and Estore
- 0.8.1: new options for reading entities
- 0.8.2: fixed omitted keys in grpc api
- 0.8.6: fixed threading issue
- 0.9: added read on session
- 0.10: added flows
- 0.11: changed stfl interfaces for reliable concurrency
- 0.12: testing build + docker

## dev

[mypi stdlib builtins](https://github.com/python/typeshed/blob/main/stdlib/builtins.pyi)
[pipenv security](https://pipenv.pypa.io/en/latest/security.html)


## docker

docker build -t t-ctr.otvl.org/workflow-task:0.1-dev .
docker push t-ctr.otvl.org/workflow-task:0.1-dev
docker run -it --rm t-ctr.otvl.org/workflow-task:0.1 /venv/bin/python -m otvl_general.utils.estore_server --db-server xxx -d yy -b bkbk
kubectl run -i estore --rm --image=t-ctr.otvl.org/workflow-task:0.1-dev -- /venv/bin/python -m otvl_general.utils.estore_server --db-server xxx -d yy -b bkbk

## Awf wma

* Daemon stfl + estore
  * python -m otvl_general.cmd.sfe_svr -p 8181 --db-server t-db-pgs -d estore_c01_main_test --s3-profile otvl-tests -b otvl-tests
* Init estore conditional
  * ESTORE_DROP_DB=FaLse python -m otvl_general.cmd.sfe_init_db --host sfe-svr-host -p 8181
* Fetch wma pams list and push to newly created queue
* 4 tasks to parse each pam archive and load content in the estore , push stats in queue
* Reduce task read stats queue

Mode check, list missing or corrupted in estore specific category.

### Env

AWS_DEFAULT_REGION=gra
AWS_ENDPOINT_URL=https://s3.gra.io.cloud.ovh.net/
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI

ESTORE_DROP_DB=FaLse

{{steps.sfe_svr.ip}}

### Todo

* Wma utils in new pypi otvl_wma
* Local testing
* Distributed testing with fast processing feature flag

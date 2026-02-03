docker build -t t-ctr.otvl.org/ddpestores:0.1 . -f docker/Dockerfile.ddpestores
docker run -it --rm t-ctr.otvl.org/ddpestores:0.1.3 /venv/bin/python -m ddpestores.estore_server

docker build -t t-ctr.otvl.org/workflow-task:0.1-dev .
docker push t-ctr.otvl.org/workflow-task:0.1-dev
docker run -it --rm t-ctr.otvl.org/workflow-task:0.1 /venv/bin/python -m otvl_general.utils.estore_server --db-server xxx -d yy -b bkbk
kubectl run -i estore --rm --image=t-ctr.otvl.org/workflow-task:0.1-dev -- /venv/bin/python -m otvl_general.utils.estore_server --db-server xxx -d yy -b bkbk

docker push t-ctr.otvl.org/otvl-pg-cli:0.8

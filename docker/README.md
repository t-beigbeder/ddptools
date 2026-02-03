docker build -t t-ctr.otvl.org/ddpestores:0.1 . -f docker/Dockerfile.ddpestores
docker run -it --rm t-ctr.otvl.org/ddpestores:0.1.4 /venv/bin/python -m ddpestores.estore_server

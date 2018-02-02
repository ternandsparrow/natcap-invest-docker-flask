# natcap-invest-docker-flask

HTTP wrapper around NatCap's InVEST product (https://pypi.python.org/pypi/natcap.invest) using Flask.

Specifically we've focused on the pollination model at this stage, because that's what we need.

## Running it

This is a docker image. The contained process runs in the foreground so we'll run it without detatching so we can control+c to kill it. We'll also use the `--rm` flag so the container is removed when we exit. Use the following command to run:
```bash
docker run \
  --rm \
  -it \
  -p 5000:5000 \
  tomsaleeba/natcap-invest-docker-flask
```

Then you can use it like this:
```bash
curl localhost:5000/ # this will get the available links, just a healthcheck really
curl localhost:5000/pollination # this will execute the pollination model
```

Alternatively, you can go to http://localhost:5000/tester to use a web UI to interact with the service.

## Building it

You can build this project with the following command:
```bash
cd natcap-invest-docker-flask/
./docker-build.sh
```

Then you can push to DockerHub with:
```bash
docker push tomsaleeba/natcap-invest-docker-flask
```

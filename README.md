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

## Faster development iterations

There are 3 ways to run this project:
 1. build the docker image and run it
 1. have a virtualenv (or not, if you're crazy) with all the dependencies installed and run full implementations directly on your machine
 1. use `tests/stub_runner.py`

The first two methods run a "real" system that will actually call natcap's code. The third method runs flask with a stub natcap implementation behind it so you can quickly iterate on changes to the HTTP related code without running the slow backend code or building a docker image (also slow).

## TODO

 1. add something to clean up old workspace files
 1. make farm vector file a param to /pollination
 1. make landcover raster file a param to /pollination

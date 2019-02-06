# natcap-invest-docker-flask

HTTP wrapper around [NatCap's InVEST](https://pypi.python.org/pypi/natcap.invest) using Flask.

Specifically we've focused on the pollination model at this stage, because that's what we need.

Getting an idea of the performance and required resources is useful. We'll run the Docker container on my
laptop with a 2nd gen Core i7, plenty of RAM and using a secondary SSD. We're using the out-of-the-box demo
farm vector and the default farm padding of 3km which gives us a raster size of approximately 13x12 km. We see
the following figures:

years simulated | run times for 3 runs (seconds) | disk used
--- | --- | ---
1 | 2.5-2.6 | 125MB
3 | 3.5-3.6 | 249MB
10 | 7.4-8.0 | 683MB
30 | 20.2-20.7 | 1.9GB

All years are run in parallel with one process per year so the CPUs are completely used once the number of
years equals the number of cores (8 on my machine). Even though the NatCap model writes a lot of intermediate
`tif` files as part of the processing, a faster disk (like ramdisk) doesn't improve performance because we're
CPU-bound. Also note that all the files produced from InVEST are removed after a run, however you *need* the
disk space available to perform the run.

## Version numbers
We tag the Git and DockerHub repos with a version scheme: `{our version}_{InVEST version}`, for example
`1.0.0_3.4.2`.

## Running it

This is a docker image. The contained process runs in the foreground so we'll run it without detatching so we
can control+c to kill it. We'll also use the `--rm` flag so the container is removed when we exit. Use the
following command to run:
```bash
docker run \
  --rm \
  -it \
  -p 5000:5000 \
  ternandsparrow/natcap-invest-docker-flask:1.0.0_3.4.2 # check DockerHub for the latest tag
```

You can configure aspects of the model execution by providing [env parameters](https://docs.docker.com/engine/reference/run/#env-environment-variables) to the `docker run` command.

| key |value type | default value | description |
| --- |---------- | ------------- | ----------- |
|`FARM_PADDING_METRES`|integer|3000| padding, in metres, used when cropping the raster around the farm vector. Smaller values mean faster runs but if you go too small, it'll negatively affect results as there's not enough raster around the farm to calculate wild pollination values. |
|`PURGE_WORKSPACE`|0 or 1|1 (True)|controls if the temporary workspace on disk is completely purged after each run. Each request is stateless/self-contained so the only reason to keep the workspace is for debugging reasons.|

Then you can use it like this:
```bash
curl localhost:5000/ # get available links, just a healthcheck really
cd natcap-invest-docker-flask/natcap_invest_docker_flask/static/
# execute the pollination model:
echo '{"farm":'`cat example-farm-vector.json`',"reveg":'`cat example-reveg-vector.json`'}' \
  | curl \
  -H 'Accept: application/json' \
  -H 'Content-type: application/json' \
  -d @- \
  'http://localhost:5000/pollination?years=2'
```

Alternatively, you can go to http://localhost:5000/tester to use a web UI to interact with the service.

## Building it

You can build this project with the following command:
```bash
cd natcap-invest-docker-flask/
./docker-build.sh
```

## Affect of farm vector inputs on the outputs
There are quite a few parameters in the attribute table of the farm vector that you supply, as a user. To get
a feel for how they affect the output, have a look at
[spectrum/value_spectrum_0.33step.csv](./spectrum/value_spectrum_0.33step.csv). If you want to produce your
own spectrum file, see the `spectrum/value_spectrum.py` program.

## Faster development iterations

There are 3 ways to run this project:
 1. build the docker image and run it
 1. have a virtualenv (or not, if you're crazy) with all the dependencies installed and run full implementations directly on your machine
 1. use `tests/stub_runner.py`

The first two methods run a "real" system that will actually call natcap's code. The third method runs flask
with a stub natcap implementation behind it so you can quickly iterate on changes to the HTTP related code
without running the slow backend code or building a docker image (also slow).

## TODO
 - add 'crop type' selector logic to pick the correct guild table based on 'crop_type' field in farm vector, validate value too
 - add validation for only one crop, can have multiple polys though
 - change demo to only have one crop type

# natcap-invest-docker-flask

HTTP wrapper around [NatCap's
InVEST](https://pypi.python.org/pypi/natcap.invest) using Flask. Specifically it
builds on [this](https://github.com/ternandsparrow/natcap-invest-docker) base
image. The landcover raster comes from
[here](https://github.com/ternandsparrow/landuse-raster-south-australia).

Specifically we've focused on the pollination model at this stage, because
that's what we need.

## What data do we feed into the model?
The InVEST model lists its [data needs
here](http://data.naturalcapitalproject.org/nightly-build/invest-users-guide/html/croppollination.html#data-needs).
You can find the "landcover biophysical tables", "guild tables" and "farm
attributes" that we feed into the model in the `docker/` directory of this
repository. Each crop type that we support has its own tables. The user is asked
to supply *only* the vector for their farm. The attributes for the farm are
taken from CSVs files on the server, we don't get those values from the user.

Modelling the introduction of varroa mite is achieved by using separate "guild
tables" that adjust the `nesting_suitability_` and `foraging_activity_` values
for the Apis genus.  We found that this was the best way to model a reduction in
Apis. Adjusting the `relative_abundance` value seemed to have the opposite of
the desired effect; rather than reducing Apis abundance, it seemed to increase
the other guilds.

## Performance

Getting an idea of the performance and required resources is useful. Run time
and disk space usage is primarily affected by the size of the farm vector.
Larger farms mean larger rasters and these take longer to process. The number of
years makes less difference because we only run for a subset of years so more
years doesn't mean more simulations.

Running on a 4th gen 3.6ghz Intel Core i7, with 1.5km farm padding, we see the
following kinds of numbers:

years simulated | farm size (ha) | run times for 3 runs (seconds) | disk used (MB)
--- | --- | --- | ---
3 | 50 | 3 | 24
3 | 5040 | 5 | 98
15 | 50 | 4 | 44
15 | 5040 | 7 | 182
25 | 50 | 4 | 48
25 | 5040 | 7 | 196

All simulations are run in parallel with one process per year so the CPUs are
completely used once the number of simulations equals the number of cores . As
we only run for a subset of all years, the number of simulations is usually 7-9.
Even though the NatCap model writes a lot of intermediate `tif` files as part of
the processing, a faster disk (like ramdisk) doesn't improve performance because
we're CPU-bound. Also note that all the files produced from InVEST are removed
after a run, however you *need* the disk space available to perform the run.

## Version numbers
We tag the Git and DockerHub repos with a version scheme: `{our version}_{InVEST
version}`, for example `1.2.2_3.8.9`.

## Running it

This is a docker image and it's built on DockerHub, so to run on a host all you
need is to grab the runner script and docker-compose file(s) from this repo (you
don't need to whole repo) and a host with docker installed. It will pull the
image when you run the script.

  1. get the runner script
      ```bash
      git clone https://github.com/ternandsparrow/natcap-invest-docker-flask
      cd natcap-invest-docker-flask
      cp run-container.sh.example run-container.sh
      # OR, pull direct from GitHub
      wget https://github.com/ternandsparrow/natcap-invest-docker-flask/raw/master/{run-container.sh.example,docker-compose.yml,docker-compose.local-dev.yml}
      mv run-container.sh.example run-container.sh
      ```
  1. make it executable
      ```bash
      chmod +x run-container.sh
      ```
  1. make any required edits
      ```bash
      vim run-container.sh # select an image tag and/or enable production mode
      ```
  1. run it
      ```bash
      ./run-container.sh
      ```

You can configure aspects of the model execution by providing [env
parameters](https://docs.docker.com/engine/reference/run/#env-environment-variables)
to the `docker run` command.

| key |value type | default value | description |
| --- |---------- | ------------- | ----------- |
|`FARM_PADDING_METRES`|integer|1500| padding, in metres, used when cropping the raster around the farm vector. Smaller values mean faster runs. Be sure to make it larger than the max `alpha` value in your guild tables. |
|`PURGE_WORKSPACE`|0 or 1|1 (True)|controls if the temporary workspace on disk is completely purged after each run. Each request is stateless/self-contained so the only reason to keep the workspace is for debugging reasons.|

Then you can make a call to the server like this:
```bash
curl localhost:5000/ # get available links, just a healthcheck really
# change to a dir where we can use the example payloads
cd natcap-invest-docker-flask/natcap_invest_docker_flask/static/
# execute the pollination model:
echo '{"crop_type":"apple","years":3,"farm":'`cat example-farm-vector.json`',"reveg":'`cat example-reveg-vector.json`'}' \
  | curl \
  -H 'Accept: application/json' \
  -H 'Content-type: application/json' \
  -d @- \
  'http://localhost:5000/pollination'
```

Alternatively, you can go to http://localhost:5000/tester to use a web UI to
interact with the service.

## Code style
We're using [yapf](https://github.com/google/yapf) to format the code in this
repo.


## Building it

You can build this project with the following command:
```bash
docker build -t ternandsparrow/natcap-invest-docker-flask:dev .
```

The docker build uses a multi-stage approach. This means subsequent builds will
be fast because they'll use the build cache. The last stage of the build, which
always runs, copys the code over to the container. If you make changes to the
dependencies, you'll need to bust the cache and rebuild all stages. Do this
with:
```bash
docker build --no-cache -t ternandsparrow/natcap-invest-docker-flask:dev .
```

## Affect of farm vector inputs on the outputs
There are quite a few parameters in the attribute table of the farm vector that
you supply, as a user. To get a feel for how they affect the output, have a look
at
[spectrum/value_spectrum_0.33step.csv](./spectrum/value_spectrum_0.33step.csv).
If you want to produce your own spectrum file, see the
`spectrum/value_spectrum.py` program.

## Faster development iterations

There are 4 ways to run this project:
 1. build the docker image and run it
 1. (preferred) use the built docker container but mount your workspace as a
    volume so it sees the changes *live* (the `LOCAL_DEV` env var will trigger
    the volume mounting)
      ```bash
      # edit your run-container.sh file that you created by following the
      # instructions under "Running it" so the docker tag matches what you used
      # to build the image
      LOCAL_DEV=1 ./run-container.sh
      ```
 1. have a virtualenv (or not, if you're crazy) with all the dependencies
    installed and run full implementations directly on your machine
 1. use `tests/stub_runner.py` (FIXME need to also install GDAL, natcap, etc
    which aren't explicit requirements - assumed to come from base Docker image)

The first three methods run a "real" system that will actually call natcap's
code. The fourth method runs flask with a stub natcap implementation behind it
so you can quickly iterate on changes to the HTTP related code without running
the slow backend code or building a docker image (also slow).

## Running unit tests
The code base is currently only lightly tested and as such doesn't require all
the dependencies to be able to run the tests. This means you can run tests by:

  1. create a virtualenv
      ```bash
      virtualenv -p python3 .venv
      . .venv/bin/activate
      ```
  1. install the dependencies for this project (doesn't include the underlying
     dependencies like natcap and GDAL)
      ```bash
      pip install -r requirements.txt -r requirements-test.txt
      ```
  1. run the tests
      ```bash
      nose2
      ```

In the future when we test more of the code, and we need natcap, etc to be
present, we'll probably run the tests inside a docker container.

## Benchmarking
The NatCap InVEST software is CPU bound so more CPUs means fasters runs. To see
how a machine performs with varying lengths of simulation (years):

  1. start the server (serving at localhost:5000): `./run-container.sh`
  1. make sure you have the python requests library available: `pip install requests`
  1. run the benchmark script: `python tests/benchmark.py`
  1. the output will be a CSV (written to stdout) that you can chart as you like

## Code style
The code for this repo should pass a `./scripts/flake8.sh` run. To make it
easier to achieve compliance, you can run the `./scripts/lint-fix.sh` script to
auto-fix a lot of whitespace related lint errors.

FROM ternandsparrow/natcap-invest-docker:1.1.1_3.8.0 AS withDeps

WORKDIR /app/
ADD docker/stage1/setup.sh docker/stage1/setup.sh
ADD requirements.txt .
RUN /bin/bash docker/stage1/setup.sh


FROM withDeps
ADD . /app/
ENTRYPOINT [ "/bin/bash", "docker/run.sh" ]

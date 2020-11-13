FROM ternandsparrow/natcap-invest-docker:1.1.4_3.8.9 AS withDeps

WORKDIR /app/
ADD docker/setup.sh docker/setup.sh
ADD requirements.txt .
RUN /bin/bash docker/setup.sh


FROM withDeps
ADD . /app/
RUN set -eux; \
	groupadd -r nidfuser --gid=999; \
	useradd -r -g nidfuser --uid=999 --home-dir=/workspace --shell=/bin/bash nidfuser; \
	chown -R nidfuser:nidfuser /workspace
USER nidfuser:nidfuser
ENTRYPOINT [ "/bin/bash", "docker/run.sh" ]

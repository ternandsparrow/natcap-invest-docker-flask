FROM tomsaleeba/natcap-invest-docker:3.4.2-pollination

RUN mkdir /invest_http
ADD files/ /invest_http
WORKDIR /invest_http
RUN /bin/bash setup.sh
ENTRYPOINT [ "/bin/bash", "run.sh" ]

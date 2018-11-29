FROM python:3.7-alpine3.7

MAINTAINER Rob Jahn <rob.jahn@dynatrace.com>

ENV DT_API_TOKEN=""
ENV DT_TENANT_HOST=""


RUN apk add --update \
    jq \
    git

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

RUN git clone https://github.com/Dynatrace/dynatrace-cli.git

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY app.py /app

ENTRYPOINT [ "python" ]

CMD [ "app.py" ]
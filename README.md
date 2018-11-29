# Overview

This is a web REST application that serves as a wrapper to the Python bases [Dynatrace CLI](https://github.com/Dynatrace/dynatrace-cli)

The application is writen in Python3 and uses [Flask](http://flask.pocoo.org) and the [Flask Rest Plus extention](https://flask-restplus.readthedocs.io)

Docker build image makes an image called ```dtcli-webproxy```
1. use python:3.7-alpine3.7 base image
1. install git
1. clone https://github.com/Dynatrace/dynatrace-cli.git 
1. run pip to install python dependencies
 
# Build

This repo is being automatically build on master branch using:
[![Build Status](https://dev.azure.com/robjahn/unbreakablepipeline/_apis/build/status/robertjahn.dtcli-webproxy)](https://dev.azure.com/robjahn/unbreakablepipeline/_build/latest?definitionId=5)

Two scripts provided to help with this, but modify for your target
1. docker_build.bat
1. docker_push.bat

# Start Application

Start application
```
docker run --rm -p 5000:5000 --name cli-app -e DT_TENANT_HOST=<YOUR URL> -e DT_API_TOKEN=<YOUR TOKEN> dtcli-webproxy
```

If needed run these commands to cleanup
```
docker stop dtcli-webproxy
docker rm dtcli-webproxy
docker rmi dtcli-webproxy
```

# Usage

See the swagger Spec at [http://localhost:5000](http://localhost:5000)


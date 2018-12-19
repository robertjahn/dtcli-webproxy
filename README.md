# Overview

This is a web REST application that serves as a proxy to the Python 
[Dynatrace CLI](https://github.com/Dynatrace/dynatrace-cli)

It is an alternate solution for the Dynatrace web proxy required to support the pipeline quality gate of the Azure functional 
application within [Unbreakable Pipeline Azure Demo](https://github.com/dynatrace-innovationlab/unbreakable-pipeline-vsts#dynatrace-unbreakable-pipeline-proxy)

The application and the Python CLI requires Python3 and uses [Flask](http://flask.pocoo.org) and the 
[Flask Rest Plus extention](https://flask-restplus.readthedocs.io)

The application has a single end point that is used to process the "monspec" action of the CLI

To process the request, POST to this endpoint:
```
http://localhost:5000/api/DTCLIProxy/MonspecPullRequest
```

The output of this call is the output of the Python CLI monspec pullcompare command.  

The parameters are passed in the BODY of the POST request. See lower in the README for more details on the structure.
```
python dtcli.py monspec pullcompare MONSPEC_FILE PIPELINEINFO_FILE  SERVICE_TO_COMPARE COMPARE_WINDOW
```

Note that this project is setup to work with my personal docker hub and Azure accounts, so I suggest you fork this 
repo and adjust the files described below for your purposes.

# Build Options

## 1. Use my Docker image

I have a pipeline will make the docker image and deploy it to [my personal Docker hub](https://hub.docker.com/r/robjahn/dtcli-webproxy/)

Jump to the Run section below to see how to just use it.

## 2. Build Docker and push to your own Docker Hub account

You will need a docker hub account and you will have to have run ```docker login``` first.

Use these two Window batch scripts as aides:

* docker_build.bat - this will build image called ```dtcli-webproxy``` 
* docker_push.bat - this will push to my docker hub repo, so adjust this script for your testing

Run using the same instructions from #1 above

## 3. Azure Devops "Build" Pipeline

Use an Azure pipeline to make the docker image and deploy it to an Azure container registry or Docker hub
using the ```azure-pipelines.yaml``` within this repo.

To add your own build pipeline, perform these steps:
1. add a build pipeline pointing to this GIT repo
2. when prompted add the GIT service connection with the credentials
3. define these variables in your build pipeline in the web UI:
  * registryType: either value of 'docker' or 'azure'
  * containerRegistry: required for example rjahndemoregistry.azurecr.io for 'azure' or robjahn for 'docker'
  * dockerPassword: Your password for Docker Hub account.  Only required for type = 'docker'
4. If you use type azure, add a service connection of type 'Type: Azure Resource Manager' within project settings
5. If you use type azure, adjust this ```azure-pipelines.yaml``` with the name of your subscription service connection in the variable 'SUBSCRIPTION_SERVICE_CONNECTION'. This must be hardcoded due to Microsoft limitation
6. Once the build pipelines, you will need to setup a "deploy" pipeline to deploy it. See run option #2 below for instructions.

NOTE: 
* My pipeline will deploy to [my personal Docker hub](https://hub.docker.com/r/robjahn/dtcli-webproxy/) 
[![Build Status](https://dev.azure.com/robjahn/unbreakablepipeline/_apis/build/status/dtcli-proxy/robertjahn.dtcli-webproxy%20-%20Docker%20Build%20and%20Push?branchName=master)](https://dev.azure.com/robjahn/unbreakablepipeline/_build/latest?definitionId=5)
* My pipeline will deploy to my personal Azure Container registry (not public)
[![Build Status](https://dev.azure.com/robjahn/unbreakablepipeline/_apis/build/status/dtcli-proxy/robertjahn.dtcli-webproxy%20-%20Azure%20Build%20and%20Push?branchName=master)](https://dev.azure.com/robjahn/unbreakablepipeline/_build/latest?definitionId=12)

# Run Options

## 1. Pull image from Docker Hub and run it

You can do this locally or on some VM. You must have docker installed for this, but simple as pull and run.
```
# these are commands using my docker image
docker pull robjahn/dtcli-webproxy 
docker run --rm -p 5000:5000 --name dtcli-webproxy robjahn/dtcli-webproxy
```

To Stop, hit ctrl-c and then run these commands to cleanup Docker
```
# stop container
docker stop dtcli-webproxy
# remove image
docker rmi robjahn/dtcli-webproxy
```

## 2. Use the Azure CLI to create an Azure container service using ARM templates

In the ```\arm``` subfolder is a Unix Makefile that will call the Azure CLI which uses an Azure Resource 
Management (ARM) template that will create and update an Azure container service instance that 
will use the docker image deployed to my docker hub repo. You can adjust the parameters for your use.

The ```deploy.sh``` script is provided by Microsoft actually calls the CLI and will create a resource group and container if it does not exist.


To run this, perform these steps:
1. Edit the containerURI value in ```paramters.json``` file to match the image name before you run the script.
2. Create a file called ```subscription.txt``` in the ```arm``` subfolder that contains your Azure
subscription value.  This file is excluded in the ```.gitignore``` and just gets read in my the Makefile.
3. Install have the Azure CLI with connection to your azure subscription
4. Run the ```make``` command from Unix sub-system for Windows, MacOS or unix.
```
# change into arm directory where the Makefile resides
cd arm
# This will display values that will be used during the deployment
make 
# adjust Makefile & parameters.json as required
make container_deploy
# this will remove the container - be careful
make container_remove
# this will remove the whole group - be careful
make group_remove
```

5. See the resource group and container as its created in Azure web portal

## 3. Use an Azure Devops "Release" Pipeline to create an Azure container service using ARM templates

In the ```\arm``` subfolder is a Azure Resource Management (ARM) template that will create and update an Azure container 
service instance that will use the docker image deployed to my docker hub repo. You can adjust the parameters for your use.

To add your own build pipline, perform these steps:
1. add a release pipeline pointing to the artifact from the build pipeline
2. add a 'Azure Resource Group Deployment' task to the first stage
  * pick action = create or update resource group
  * template location = linked artifact
  * use the file selector to link the template and parameter files that are in the artifact
3. run pipeline and verify container service is running the app via the container properties image name

# Testing

Yes will seem odd, but the body of the POST request is in a query string format as to support the demo.  

[PostMan](https://www.getpostman.com/) is a good tool to test with.  Follow these steps to test.  

```
# make request to end point
http://localhost:5000/api/DTCLIProxy/MonspecPullRequest

serviceToCompare=SampleJSonService/StagingToProduction&compareWindow=5&dynatraceTennantUrl=https://[YOUR TENTANT].live.dynatrace.com&token=[YOUR TOKEN]&monspecFile={
    "SampleJSonService" : {
        "etype": "SERVICE",
        "_comment_etype" : "Options are SERVICE, APPLICATION, HOST, PROCESS_GROUP_INSTANCE",
        "name": "SampleNodeJsService",
        "owner" : "Dev Team",
        "_comment" : "This defines our initial thoughts about monitoring!",
        "environments" : {
            "Staging" : {
                "tags" : [
                    {
                        "context": "Environment",
                        "key": "DEPLOYMENT_GROUP_NAME",
                        "value": "Staging"
                    }
                ]
            },
            "Production" : {
                "tags" : [
                    {
                        "context": "Environment",
                        "key": "DEPLOYMENT_GROUP_NAME",
                        "value": "Production"
                    }
                ]
            }
        },
        "_comment_environments" : "Allows you to define different environments and the ways dynatrace can identify the entities in that environment",
        "comparisons" : [
            {
                "name" : "StagingToProduction",
                "source" : "Staging",
                "compare" : "Production",
                "scalefactorperc" : {
                    "default": 30,
                    "com.dynatrace.builtin:service.requestspermin" : 90
                },
                "shiftcomparetimeframe" : 0,
                "shiftsourcetimeframe" : 0,

                "_comment_name" : "Name of that comparison setting. Needs to be specified when using this file with our automation scripts",
                "_comment_source" : "source entites. we compare timeseries from this entity with compare",
                "_comment_compare": "compare entites. basically our baseline which we compare source against",
                "_comment_scalefactorperc": "+/-(0-100)% number: if 10 it means that source can be 10% above/below than compare. you can define a default value but override it for individual measure, e.g: if Staging has 90% less traffic that prod you can define that here",
                "_comment_shiftsourcetimeframe" : "allows you to define a shifted timeframe back to NOW(). Its in seconds, e.g: 600 means we compare against 10 minutes ago",
                "_comment_shiftcomparetimeframe" : "allows you to define a shifted timeframe to NOW(). Its in seconds, e.g: 86400 means we compare against same time 1 day ago"
            },
            {
                "name" : "StagingToProductionYesterday",
                "source" : "Staging",
                "compare" : "Production",
                "scalefactorperc" : {
                    "default": 15,
                    "com.dynatrace.builtin:service.requestspermin" : 90
                },
                "shiftsourcetimeframe" : 60,
                "shiftcomparetimeframe" : 86400
            },
            {
                "name" : "StagingToStagingLastHour",
                "source" : "Staging",
                "compare" : "Staging",
                "scalefactorperc" : { "default": 10},
                "shiftsourcetimeframe" : 60,
                "shiftcomparetimeframe" : 3600
            },
            {
                "name" : "ProductionToProductionLastHour",
                "source" : "Production",
                "compare" : "Production",
                "scalefactorperc" : { "default": 10, "com.dynatrace.builtin:service.requestspermin" : 30},
                "shiftsourcetimeframe" : 60,
                "shiftcomparetimeframe" : 3600
            }
        ],
        "_comment_comparisons" : "Allows you to define different comparison configurations which can be used to automate comparison between environments and timeframes",
        "perfsignature" : [
            {
                "timeseries" : "com.dynatrace.builtin:service.responsetime",
                "aggregate" : "avg",
                "validate" : "upper",
                "_upperlimit" : 100,
                "_lowerlimit" : 50,
                "_comment_aggregate" : "Depending on the metric can be: min, max, avg, sum, median, count, pXX (=XX th percentile) ",
                "_comment_validate" : "Defines whether we compare the upper or lower boundary of the calculated value bandwidth. Default is upper as for most metrics (response time, failure rate) we dont want the value to exceed our upper threshold",
                "_comment_upperlimit" : "if specified we compare against this static threshold - otherwise against what is specified in comparison",
                "_comment_lowerlimit" : "if specified, we compare against this static threshold - otherwise against what is specified in comparison"
            },
            {
                "timeseries" : "com.dynatrace.builtin:service.responsetime",
                "aggregate" : "p90"
            },
            {
                "timeseries" : "com.dynatrace.builtin:service.failurerate",
                "aggregate" : "avg"
            },
            {
                "timeseries" : "com.dynatrace.builtin:service.requestspermin",
                "aggregate" : "count",
                "validate" : "lower"
            },
            {
                "smartscape" : "toRelationships:calls",
                "upperlimit" : "2",
                "aggregate" : "count",
                "validate" : "lower"
            },
            {
                "smartscape" : "fromRelationships:runsOn",
                "aggregate" : "count",
                "validate" : "lower"
            },
            {
                "smartscape" : "fromRelationships:calls",
                "aggregate" : "count",
                "validate" : "lower"
            }
        ],
        "_comment_perfsignature" : "this is the list of key metrics that make up your performance signature. we will then compare these metrics against the compare enviornment or a static threshold",
        "servicemethods" : [
            {
                "name" : "/api/invoke",
                "perfsignature" : [
                    {
                        "timeseries" : "com.dynatrace.builtin:servicemethod.responsetime",
                        "aggregate" : "avg"
                    },
                    {
                        "timeseries" : "com.dynatrace.builtin:servicemethod.responsetime",
                        "aggregate" : "p90"
                    },
                    {
                        "timeseries" : "com.dynatrace.builtin:servicemethod.failurerate",
                        "aggregate" : "avg"
                    }
                ]
            }
        ],
        "_comment_servicemethods" : "Allows you to define key metrics of individual service methods and not just the service itself"
    }
}&pipelineInfoFile={
    "displayName" : "SampleDevOpsPipeline",
    "favicon" : "https://upload.wikimedia.org/wikipedia/commons/a/a8/Microsoft_Azure_Logo.svg",
    "configUrl" : "",
    "tags" : ["", ""],
    "properties" : {"Project" : "SampleDevOpsPipeline"}
}
```

If the application gets an error it will still return a 200 return code with this outpout
```
{
    "performanceSignature": [],
    "totalViolations": 1,
    "comment": "error calling function: python /dynatrace-cli/dtcli.py monspec pullcompare XXXX  Failed to establish a new connection: [Errno -2] Name does not resolve'))\")}\n"
}
```


# Development

Edit the ```app.py``` and use this ```app_build_and_run.bat``` for a quick way to build and run the app locally.

Shell into running container via: ```docker exec -it dtcli-webproxy /bin/sh```
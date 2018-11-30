from flask import Flask, jsonify, request
from flask_restplus import Api, Resource, fields, reqparse, inputs
from pathlib import Path

import os
import subprocess
import logging
import requests
import json


app = Flask(__name__)
api = Api(app,
          title='Dynatrace Proxy App',
          description='Rest App used as proxy to the Dynatrace API',
          contact='rob.jahn@dynatrace.com')

# this will be the root URI and set grouping within swagger
ns = api.namespace('api', description='Dynatrace API operations')

# CONSTANTS
APP_VERSION = '1'
MONSPEC_FILE = '/smplmonspec.json'
PIPELINEINFO_FILE = '/smplpipelineinfo.json'
RESULTS_FILE = '/output.json'
DT_CLI_COMMAND = 'python /dynatrace-cli/dtcli.py'
DT_CONFIG_FILE = '/dynatrace-cli/dtconfig.json'

monspec_pull_request = api.model('MonspecPullRequest', {
    'tenanthost': fields.String(description='DT host URL. e.g. https://XXXX.live.dynatrace.com', required=True),
    'token': fields.String(description='DT API Token', required=True),
    'monspecFile': fields.String(description='URL to MonSpec file', required=True),
    'pipelineInfoFile': fields.String(description='UTL to Pipeline Info file', required=True),
    'serviceToCompare': fields.String(description='Monspec value to compare. e.g. SampleJSonService/ProductionToStaging', required=True),
    'compareWindow': fields.String(description='Number of minutes to compare. e.g. 5', required=True)
})

@api.route('/version')
class Hosts(Resource):
    def get(self):
        return {"app version": APP_VERSION}

@ns.route('/DTCLIProxy/MonspecPullRequest')
class MonSpecCompare(Resource):

    #@ns.expect(monspec_pull_request)
    @ns.response(200, 'Success')
    @ns.response(500, 'Processing Error')
    def post(self):

        logging.debug(request)
        request_body = request.stream.read().decode("utf-8")
        logging.debug(request_body)

        sets = request_body.split("&")
        for a_set in sets:
            logging.debug(a_set)
            key_value = a_set.split('=', 1)
            if str(key_value[0]) == 'serviceToCompare':
                serviceToCompare = key_value[1]
            elif key_value[0] == 'compareWindow':
                compareWindow = key_value[1]
            elif key_value[0] == 'dynatraceTennantUrl':
                dynatraceTennantUrl = key_value[1]
            elif key_value[0] == 'token':
                token = key_value[1]
            elif key_value[0] == 'monspecFile':
                monspecFile = key_value[1]
            elif key_value[0] == 'pipelineInfoFile':
                pipelineInfoFile = key_value[1]
            else:
                logging.error("Bad argument: " + key_value[0])

        # setup security based on passed in values
        if not cliConfigure(token, dynatraceTennantUrl):
            error = getOutputFileContents(RESULTS_FILE)
            return {"error": error, "function": "cliConfigure"}, 500

        # save strings to files that will be passed in the to CLI
        saveFileFromString(MONSPEC_FILE, monspecFile)
        saveFileFromString(PIPELINEINFO_FILE, pipelineInfoFile)

        # make cli call
        cmd = DT_CLI_COMMAND + ' monspec pullcompare ' + MONSPEC_FILE + ' ' + PIPELINEINFO_FILE + ' ' \
            + serviceToCompare + ' ' + compareWindow + ' > ' + RESULTS_FILE
        if not callCli(cmd):
            error = getOutputFileContents(RESULTS_FILE)
            return {"error": error, "function": cmd}, 500

        return json.loads(getOutputFileContents(RESULTS_FILE))

# TODO -- Make work as to support this.  Also consider making one for custom event
#@api.route('/deployevent')
class DeployEvent(Resource):
    #def deploymentEvent(entity, options_string_array):
    def post(self):
        entity = ''
        options_string_array = ['']
        cmd = DT_CLI_COMMAND + ' evt push ' + entity + ' ' + " ".join(options_string_array) + ' > ' + RESULTS_FILE
        if not callCli(cmd):
            error = getOutputFileContents(RESULTS_FILE)
            return {"error": error}

        return getOutputFileContents(RESULTS_FILE)


# TODO -- Just for quick test, will remove or make more generic and include it
#@ns.route('/hosts')
class Hosts(Resource):
    def get(self):
        cmd = DT_CLI_COMMAND + ' ent host .* > ' + RESULTS_FILE
        if not callCli(cmd):
            error = getOutputFileContents(RESULTS_FILE)
            return {"error": error}

        return getOutputFileContents(RESULTS_FILE)

def callCli(cmd):
    logging.debug('callCli cmd: ' + cmd)
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except Exception:
        return False

def saveFileFromString(file_to_save, content_string):
    with open(file_to_save, 'w') as f:
        f.write(content_string)
    return True

def saveFileFromUrl(file_url, file_to_save):
    r = requests.get(file_url)
    if r.status_code == 200:
        jsondata = r.json()
        with open(file_to_save, 'w') as f:
            json.dump(jsondata, f)
        return True
    else:
        return False

def getOutputFileContents(theFile):
    results_file = Path(theFile)
    if results_file.is_file():
        if results_file.stat().st_size > 0:
            with open(theFile, 'r') as the_file:
                resultContent = the_file.read()
        else:
            resultContent = 'File has no contents: ' + theFile
    else:
        resultContent = 'File not found: ' + theFile

    logging.debug('=============================================================')
    logging.debug('Contents for file: ' + theFile)
    logging.debug(resultContent)
    logging.debug('=============================================================')

    return resultContent

def cliConfigure(token, tenanthost):
    """
    # Don't enable this for a pipeline.  Just use locally
    logging.debug('==========================================================')
    logging.debug('DT TOKEN = ' + token)
    logging.debug('DT TENANT HOST = ' + tenanthost)
    logging.debug('==========================================================')
    """

    cmd = DT_CLI_COMMAND + ' config apitoken ' + token + ' tenanthost ' + tenanthost + ' > ' + RESULTS_FILE
    if not callCli(cmd):
        return False
    else:
        """
        # Don't enable this for a pipeline.  Just use locally
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            getOutputFileContents(RESULTS_FILE)
            getOutputFileContents(DT_CONFIG_FILE)
        """
        return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    if ('DT_API_TOKEN' in os.environ) and ('DT_TENANT_HOST' in os.environ):
        cliConfigure(os.environ['DT_API_TOKEN'], os.environ['DT_TENANT_HOST'])

    app.run(debug=True, host='0.0.0.0')

    # TODO - in future may want to require initialize this way
    """
    # validate environment variables exist.  If not, abort
    if 'DT_API_TOKEN' not in os.environ:
        print('Abort: DT_API_TOKEN is a required environment argument')
        exit(1)

    if 'DT_TENANT_HOST' not in os.environ:
        print('Abort: DT_TENANT_HOST is a required environment argument')
        exit(1)
    """

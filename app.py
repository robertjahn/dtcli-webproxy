from flask import Flask, jsonify, request
from flask_restplus import Api, Resource, fields, reqparse
from pathlib import Path

import os
import subprocess
import logging
import requests
import json


app = Flask(__name__)
api = Api(app)

# CONSTANTS
MONSPEC_FILE = '/smplmonspec.json'
PIPELINEINFO_FILE = '/smplpipelineinfo.json'
RESULTS_FILE = '/output.json'
DT_CLI_COMMAND = 'python /dynatrace-cli/dtcli.py'

@api.route('/monspec')
class MonSpecCompare(Resource):
    def post(self):

        # pull out the data
        json_data = request.get_json(force=True)
        tenanthost = json_data['dynatraceTennantUrl']
        token = json_data['token']
        monspecFile = json_data['monspecFile']
        pipelineInfoFile = json_data['pipelineInfoFile']
        serviceToCompare = json_data['serviceToCompare']
        compareWindow = json_data['compareWindow']

        # setup security based on passed in values
        if not cliConfigure(token, tenanthost):
            return {'error': 'something when wrong with CLI configuration'}

        # get the files from remote source and save locally for procesing
        if saveFileFromUrl(monspecFile, MONSPEC_FILE):
            getOutputFileContents(MONSPEC_FILE)
        else:
            return {'error': 'something when wrong with reading monspecFile'}

        if saveFileFromUrl(pipelineInfoFile, PIPELINEINFO_FILE):
            getOutputFileContents(PIPELINEINFO_FILE)
        else:
            return {'error': 'something when wrong with reading pipelineInfoFile'}

        # make cli call
        cmd = DT_CLI_COMMAND + ' monspec pullcompare ' + MONSPEC_FILE + ' ' + PIPELINEINFO_FILE + ' ' + serviceToCompare + ' '  + compareWindow + ' > ' + RESULTS_FILE
        if not callCli(cmd):
            error = getOutputFileContents(RESULTS_FILE)
            return {"error": error}, 50

        return jsonify(s=serviceToCompare, c=compareWindow)

@api.route('/deployevent')
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


@api.route('/hosts')
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
            resultContent = {'result': 'file has no contents'}
    else:
        resultContent = {'result': 'no file found'}

    logging.debug('=============================================================')
    logging.debug('Contents for file: ' + theFile)
    logging.debug(resultContent)
    logging.debug('=============================================================')

    return resultContent

def cliConfigure(token, tenanthost):
    logging.debug('==========================================================')
    logging.debug('DT TOKEN = ' + token)
    logging.debug('DT TENANT HOST = ' + tenanthost)
    logging.debug('==========================================================')

    cmd = DT_CLI_COMMAND + ' config apitoken ' + token + ' tenanthost ' + tenanthost + ' > ' + RESULTS_FILE
    subprocess.run(cmd, shell=True, check=True)

    if logging.getLogger().isEnabledFor(logging.DEBUG):
        getOutputFileContents(RESULTS_FILE)
        getOutputFileContents('/dynatrace-cli/dtconfig.json')

    return True


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    # validate envionrment variables exist.  If not, abort
    if 'DT_API_TOKEN' not in os.environ:
        print('Abort: DT_API_TOKEN is a required environment argument')
        exit(1)

    if 'DT_TENANT_HOST' not in os.environ:
        print('Abort: DT_TENANT_HOST is a required environment argument')
        exit(1)

    cliConfigure(os.environ['DT_API_TOKEN'], os.environ['DT_TENANT_HOST'])

    app.run(debug=True, host='0.0.0.0')
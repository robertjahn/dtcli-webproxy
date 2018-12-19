from flask import Flask, jsonify, request
from flask_restplus import Api, Resource, fields, reqparse, inputs
from pathlib import Path

import subprocess
import logging
import json
import datetime
import os


# CONSTANTS
APP_VERSION = '5'
DT_CLI_COMMAND = 'python /dynatrace-cli/dtcli.py'

app = Flask(__name__)
api = Api(app,
          title='Dynatrace Proxy App',
          description='Rest App used as proxy to the Dynatrace API',
          contact='rob.jahn@dynatrace.com')

# this will be the root URI and set grouping within swagger
ns = api.namespace('api', description='Dynatrace API operations')

@api.route('/version')
class Hosts(Resource):
    def get(self):
        return {
                "current_version": APP_VERSION,
                "version_comments": [
                    { "version": "5", "comment": "convert null to zero in response and add error handing and change error response to be 200" },
                    { "version": "4", "comment": "Saves internal working files to unique names" }
                ]
                }

@ns.route('/DTCLIProxy/MonspecPullRequest')
class MonSpecCompare(Resource):

    @ns.response(200, 'Success')
    @ns.response(500, 'Processing Error')
    def post(self):

        logging.debug(request)
        request_body = request.stream.read().decode("utf-8")
        logging.debug(request_body)

        serviceToCompare = None
        compareWindow = None
        dynatraceTennantUrl = None
        token = None
        monspecFile = None
        pipelineInfoFile = None

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

        # argument validation
        if not serviceToCompare:
            return {"performanceSignature": [], "totalViolations": 1, "comment": "serviceToCompare argument not passed"}, 200
        if not compareWindow:
            return {"performanceSignature": [], "totalViolations": 1, "comment": "compareWindow argument not passed"}, 200
        if not dynatraceTennantUrl:
            return {"performanceSignature": [], "totalViolations": 1, "comment": "dynatraceTennantUrl argument not passed"}, 200
        if not token:
            return {"performanceSignature": [], "totalViolations": 1, "comment": "token argument not passed"}, 200
        if not monspecFile:
            return {"performanceSignature": [], "totalViolations": 1, "comment": "monspecFile argument not passed"}, 200
        if not pipelineInfoFile:
            return {"performanceSignature": [], "totalViolations": 1, "comment": "pipelineInfoFile argument not passed"}, 200


        # save strings to files that will be passed in the to CLI
        ts = datetime.datetime.now().timestamp()
        MONSPEC_FILE = '/smplmonspec_' + str(ts) + '.json'
        PIPELINEINFO_FILE = '/smplpipelineinfo_' + str(ts) + '.json'
        RESULTS_FILE = '/output_' + str(ts) + '.json'

        # setup security based on passed in values
        if not cliConfigure(token, dynatraceTennantUrl, RESULTS_FILE):
            error = getOutputFileContents(RESULTS_FILE)
            return {"performanceSignature": [], "totalViolations": 1, "comment": "Error calling cliConfigure"}, 200

        # have to save to file, for the CLI expects a file
        saveFileFromString(MONSPEC_FILE, monspecFile)
        saveFileFromString(PIPELINEINFO_FILE, pipelineInfoFile)

        # make cli call
        cmd = DT_CLI_COMMAND + ' monspec pullcompare ' + MONSPEC_FILE + ' ' + PIPELINEINFO_FILE + ' ' \
            + serviceToCompare + ' ' + compareWindow + ' > ' + RESULTS_FILE
        if not callCli(cmd):
            error = getOutputFileContents(RESULTS_FILE)
            return {"performanceSignature": [], "totalViolations": 1, "comment": "error calling function: " + cmd + " " + error}, 200

        result_json_string = json.loads(getOutputFileContents(RESULTS_FILE).replace(": null", ": 0"))
        if os.path.exists(MONSPEC_FILE):
            os.remove(MONSPEC_FILE)
        if os.path.exists(PIPELINEINFO_FILE):
            os.remove(PIPELINEINFO_FILE)
        if os.path.exists(RESULTS_FILE):
            os.remove(RESULTS_FILE)
        return result_json_string

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

def cliConfigure(token, tenanthost, configure_results_file):
    cmd = DT_CLI_COMMAND + ' config apitoken ' + token + ' tenanthost ' + tenanthost + ' > ' + configure_results_file
    if not callCli(cmd):
        return False
    else:
        return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.info('running version:'+ APP_VERSION)
    app.run(debug=True, host='0.0.0.0')

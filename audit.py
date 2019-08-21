"""

Description:
 A simple lambda function which will run a quick audit of AWS instances,
 VPCs and workspaces

"""

import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import boto3
# X-ray instrumentation
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

# imports from common lib
import common

# patch boto for xray usage
patch(['boto3'])

AWS_REGIONS = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


@xray_recorder.capture('get_systems_manager_parameter')
def get_systems_manager_parameter(param_name):
    """
    Retrieve the given parameter from the AWS Systems Manager

    :param param_name: The parm to get from Systems Manager
    :return: The output from Systems Manager
    """

    # Create the SSM Client
    ssm = boto3.client('ssm', region_name='us-east-2')

    # Get the requested parameter
    response = ssm.get_parameters(
        Names=[
            param_name,
        ],
        WithDecryption=False
    )

    # Store the credentials in a variable
    credentials = response['Parameters'][0]['Value']

    xray_recorder.current_subsegment().put_annotation('credentials', credentials)

    return credentials


@xray_recorder.capture('post_to_teams')
def post_to_teams(msg):
    """
    Post the given message to a pre-defined MS Teams channel

    :param msg: The message to be posted
    :return: Nothing
    """

    # prints to cloudwatch
    print(msg)

    teams_message = {
        "@context": "https://schema.org/extensions",
        "@type": "MessageCard",
        "themeColor": "0072C6",
        "title": "CADO AWS Audit Snapshot",
        "text": "<pre>%s</pre>" % msg
    }

    #
    # We keep the webhook for our Teams URL in a Systems Manager parameter.
    # This allows us to make the repo public without compromising security
    #
    # Comment out line below for debug
    hook_url = get_systems_manager_parameter("rtt-audit-output-teams-channel")

    # UN-comment line below for debug
    # hook_url = get_systems_manager_parameter("rtt-audit-output-test-channel")

    xray_recorder.current_subsegment().put_annotation('hook_url', hook_url)

    data = json.dumps(teams_message)

    req = Request(hook_url, data.encode('utf-8'))

    try:
        response = urlopen(req)
        response.read()
        LOGGER.info("Message posted")
    except HTTPError as e:
        LOGGER.error("Request failed: %d %s", e.code, e.reason)
        xray_recorder.current_subsegment().put_annotation('http_error', e.code)
    except URLError as e:
        LOGGER.error("Server connection failed: %s", e.reason)
        xray_recorder.current_subsegment().put_annotation('url_error', e.reason)


# noinspection PyUnusedLocal
@xray_recorder.capture('handler')
def handler(event, context):
    """
    The main lambda function handler

    :param event:  The event which drives the function (unused)
    :param context: The context in which the function is called (unused)
    :return: Nothing.
    """
    out_data = ""
    for region in AWS_REGIONS:
        client = boto3.client('ec2', region_name=region)
        out_data += common.post_by_vpc(ec2=client)
        out_data += common.print_unattached_volumes(region)
        out_data += common.print_snapshots(client, region)
        out_data += common.print_workspaces('AVAILABLE', region)

    if out_data:
        post_to_teams(out_data)
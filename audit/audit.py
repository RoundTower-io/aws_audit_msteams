"""

Description:
 A simple lambda function which will run a quick audit of AWS instances,
 VPCs and workspaces

"""
from __future__ import print_function
from common import post_by_vpc
from common import print_workspaces
from common import print_unattached_volumes
import boto3
import json
import logging
from urllib2 import Request, urlopen, URLError, HTTPError

# X-ray instrumentation
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

# patch boto for xray usage
patch(['boto3'])

AWS_REGIONS = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@xray_recorder.capture('get_systems_manager_parameter')
def get_systems_manager_parameter(param_name):

    # Create the SSM Client
    ssm = boto3.client('ssm', region_name='us-east-2' )

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
    #hook_url = get_systems_manager_parameter("rtt-audit-output-teams-channel")
    hook_url = get_systems_manager_parameter("rtt-audit-output-test-channel")
    xray_recorder.current_subsegment().put_annotation('hook_url', hook_url)

    req = Request(hook_url, json.dumps(teams_message))

    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted")
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
        xray_recorder.current_subsegment().put_annotation('http_error', e.code)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)
        xray_recorder.current_subsegment().put_annotation('url_error', e.reason)


# noinspection PyUnusedLocal
def handler(event, context):
    out_data = ""
    for region in AWS_REGIONS:
        client = boto3.client('ec2', region_name=region)
        out_data = out_data + post_by_vpc(ec2=client)
        out_data = out_data + print_unattached_volumes(region)

    out_data = out_data + print_workspaces('AVAILABLE', 'us-east-1')

    if out_data:
        post_to_teams(out_data)


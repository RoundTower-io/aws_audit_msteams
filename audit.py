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

AWS_HOME_REGION = 'us-east-2'
AWS_SYSTEMS_MANAGER_PARM = "rtt-audit-output-teams-channel"
# line below for debug
AWS_SYSTEMS_MANAGER_PARM_TEST = "rtt-audit-output-test-channel"

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
    ssm = boto3.client('ssm', region_name=AWS_HOME_REGION)

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
def post_to_teams(msg, destination):
    """
    Post the given message to a pre-defined MS Teams channel

    :param destination: The destination Teams channel for our output
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
    # Keep the webhook for our Teams URL in a Systems Manager parameter.
    # This allows us to make the repo public without compromising security
    #
    # Comment out line below for debug
    hook_url = get_systems_manager_parameter(destination)

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


@xray_recorder.capture('get_regions')
def get_regions():
    """
    A simple routine to retrieve all the AWS region names
    :return: A list of region names
    """
    region_list = []
    ec2 = boto3.client('ec2')

    # Retrieves all regions/endpoints that work with EC2
    response = ec2.describe_regions()

    for region in response["Regions"]:
        region_list.append(region["RegionName"])

    return region_list


@xray_recorder.capture('gather_output_data')
def gather_output_data():
    """
    Get output data from various sources
    :return: string
    """
    out_data = ""
    for region in get_regions():
        print("Handling region: " + region)
        client = boto3.client('ec2', region_name=region)
        out_data += common.print_instances(client)
        out_data += common.print_unattached_volumes(region)
        out_data += common.print_snapshots(client, region)
        out_data += common.print_workspaces('AVAILABLE', region)
        out_data += common.print_elastic_ips(client, region)

    return out_data


@xray_recorder.capture('handle_scheduled_invocation')
def handle_scheduled_invocation(destination):
    """
    Collect output data and send it to MS Teams webhook
    :param destination: The destination Teams channel for our output
    :return: nothing
    """
    out_data = gather_output_data()
    if out_data:
        post_to_teams(out_data, destination)
    else:
        print("Nothing to report")


# noinspection PyUnusedLocal
@xray_recorder.capture('handler')
def handler(event, context):
    """
    The main lambda function handler

    :param event:  The event which drives the function (unused)
    :param context: The context in which the function is called (unused)
    :return: Nothing.
    """
    #print("Event:\n"+str(event))
    xray_recorder.current_subsegment().put_annotation('event', event)
    xray_recorder.current_subsegment().put_annotation('context', context)

    # Lambda test data of type "Schedule" will have a 1970 timestamp
    if event['time'] == "1970-01-01T00:00:00Z":
        destination = "rtt-audit-output-test-channel"
    else:
        destination = "rtt-audit-output-teams-channel"

    handle_scheduled_invocation(destination)

"""

Description:
 A simple lambda function which will run a quick audit of AWS instances,
 VPCs and workspaces

"""
from __future__ import print_function
from common import post_by_vpc
from common import print_workspaces
import boto3
import json
import logging
from urllib2 import Request, urlopen, URLError, HTTPError

AWS_REGIONS = [ 'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']
AWS_ENGINEERING_ID = "375301133253"
IDS = [AWS_ENGINEERING_ID]

# noinspection PyPep8
HOOK_URL = 'https://outlook.office.com/webhook/3d224b9f-a9a8-474e-9d62-6138e993a8a5@6a8ff3cc-d3cc-4944-9654-edad9087dfdc/IncomingWebhook/a6adac7f3b3541698f47a87246e04b39/edfddb3f-3fff-4646-8b9a-eb854503b582'
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def post_to_slack(msg):
    # uncomment to debug
    print(msg)
    #return
    teams_message = {
        "@context": "https://schema.org/extensions",
        "@type": "MessageCard",
        "themeColor": "0072C6",
        "title": "CADO AWS Audit Snapshot",
        "text": "<pre>%s</pre>" % msg
    }
    req = Request(HOOK_URL, json.dumps(teams_message))
    try:
        response = urlopen(req)
        response.read()
        #logger.info("Message posted to %s", teams_message['channel'])
        logger.info("Message posted")
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)


# noinspection PyUnusedLocal
def handler(event, context):
    out_data = ""
    for region in AWS_REGIONS:
        client = boto3.client('ec2', region_name=region)
        out_data = out_data + post_by_vpc(ec2=client)

    out_data = out_data + print_workspaces('AVAILABLE', 'us-east-1')

    if len(out_data):
        post_to_slack(out_data)


# Uncomment to debug
#handler("", "")

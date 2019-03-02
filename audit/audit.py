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
from botocore.exceptions import ClientError

AWS_REGIONS = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']
AWS_ENGINEERING_ID = "375301133253"
IDS = [AWS_ENGINEERING_ID]

# noinspection PyPep8
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_to_teams(msg):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "Sender Name <lambda@aws.roundtower.io.com>"

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    RECIPIENT = "tennis.smith@roundtower.com"

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"

    # The subject line for the email.
    SUBJECT = "Amazon SES Test (SDK for Python)"

    # The email body for recipients with non-HTML email clients.
    # BODY_TEXT = ("Amazon SES Test (Python)\r\n"
    #              "This email was sent with Amazon SES using the "
    #              "AWS SDK for Python (Boto)."
    #              )
    BODY_TEXT = msg


    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
      <h1>Amazon SES Test (SDK for Python)</h1>
      <p>This email was sent with
        <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
        <a href='https://aws.amazon.com/sdk-for-python/'>
          AWS SDK for Python (Boto)</a>.</p>
    </body>
    </html>
                """

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


# noinspection PyUnusedLocal
def handler(event, context):
    instances = ''
    for region in AWS_REGIONS:
        client = boto3.client('ec2', region_name=region)
        instances += post_by_vpc(ec2=client)

    workspaces = print_workspaces('AVAILABLE', 'us-east-1')

    report = instances+workspaces

    send_to_teams(report)

# Uncomment to debug
#handler("", "")

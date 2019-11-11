#!/usr/bin/env python
"""

Description:
 Simple functions which will run a quick audit AWS instances, AMIs and
 VPCs

"""

from io import StringIO
import boto3
from botocore.exceptions import EndpointConnectionError

# X-ray instrumentation
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

patch(['boto3'])

NAME_LEN = 20
INST_LEN = 16
IMG_LEN = 16
LAUNCHED_LEN = 14
TYPE_LEN = 12

BODY_TEMPLATE = '{NAME:%d}{INST:%d}{IMG:%d}{LAUNCHED:%d}{TYPE:%d}\n' % \
                (NAME_LEN, INST_LEN, IMG_LEN, LAUNCHED_LEN, TYPE_LEN)
HEADER_TEMPLATE = 'Name: {0}  Region: {1}  VPC: {2}\n'


@xray_recorder.capture('get_name_tag')
def get_name_tag(tags):
    """
    Search through a collection of tags and return the value of a particular one

    :param tags:  The tags to search
    :return:  The value for that particular tag
    """
    name = 'none'
    if tags:
        for t in tags:
            if isinstance(t, dict) and t['Key'] == 'Name':
                name = t['Value']
    return name


@xray_recorder.capture('get_sorted_vpc_list')
def get_sorted_vpc_list(vpcs):
    """
    Take a list of VPCs and sort them.

    :param vpcs: The unsorted list of VPCs
    :return: A sorted list of VPCs
    """
    vpc_list = []
    for v in vpcs['Vpcs']:
        if v['IsDefault']:
            vname = 'Default'
        elif 'Tags' in v:
            vtags = v['Tags']
            for vt in vtags:
                if isinstance(vt, dict) and vt['Key'] == 'Name':
                    vname = vt['Value']
        else:
            vname = 'UNKNOWN'

        vpc = v['VpcId']

        assert vname is not None
        vpc_list.append([vname, vpc])

    return sorted(vpc_list)


@xray_recorder.capture('get_sorted_vpc_entries_list')
def get_sorted_vpc_entries_list(entries):
    """
    Take a list of VPC entries and sort them

    :param entries:  The VPC entries
    :return:  The sorted version
    """
    entry_list = []
    for reservation in entries:
        for each in reservation["Instances"]:
            if "Tags" in each:
                name = get_name_tag(each["Tags"])
            else:
                name = "None"
            entry_list.append(
                [name,
                 each['InstanceId'],
                 each['ImageId'],
                 each['LaunchTime'].strftime("%Y-%m-%d"),
                 each['InstanceType']]
            )
    return sorted(entry_list)


@xray_recorder.capture('get_box_status')
def get_box_status(boxes, status="running"):
    """
    Take a list of instances and return those that match the 'status' value

    :param boxes: The list of boxes (instances) to search through
    :param status: The status you are searching for
    :return: A list of instances that match the status value passed
    """
    box_list = []
    for box in boxes:
        if box["Instances"][0]["State"]["Name"] == status:
            box_list.append(box)
    return box_list


@xray_recorder.capture('abbreviate_name')
def abbreviate_name(a_string, max_length):
    """
    Abbreviate a name to the first max_length - 5
    Append ellipsis to the remainder
    :param a_string: A string to be abbreviated
    :param max_length: The max length the string can be.
    :return: An abbreviated string
    """
    if len(a_string) > int(max_length):
        return str(a_string[0:int(max_length-5)]+'...')
    return a_string


@xray_recorder.capture('abbreviate_id')
def abbreviate_id(a_string):
    """
    1. Hack off the first 6 and the last 4 characters.
    2. Then join them with an ellipsis.

    :param a_string:
    :return: An abbreviated id string
    """
    return str(a_string[0:6]+'...'+a_string[-4::])


@xray_recorder.capture('print_instances')
def print_instances(ec2):
    """
    Print out VPC information in a pretty format

    :param ec2: The boto3 ec2 client
    :return: The nicely formatted list of VPCs
    """
    vpcs = ec2.describe_vpcs()
    fp = StringIO()

    for e in get_sorted_vpc_list(vpcs):
        vpc_name = e[0]
        vpc_id = e[1]
        vpc_filter = [
            {
                'Name': 'vpc-id',
                'Values': [vpc_id]
            }
        ]
        res = get_box_status(ec2.describe_instances(Filters=vpc_filter)["Reservations"], "running")
        if not res:
            continue

        region = ec2.meta.region_name
        fp.write('\n')
        fp.write(HEADER_TEMPLATE.format(vpc_name, region, vpc_id.replace('vpc-', '')))
        fp.write('\n')
        fp.write(BODY_TEMPLATE.format(NAME='Name',
                                      INST='Instance',
                                      IMG='Image',
                                      LAUNCHED='Launched',
                                      TYPE='Type'))

        fp.write(BODY_TEMPLATE.format(NAME=('-' * (NAME_LEN - 2)),
                                      INST=('-' * (INST_LEN - 2)),
                                      IMG=('-' * (IMG_LEN - 2)),
                                      LAUNCHED=('-' * (LAUNCHED_LEN - 2)),
                                      TYPE=('-' * (TYPE_LEN - 2))))

        for instance in get_sorted_vpc_entries_list(res):
            fp.write(BODY_TEMPLATE.format(NAME=abbreviate_name(instance[0], NAME_LEN),
                                          INST=abbreviate_id(instance[1]),
                                          IMG=abbreviate_id(instance[2]),
                                          LAUNCHED=instance[3],
                                          TYPE=instance[4]))
    vpc_out = fp.getvalue()
    fp.close()
    return vpc_out


@xray_recorder.capture('print_workspaces')
def print_workspaces(status, region):
    """
    Print workspace instances in a pretty format
    :param status: The instance status value we are searching for
    :param region: The region in which we are looking for workspaces
    :return: The nicely formatted list of workspaces
    """

    ws = boto3.client("workspaces", region_name=region)
    try:
        response = ws.describe_workspaces()
    except EndpointConnectionError:
        print("Region does not appear to support workspaces yet: ", region)
        return ""

    fp = StringIO()
    found = 0
    fp.write('\n')
    fp.write('Active Workspaces in %s\n' % region)
    fp.write('------------------------------\n')
    for workspace in response["Workspaces"]:
        # Some temporary variables for each workspace
        state = str(workspace["State"])
        username = str(workspace["UserName"])
        if state == status:
            fp.write(username)
            fp.write('\n')
            found += 1
    ws_out = fp.getvalue()
    fp.close()
    if not found:
        return ""
    return ws_out


@xray_recorder.capture('print_unattached_volumes')
def print_unattached_volumes(region):
    """
    Print a list of un-attached volumes

    :param region: The region we look in
    :return: A nicely formatted list list of volumes to print
    """
    ec2 = boto3.resource('ec2', region_name=region)
    volumes = ec2.volumes.filter(
        Filters=[
            {
                'Name': 'status',
                'Values': ['available']
            }
        ]
    )
    found = 0
    fp = StringIO()
    fp.write('\n')
    fp.write('UN-Attached Volumes in %s\n' % region)
    fp.write('---------------------------------\n')
    for volume in volumes:
        volume_data = ec2.Volume(volume.id)
        fp.write(str(volume.id))
        fp.write('  ')
        fp.write(str(volume_data.create_time.strftime("%Y-%m-%d")))
        fp.write('\n')
        found += 1
    vol_out = fp.getvalue()
    fp.close()
    if not found:
        return ""
    return vol_out


@xray_recorder.capture('print_snapshots')
def print_snapshots(ec2, region):
    """
    Print a list of snapshots
    :param ec2: The boto3 ec2 client
    :param region: The region to search in
    :return: The nicely formatted list of snapshots to print
    """
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])
    snapshot_list = snapshots['Snapshots']

    found = 0
    fp = StringIO()
    fp.write('\n')
    fp.write('Snapshots in %s\n' % region)
    fp.write('----------------------------------\n')
    for snapshot in snapshot_list:
        snapshot_id = snapshot['SnapshotId']
        snapshot_start_time = snapshot['StartTime'].strftime("%Y-%m-%d")
        fp.write(str(snapshot_id))
        fp.write('  ')
        fp.write(str(snapshot_start_time))
        fp.write('\n')
        found += 1
    sn_out = fp.getvalue()
    fp.close()
    if not found:
        return ""
    return sn_out


@xray_recorder.capture('print_elastic_ips')
def print_elastic_ips(ec2, region):
    """
    Print a list of UN-attached Elastic IP addresses

    :param ec2: The boto3 ec2 client
    :param region: The region to search in
    :return: The nicely formatted list of EIPs to print
    """
    addresses_dict = ec2.describe_addresses()
    found = 0
    fp = StringIO()
    fp.write('\n\n')
    fp.write('UN-attached Elastic IPs in %s\n' % region)
    fp.write('----------------------------------\n')
    for eip_dict in addresses_dict['Addresses']:
        if "InstanceId" not in eip_dict:
            fp.write(str(eip_dict['PublicIp']) + "  ")
            found += 1
    eip_out = fp.getvalue()
    fp.close()
    if not found:
        return ""
    return eip_out

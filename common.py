#!/usr/bin/env python
"""

Description:
 Simple functions which will run a quick audit AWS instances, AMIs and
 VPCs

"""
from __future__ import print_function
from io import StringIO
import datetime
import boto3

NAME_LEN = 20
INST_LEN = 23
IMG_LEN = 25
LAUNCHED_LEN = 14
TYPE_LEN = 12

BODY_TEMPLATE = u'{NAME:%d}{INST:%d}{IMG:%d}{LAUNCHED:%d}{TYPE:%d}\n' % \
                (NAME_LEN, INST_LEN, IMG_LEN, LAUNCHED_LEN, TYPE_LEN)
HEADER_TEMPLATE = u'Name: {0}  Region: {1}  VPC: {2}\n'

def get_name_tag(tags):
    name = 'none'
    if tags:
        for t in tags:
            if type(t) is dict and t['Key'] == 'Name':
                name = t['Value']
    return name


def get_sorted_vpc_list(vpcs):
    vpc_list = []
    for v in vpcs['Vpcs']:
        if v[u'IsDefault']:
            vname = 'Default'
        elif 'Tags' in v:
            vtags = v['Tags']
            for vt in vtags:
                if type(vt) is dict and vt['Key'] == 'Name':
                    vname = vt['Value']
        else:
            vname = 'UNKNOWN'

        vpc = v['VpcId']

        assert vname is not None
        vpc_list.append([vname, vpc])

    return sorted(vpc_list)


def get_sorted_vpc_entries_list(entries):
    entry_list = []
    for reservation in entries:
        for each in reservation["Instances"]:
            if "Tags" in each:
                name = get_name_tag(each["Tags"])
            else:
                name = "None"
            instid = each[u'InstanceId']
            imgid = each[u'ImageId']
            dtg = each[u'LaunchTime'].strftime("%Y-%m-%d")
            type = each[u'InstanceType']
            entry_list.append([name, instid, imgid, dtg, type])
    return sorted(entry_list)


def get_jump_box(reservations):
    for r in reservations:
        if "Tags" in r["Instances"][0]:
            for t in r["Instances"][0]["Tags"]:
                if t["Key"] == "NAME" and t["Value"] == "jump":
                    return r["Instances"][0]


def get_jump_dns(box):
    if box:
        for x in box["Tags"]:
            if x["Key"] == 'route53_config':
                return x["Value"].split(':')[1]


def get_box_status(boxes, status="running"):
    box_list = []
    for box in boxes:
        if box["Instances"][0]["State"]["Name"] == status:
            box_list.append(box)
    return box_list


def post_by_vpc(ec2):
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
        if not len(res):
            continue

        region = ec2.meta.region_name
        fp.write(u'\n')
        fp.write(HEADER_TEMPLATE.format(vpc_name, region, vpc_id.replace('vpc-', '')))
        fp.write(u'\n')
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
            fp.write(BODY_TEMPLATE.format(NAME=instance[0],
                                          INST=instance[1],
                                          IMG=instance[2],
                                          LAUNCHED=instance[3],
                                          TYPE=instance[4]))
    vpc_out = fp.getvalue()
    fp.close()
    return vpc_out


def print_workspaces(status, region):
    fp = StringIO()
    found = 0

    fp.write(u'\n')
    fp.write(u'Active Workspaces in %s\n' % region)
    fp.write(u'------------------------------\n')
    ws = boto3.client("workspaces", region_name=region)
    response = ws.describe_workspaces()
    for workspace in response["Workspaces"]:
        # Some temporary variables for each workspace
        state = str(workspace["State"])
        username = str(workspace["UserName"])
        if state == status:
            fp.write(unicode(username, "utf-8"))
            fp.write(u'\n')
            found += 1

    if found == 0:
        fp.close()
        return ""

    ws_out = fp.getvalue()
    fp.close()
    return ws_out

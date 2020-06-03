import boto3
import os
import requests
from botocore.exceptions import ClientError

def lambda_handler(event, context):
  # fetch o365 as json
  o365_list_url = 'https://endpoints.office.com/endpoints/worldwide?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7'
  o365_json = requests.get(o365_list_url).json()

  # filter on outlook_address from all o365
  outlook_address = '*.mail.protection.outlook.com'
  outlook_json = list(filter(lambda key: key.get('urls',None) == [outlook_address], o365_json))

  # find subnets in outlook_json
  for json_data in outlook_json:
    for key, value in json_data.items():
      if key == 'ips':
        outlook_subnets = value

  # connect to aws
  resource = boto3.resource("ec2")

  # fetch security group via id
  security_group_id = os.environ['SECURITY_GROUP_ID']
  security_group = resource.SecurityGroup(security_group_id)

  # filter on smtp (port 25) from all egress
  smtp_egress = list(filter(lambda rule: rule["IpProtocol"] == "tcp" and rule["FromPort"] == 25 and rule["ToPort"] == 25, security_group.ip_permissions_egress))

  # find subnets in smtp_egress
  existing_subnets = []
  for json_data in smtp_egress:
    for key, value in json_data.items():
      if key == 'IpRanges':
        existing_subnets = value

  # filter existing_subnets on matching description
  description_filter = 'lambda_o365outlook_whitelist'
  existing_subnets = list(filter(lambda rule: rule.get("Description",None) == description_filter, existing_subnets))
  filtered_subnets = []
  for json_data in existing_subnets:
    for key, value in json_data.items():
      if key == 'CidrIp':
        filtered_subnets.append(value)

  # subnets to be added and removed
  add_subnets = [outlook_subnet for outlook_subnet in outlook_subnets if outlook_subnet not in filtered_subnets]
  remove_subnets = [filtered_subnet for filtered_subnet in filtered_subnets if filtered_subnet not in outlook_subnets]

  # perform adds and removes
  client = boto3.client('ec2')
  for add_subnet in add_subnets:
    if ':' not in add_subnet:
      client.authorize_security_group_egress(
        GroupId=security_group_id,
        IpPermissions=[
          {
            'IpProtocol': 'tcp',
            'FromPort': 25,
            'ToPort': 25,
            'IpRanges': [
              {'CidrIp': add_subnet,'Description': description_filter}
            ]
          }
        ]
      )

  for add_subnet in add_subnets:
    if ':' in add_subnet:
      client.authorize_security_group_egress(
        GroupId=security_group_id,
        IpPermissions=[
          {
            'IpProtocol': 'tcp',
            'FromPort': 25,
            'ToPort': 25,
            'Ipv6Ranges': [
              {'CidrIpv6': add_subnet,'Description': description_filter}
            ]
          }
        ]
      )

  for remove_subnet in remove_subnets:
    if ':' not in remove_subnet:
      client.revoke_security_group_egress(
        GroupId=security_group_id,
        IpPermissions=[
          {
            'IpProtocol': 'tcp',
            'FromPort': 25,
            'ToPort': 25,
            'IpRanges': [
              {'CidrIp': remove_subnet}
            ]
          }
        ]
      )

  for remove_subnet in remove_subnets:
    if ':' in remove_subnet:
      client.revoke_security_group_egress(
        GroupId=security_group_id,
        IpPermissions=[
          {
            'IpProtocol': 'tcp',
            'FromPort': 25,
            'ToPort': 25,
            'Ipv6Ranges': [
              {'CidrIpv6': remove_subnet}
            ]
          }
        ]
      )

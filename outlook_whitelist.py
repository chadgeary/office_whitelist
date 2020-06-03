import botocore
import boto3
import os
import urllib3
import json

def lambda_handler(event, context):

  # fetch o365 as json
  o365_list_url = 'https://endpoints.office.com/endpoints/worldwide?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7'
  http = urllib3.PoolManager()
  o365_raw = http.request('GET', o365_list_url)
  print(o365_raw.status)
  o365_json = json.loads(o365_raw.data.decode('utf-8'))

  # filter on outlook_address from all o365
  outlook_address = '*.mail.protection.outlook.com'
  outlook_json = list(filter(lambda key: key.get('urls',None) == [outlook_address], o365_json))

  # find subnets in outlook_json
  for json_data in outlook_json:
    for key, value in json_data.items():
      if key == 'ips':
        outlook_subnets = value

  print("outlook: " + '[%s]' % ', '.join(map(str,outlook_subnets)))

  # connect to aws
  resource = boto3.resource("ec2")

  # fetch security group via id
  security_group_id = os.environ['SECURITY_GROUP_ID']
  security_group = resource.SecurityGroup(security_group_id)

  # filter on smtp (port 25) from all egress
  smtp_egress = list(filter(lambda rule: rule.get("IpProtocol",None) == "tcp" and rule["FromPort"] == 25 and rule["ToPort"] == 25, security_group.ip_permissions_egress))

  # find subnets in smtp_egress
  existing_subnets = []
  existing_subnetsv6 = []
  for json_data in smtp_egress:
    for key, value in json_data.items():
      if key == 'IpRanges':
        existing_subnets = value
      elif key == 'Ipv6Ranges':
        existing_subnetsv6 = value

  # filter existing_subnets on matching description
  description_filter = 'lambda_o365outlook_whitelist'
  existing_subnets = list(filter(lambda rule: rule.get("Description",None) == description_filter, existing_subnets))
  filtered_subnets = []
  filtered_subnetsv6 = []
  for json_data in existing_subnets:
    for key, value in json_data.items():
      if key == 'CidrIp':
        filtered_subnets.append(value)
  for json_data in existing_subnetsv6:
    for key, value in json_data.items():
      if key == 'CidrIpv6':
        filtered_subnetsv6.append(value)

  print("existing: " + '[%s]' % ', '.join(map(str, filtered_subnets)))

  # subnets to be added and removed
  add_subnets = [outlook_subnet for outlook_subnet in outlook_subnets if (outlook_subnet not in filtered_subnets) and (':' not in outlook_subnet) ]
  add_subnetsv6 = [outlook_subnet for outlook_subnet in outlook_subnets if (outlook_subnet not in filtered_subnetsv6) and (':' in outlook_subnet) ]
  remove_subnets = [filtered_subnet for filtered_subnet in filtered_subnets if filtered_subnet not in outlook_subnets]
  remove_subnetsv6 = [filtered_subnetv6 for filtered_subnetv6 in filtered_subnetsv6 if filtered_subnetv6 not in outlook_subnets]

  print("adding: " + '[%s]' % ', '.join(map(str, add_subnets)) + '[%s]' % ', '.join(map(str, add_subnetsv6)))
  print("removing: " + '[%s]' % ', '.join(map(str, remove_subnets)) + '[%s]' % ', '.join(map(str, remove_subnetsv6)))

  # perform adds and removes
  client = boto3.client('ec2')
  for add_subnet in add_subnets:
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

  for add_subnetv6 in add_subnetsv6:
    client.authorize_security_group_egress(
      GroupId=security_group_id,
      IpPermissions=[
        {
          'IpProtocol': 'tcp',
          'FromPort': 25,
          'ToPort': 25,
          'Ipv6Ranges': [
            {'CidrIpv6': add_subnetv6,'Description': description_filter}
          ]
        }
      ]
    )

  for remove_subnet in remove_subnets:
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

  for remove_subnetv6 in remove_subnetsv6:
    client.revoke_security_group_egress(
      GroupId=security_group_id,
      IpPermissions=[
        {
          'IpProtocol': 'tcp',
          'FromPort': 25,
          'ToPort': 25,
          'Ipv6Ranges': [
            {'CidrIpv6': remove_subnetv6}
          ]
        }
      ]
    )

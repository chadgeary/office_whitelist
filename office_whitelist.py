import botocore
import boto3
import os
import urllib3
import json

def lambda_handler(event, context):

  # build web connection pool
  http = urllib3.PoolManager()

  # fetch owl_endpoints_url as json
  owl_endpoints_url = os.environ['OWL_ENDPOINTS_URL']
  owl_endpoints_raw = http.request('GET', owl_endpoints_url)
  owl_endpoints_json = json.loads(owl_endpoints_raw.data.decode('utf-8'))
  print("endpoints_fetch_response: " + str(owl_endpoints_raw.status))

  # filter on owl_service_url
  owl_service_url = os.environ['OWL_SERVICE_URL']
  owl_service_json = list(filter(lambda key: key.get('urls',None) == [owl_service_url], owl_endpoints_json))
  print("service_url: " + owl_service_url)

  # find subnets in owl_service_json
  for json_data in owl_service_json:
    for key, value in json_data.items():
      if key == 'ips':
        owl_service_subnets = value
  print("service_subnets: " + '[%s]' % ', '.join(map(str,owl_service_subnets)))

  # define ec2 resource (for security group data)
  resource = boto3.resource("ec2")

  # fetch security group via id
  security_group_id = os.environ['SECURITY_GROUP_ID']
  security_group = resource.SecurityGroup(security_group_id)

  # filter on owl_port_protocol and owl_port_number from all egress
  owl_port_protocol = os.environ['OWL_PORT_PROTOCOL']
  owl_port_number = int(os.environ['OWL_PORT_NUMBER'])
  sg_egress = list(filter(lambda rule: rule.get("IpProtocol",None) == owl_port_protocol and rule["FromPort"] == owl_port_number and rule["ToPort"] == owl_port_number, security_group.ip_permissions_egress))

  # find subnets in sg_egress
  existing_subnets = []
  existing_subnetsv6 = []
  for json_data in sg_egress:
    for key, value in json_data.items():
      if key == 'IpRanges':
        existing_subnets = value
      elif key == 'Ipv6Ranges':
        existing_subnetsv6 = value

  # filter existing_subnets on matching description
  owl_rule_description = os.environ['OWL_RULE_DESCRIPTION']
  existing_subnets = list(filter(lambda rule: rule.get("Description",None) == owl_rule_description, existing_subnets))
  existing_subnetsv6 = list(filter(lambda rule: rule.get("Description",None) == owl_rule_description, existing_subnetsv6))

  # split existing subnets to ipv4 and ipv6
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

  print("Found existing subnets matching egress port_protocol: {} + port_number: {} + description: {}".format(owl_port_protocol, str(owl_port_number), owl_rule_description))
  print('[%s]' % ', '.join(map(str, filtered_subnets)) + '[%s]' % ', '.join(map(str, filtered_subnetsv6)))

  # define ec2 client (for security group rule manipulation)
  client = boto3.client('ec2')

  # add ipv4
  add_subnets = [owl_service_subnet for owl_service_subnet in owl_service_subnets if (owl_service_subnet not in filtered_subnets) and (':' not in owl_service_subnet) ]
  print("adding v4: " + '[%s]' % ', '.join(map(str, add_subnets)))

  for add_subnet in add_subnets:
    client.authorize_security_group_egress(
      GroupId=security_group_id,
      IpPermissions=[
        {
          'IpProtocol': 'tcp',
          'FromPort': 25,
          'ToPort': 25,
          'IpRanges': [
            {'CidrIp': add_subnet,'Description': owl_rule_description}
          ]
        }
      ]
    )

  # add ipv6
  add_subnetsv6 = [owl_service_subnet for owl_service_subnet in owl_service_subnets if (owl_service_subnet not in filtered_subnetsv6) and (':' in owl_service_subnet)]
  print("adding v6: " + '[%s]' % ', '.join(map(str, add_subnetsv6)))

  for add_subnetv6 in add_subnetsv6:
    client.authorize_security_group_egress(
      GroupId=security_group_id,
      IpPermissions=[
        {
          'IpProtocol': 'tcp',
          'FromPort': 25,
          'ToPort': 25,
          'Ipv6Ranges': [
            {'CidrIpv6': add_subnetv6,'Description': owl_rule_description}
          ]
        }
      ]
    )

  # remove ipv4
  remove_subnets = [filtered_subnet for filtered_subnet in filtered_subnets if filtered_subnet not in owl_service_subnets]
  print("removing v4: " + '[%s]' % ', '.join(map(str, remove_subnets)))

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

  # remove ipv6
  remove_subnetsv6 = [filtered_subnetv6 for filtered_subnetv6 in filtered_subnetsv6 if filtered_subnetv6 not in owl_service_subnets]
  print("removing v6: " + '[%s]' % ', '.join(map(str, remove_subnetsv6)))

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

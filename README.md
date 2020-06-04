# Reference
AWS lambda function w/ IAM policy/role to:
1. fetch Microsoft's office365 endpoint list
2. match on endpoint url/port
3. update a security group's egress to permit access (permit new + revoke old)

# Notes
- Requires/uses Terraform (must be pre-installed).
- Requires/uses AWS credentials provided by environment.
- Defaults assume target egress is outlook (SMTP 25/tcp).

# Deploy
```
# begin terraform
terraform init
terraform apply

# answer terraform variables
var.aws_profile
  Enter a value: default

var.aws_region
  Enter a value: us-east-2

var.owl_group_id
  Enter a value: sg-12345678
```

# Output Example
```
START RequestId: 4a087cdc-e363-15fc-bd2d-fe251241e9f1 Version: $LATEST
endpoints_fetch_response: 200
service_url: *.mail.protection.outlook.com
service_subnets: [40.92.0.0/15, 40.107.0.0/16, 52.100.0.0/14, 104.47.0.0/17, 2a01:111:f400::/48, 2a01:111:f403::/48]
Found existing subnets matching egress port_protocol: tcp + port_number: 25 + description: OWL_OUTLOOK
[40.92.0.0/15, 40.107.0.0/16, 104.47.0.0/17, 52.100.0.0/14, 172.16.4.0/23][2a01:111:f400::/48]
adding v4: []
adding v6: [2a01:111:f403::/48]
removing v4: [172.16.4.0/23]
removing v6: []
END RequestId: 4a087cdc-e363-15fc-bd2d-fe251241e9f1
REPORT RequestId: 4a087cdc-e363-15fc-bd2d-fe251241e9f1	Duration: 4465.68 ms	Billed Duration: 4500 ms	Memory Size: 128 MB	Max Memory Used: 78 MB	Init Duration: 158.83 ms	
```

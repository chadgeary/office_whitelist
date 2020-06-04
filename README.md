# Reference
AWS lambda function w/ IAM policy/role to:
1. fetch Microsoft's office365 endpoint list
2. match on endpoint url/port
3. update a security group's egress to permit access (permit new + revoke old)

- Builds via terraform.
- Defaults assume target egress is outlook 25/tcp (SMTP).

# Requires
- Terraform installed.
- AWS credentials provided by environment.

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
Function Logs:
START RequestId: c21b8f95-e506-4a1f-8a24-dd1431877501 Version: $LATEST
200
outlook: [40.92.0.0/15, 40.107.0.0/16, 52.100.0.0/14, 104.47.0.0/17, 2a01:111:f400::/48, 2a01:111:f403::/48]
existing: [40.107.0.0/16, 104.47.0.0/17, 52.100.0.0/14, 169.254.0.0/24]
adding: [40.92.0.0/15][2a01:111:f403::/48]
removing: [169.254.0.0/24][]
END RequestId: c21b8f95-e506-4a1f-8a24-dd1431877501
REPORT RequestId: c21b8f95-e506-4a1f-8a24-dd1431877501	Duration: 4607.93 ms	Billed Duration: 4700 ms	Memory Size: 128 MB	Max Memory Used: 77 MB	Init Duration: 168.71 ms	
```

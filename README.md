# Reference
AWS lambda & associated IAM policy/role to fetch Microsoft's office365 SMTP server subnets and update a security group (to permit smtp [tcp/25]). Uses terraform.

# Requires
- terraform installed
- AWS credentials provided by environment

# Deploy
```
terraform init
terraform apply
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

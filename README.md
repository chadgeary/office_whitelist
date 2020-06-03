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

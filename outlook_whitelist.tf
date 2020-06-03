# A terraform configuration for a lambda function (and the associated IAM role)
# to fetch microsoft office365 outlook smtp servers
# then update a security group's egress to permit 25/tcp (SMTP)
# for those subnets

variable "aws_region" {
  type                     = string
}

variable "aws_profile" {
  type                     = string
}

provider "aws" {
  region                   = var.aws_region
  profile                  = var.aws_profile
}

variable "owl_group_id" {
  type                     = string
}

data "aws_security_group" "owl_sg" {
  id                         = var.owl_group_id
}

data "aws_iam_policy_document" "owl_pdoc" {
  statement {
    sid                      = "1"
    actions                  = [
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
      "ec2:DescribeSecurityGroups",
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources                = [
      "*"
    ]
  }
}

resource "aws_iam_policy" "owl_policy" {
  name                     = "outlook_whitelist"
  path                     = "/"
  policy                   = data.aws_iam_policy_document.owl_pdoc.json
}

resource "aws_iam_role" "owl_iamrole" {
  name                     = "outlook_whitelist"
  path                     = "/"  
  assume_role_policy       = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_policy_attachment" "owl_policy_attach" {
  name                     = "outlook_whitelist"
  roles                    = [aws_iam_role.owl_iamrole.name]
  policy_arn               = aws_iam_policy.owl_policy.arn
}

resource "aws_lambda_function" "owl_lambda" {
  filename                 = "outlook_whitelist.zip"
  function_name            = "outlook_whitelist"
  role                     = aws_iam_role.owl_iamrole.arn
  handler                  = "outlook_whitelist.lambda_handler"
  source_code_hash         = filebase64sha256("outlook_whitelist.zip")
  runtime                  = "python3.6"
  timeout                  = 60
  environment {
    variables                = {
      SECURITY_GROUP_ID        = var.owl_group_id
    }
  }
}

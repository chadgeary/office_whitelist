# A terraform configuration for a lambda function (and the associated IAM role)
# to fetch microsoft office365 outlook smtp servers and update a security group

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

variable "o365_group_id" {
  type                     = string
}

variable "lambda_group_id" {
  type                     = string
}

variable "lambda_subnet_id" {
  type                     = string
}

data "aws_security_group" "o365_sg" {
  id                         = var.o365_group_id
}

data "aws_security_group" "lambda_sg" {
  id                         = var.lambda_group_id
}

data "aws_iam_policy_document" "o365_pdoc" {
  statement {
    sid                      = "1"
    actions                  = [
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:DescribeSecurityGroups"
    ]
    resources                = [
      data.aws_security_group.o365_sg.arn
    ]
  }
  statement {
    sid                      = "2"
    actions                  = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources                = [
      "*"
    ]
  }
}

resource "aws_iam_policy" "o365_policy" {
  name                     = "lambda_o365outlook_whitelist"
  path                     = "/"
  policy                   = data.aws_iam_policy_document.o365_pdoc.json
}

resource "aws_iam_role" "o365_iamrole" {
  name                     = "lambda_o365outlook_whitelist"
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

resource "aws_iam_policy_attachment" "o365_policy_attach" {
  name                     = "lambda_o365outlook_whitelist"
  roles                    = [aws_iam_role.o365_iamrole.name]
  policy_arn               = aws_iam_policy.o365_policy.arn
}

resource "aws_lambda_function" "o365_lambda" {
  filename                 = "lambda_o365outlook_whitelist.zip"
  function_name            = "lambda_o365outlook_whitelist"
  role                     = aws_iam_role.o365_iamrole.arn
  handler                  = "lambda_o365outlook_whitelist.lambda_handler"
  source_code_hash         = filebase64sha256("lambda_o365outlook_whitelist.zip")
  runtime                  = "python3.6"
  timeout                  = 60
  vpc_config {
    security_group_ids       = [var.lambda_group_id]
    subnet_ids               = [var.lambda_subnet_id]
  }
  environment {
    variables                = {
      SECURITY_GROUP_ID        = var.o365_group_id
    }
  }
}

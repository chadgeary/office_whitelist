# A terraform configuration for a lambda function (and the associated IAM role)
# to fetch microsoft office365 web endpoints
# then update a security group's egress to permit access (e.g. mail.protection.outlook.com smtp 25/tcp)
# with the fetched subnets

# defaults assume outlook 25/tcp (SMTP)
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

variable "owl_event_schedule" {
  type                     = string
  default                  = "cron(0 0 * * ? *)"
}

variable "owl_endpoints_url" {
  type                     = string
  default                  = "https://endpoints.office.com/endpoints/worldwide?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7"
}

variable "owl_service_url" {
  type                     = string
  default                  = "*.mail.protection.outlook.com"
}

variable "owl_rule_description" {
  type                     = string
  default                  = "OWL_OUTLOOK"
}

variable "owl_port_number" {
  type                     = string
  default                  = "25"
}

variable "owl_port_protocol" {
  type                     = string
  default                  = "tcp"
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
    ]
    resources                = [
      data.aws_security_group.owl_sg.arn
    ]
  }
  statement {
    sid                      = "2"
    actions                  = [
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
  name                     = "office_whitelist"
  path                     = "/"
  policy                   = data.aws_iam_policy_document.owl_pdoc.json
}

resource "aws_iam_role" "owl_iamrole" {
  name                     = "office_whitelist"
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
  name                     = "office_whitelist"
  roles                    = [aws_iam_role.owl_iamrole.name]
  policy_arn               = aws_iam_policy.owl_policy.arn
}

resource "aws_lambda_function" "owl_lambda" {
  filename                 = "office_whitelist.zip"
  function_name            = "office_whitelist"
  role                     = aws_iam_role.owl_iamrole.arn
  handler                  = "office_whitelist.lambda_handler"
  source_code_hash         = filebase64sha256("office_whitelist.zip")
  runtime                  = "python3.6"
  timeout                  = 60
  environment {
    variables                = {
      SECURITY_GROUP_ID        = var.owl_group_id
      OWL_ENDPOINTS_URL        = var.owl_endpoints_url
      OWL_SERVICE_URL          = var.owl_service_url
      OWL_PORT_PROTOCOL        = var.owl_port_protocol
      OWL_PORT_NUMBER          = var.owl_port_number
      OWL_RULE_DESCRIPTION     = var.owl_rule_description
    }
  }
}

resource "aws_cloudwatch_event_rule" "owl_cloudwatch_event_rule" {
  name                     = "office_whitelist"
  description              = "Triggers the office_whitelist lambda"
  schedule_expression      = var.owl_event_schedule
}

resource "aws_cloudwatch_event_target" "owl_cloudwatch_event_target" {
  rule                     = aws_cloudwatch_event_rule.owl_cloudwatch_event_rule.name
  target_id                = aws_lambda_alias.owl_lambda_alias.name
  arn                      = aws_lambda_alias.owl_lambda_alias.arn
}

resource "aws_lambda_permission" "owl_lambda_allow_cloudwatch" {
  statement_id             = "AWSEvents_office_whitelist_office_whitelist_alias"
  action                   = "lambda:InvokeFunction"
  function_name            = aws_lambda_function.owl_lambda.function_name
  principal                = "events.amazonaws.com"
  source_arn               = aws_cloudwatch_event_rule.owl_cloudwatch_event_rule.arn
  qualifier                = aws_lambda_alias.owl_lambda_alias.name
}

resource "aws_lambda_alias" "owl_lambda_alias" {
  name                     = "office_whitelist_alias"
  description              = "Alias for cloudwatch invoke lambda"
  function_name            = aws_lambda_function.owl_lambda.function_name
  function_version         = "$LATEST"
}

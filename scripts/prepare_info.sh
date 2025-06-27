#!/bin/bash

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get AWS default region
AWS_REGION=$(aws configure get region)

echo "Account ID: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
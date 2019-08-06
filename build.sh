#!/usr/bin/env bash

set -e

REV_TAG=$(git log -1 --pretty=format:%h)

echo "Building image..."
docker build -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${IMAGE_REPO}:${REV_TAG} .
docker build -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${IMAGE_REPO}:latest .

echo "Pushing image"
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${IMAGE_REPO}:${REV_TAG}
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${IMAGE_REPO}:latest

echo "Updating CFN"
aws cloudformation update-stack --stack-name ${STACK_NAME} --use-previous-template --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=FlaskAppImageUrl,ParameterValue=$AWS_ACCOUNT_ID.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${IMAGE_REPO}:${REV_TAG} \
  ParameterKey=S3Location,UsePreviousValue=true \
  ParameterKey=EnvironmentName,UsePreviousValue=true \
  ParameterKey=InstanceType,UsePreviousValue=true \
  ParameterKey=MakeVPCPublic,UsePreviousValue=true \
  ParameterKey=MaxSize,UsePreviousValue=true

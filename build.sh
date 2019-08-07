  ParameterKey=MaxSize,UsePreviousValue=tru2
/web/flask_brain_db/xnat_c9.cf2
#!/usr/bin/env bash

set -e

REV_TAG=$(git log -1 --pretty=format:%h)

cd ./cookiecutter_mbam

echo "Building image..."
docker build -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${IMAGE_REPO}:${REV_TAG} .

echo "Pushing image"
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${IMAGE_REPO}:${REV_TAG}

echo "Updating CFN"
aws cloudformation update-stack --stack-name ${STACK_NAME} --use-previous-template --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=FlaskAppImageUrl,ParameterValue=$AWS_ACCOUNT_ID.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${IMAGE_REPO}:${REV_TAG} \
  ParameterKey=S3Location,UsePreviousValue=true \
  ParameterKey=EnvironmentName,UsePreviousValue=true \
  ParameterKey=InstanceType,UsePreviousValue=true \
  ParameterKey=MakeVPCPublic,UsePreviousValue=true \
  ParameterKey=DesiredCapacity,UsePreviousValue=true \
  ParameterKey=MaxSize,UsePreviousValue=true \

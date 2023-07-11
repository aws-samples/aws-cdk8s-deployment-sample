#!/bin/bash
REPO_NAME=cdk8s-samples
cdk bootstrap aws://$ACCOUNT/$REGION
aws codecommit create-repository --repository-name $REPO_NAME --region $REGION
git remote add origin codecommit::$REGION://$REPO_NAME
git push --set-upstream origin main
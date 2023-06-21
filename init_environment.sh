#!/bin/bash
cdk bootstrap aws://$ACCOUNT/$REGION
aws codecommit create-repository --repository-name $REPO_NAME --region $REGION
git remote add origin codecommit::$REGION://$PROFILE@$REPO_NAME
git push --set-upstream origin main
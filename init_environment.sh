#!/bin/bash
REPO_NAME=cdk8s-samples
python3 -m venv .venv
chmod +x .venv/bin/activate
. .venv/bin/activate
pip3 install -r requirements.txt
cdk bootstrap aws://$ACCOUNT/$REGION
aws codecommit create-repository --repository-name $REPO_NAME --region $REGION
git remote rm origin
git remote add origin codecommit::$REGION://$REPO_NAME
git push --set-upstream origin main
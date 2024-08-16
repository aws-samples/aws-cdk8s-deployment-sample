#!/bin/bash
python3 -m venv .venv
chmod +x .venv/bin/activate
. .venv/bin/activate
pip3 install -r requirements.txt
cdk bootstrap aws://$ACCOUNT/$REGION
git remote rm origin
git remote add origin $GITHUB_URL
git push --set-upstream origin $REPO_BRANCH
#!/usr/bin/env python3
import os
from aws_cdk import App, Environment, Aspects
from cdk_nag import AwsSolutionsChecks, NagSuppressions
from infrastructure.pipeline_stack import PipelineStack

# Get environment configuration
account = os.environ.get('ACCOUNT', None)
region = os.environ.get('REGION', None)
elb_account_id = os.environ.get('ELB_ACCOUNT_ID')
repo_string = os.environ.get('REPO_STRING', 'owner/repo')
repo_branch = os.environ.get('REPO_BRANCH', 'main')
connection_arn = os.environ.get('CONNECTION_ARN')
hosted_zone_id = os.environ.get('HOSTED_ZONE_ID', None)
hosted_zone_name = os.environ.get('HOSTED_ZONE_NAME', None)
record_name = os.environ.get('RECORD_NAME', None)
certificate = os.environ.get('CERTIFICATE', None)

app = App()

pipeline_stack= PipelineStack(
    app,
    "cdk8s-samples-pipeline-stack",
    env = Environment(
        account = os.environ.get('ACCOUNT', None),
        region = os.environ.get('REGION', None)
    ),
    app_name = app.node.try_get_context("appName"),
    elb_account_id = elb_account_id,
    certificate = certificate,
    hosted_zone_id =  hosted_zone_id,
    hosted_zone_name = hosted_zone_name,
    record_name = record_name,
    repo_string = repo_string,
    repo_branch = repo_branch,
    connection_arn = connection_arn
)

Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
NagSuppressions.add_stack_suppressions(
    pipeline_stack,
    [
        {
            "id": "AwsSolutions-CB4",
            "reason": "This is a demo, not production code. KMS for Codebuild is not needed"
        }
    ]
)

app.synth()

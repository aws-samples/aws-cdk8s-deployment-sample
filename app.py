#!/usr/bin/env python3
import os
from aws_cdk import App, Environment, Aspects
from cdk_nag import AwsSolutionsChecks, NagSuppressions
from infrastructure.pipeline_stack import PipelineStack

app = App()

pipeline_stack= PipelineStack(
    app,
    "cdk8s-samples-pipeline-stack",
    env = Environment(
        account = os.environ.get('ACCOUNT', None),
        region = os.environ.get('REGION', None)
    ),
    app_name = app.node.try_get_context("appName")
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

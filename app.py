#!/usr/bin/env python3
import os
from aws_cdk import App, Environment
from infrastructure.pipeline_stack import PipelineStack

app = App()

app_name = app.node.try_get_context("appName")

PipelineStack(
    app,
    "cdk8s-samples-pipeline-stack",
    env = Environment(
        account = os.environ['ACCOUNT'],
        region = os.environ['REGION']
    ),
    app_name = app_name
)

app.synth()

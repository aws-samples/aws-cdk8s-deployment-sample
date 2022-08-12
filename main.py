#!/usr/bin/env python
import os
import sys
from cdk8s import (
    App,
    YamlOutputType
)
from app_chart import AppChart

app = App(yaml_output_type = YamlOutputType.FOLDER_PER_CHART_FILE_PER_RESOURCE)

env_vars = ['ACCOUNT','REGION','NAMESPACE','RECORD','CERTIFICATE']
account = os.getenv(env_vars[0])
region = os.getenv(env_vars[1])
namespace = os.getenv(env_vars[2])
record = os.getenv(env_vars[3])
certificate = f"arn:aws:acm:{region}:{account}:certificate/{os.getenv(env_vars[4])}"

for env in env_vars:
    if os.getenv(env) is None:
        sys.exit("\033[91m\nERRORR: You you need to setup all the requested environment variables\n\033[0m")

AppChart(app, "cdk8s-test", account, region, namespace, record, certificate)

app.synth()

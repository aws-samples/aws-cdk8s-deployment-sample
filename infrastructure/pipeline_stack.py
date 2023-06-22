from constructs import Construct
from aws_cdk import Stack
from aws_cdk.aws_codecommit import Repository
from aws_cdk.pipelines import (
    CodePipeline,
    CodePipelineSource,
    ShellStep
)
#from aws_cdk.aws_codebuild import (
#    BuildEnvironment,
#    LinuxBuildImage,
#    ComputeType
#)
from .deploy_stage import DeployStage

class PipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, app_name: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        repository = Repository.from_repository_arn(
            self,
            "CodeCommitRepo",
            f'arn:aws:codecommit:{self.region}:{self.account}:{app_name}'
        )

        source_stage = CodePipelineSource.code_commit(
            repository,
            "main"
        )

        pipeline = CodePipeline(
            self,
            "Pipeline",
            pipeline_name = f"{app_name}-pipeline",
            self_mutation = True,
            synth = ShellStep(
                "Synth",
                input = source_stage,
                env={
                    "ACCOUNT" : self.account,
                    "REGION": self.region
                },
                install_commands=[
                    "npm install -g aws-cdk",
                    "python3 -m venv .env",
                    "chmod +x .env/bin/activate",
                    ". .env/bin/activate",
                    "pip3 install -r requirements.txt",
                    "pip3 install -r requirements-dev.txt"
                    ],
                commands=[
                    "cdk synth"
                ]
            )
        )

        pipeline.add_stage(
            DeployStage(
                self,
                'QA',
                app_name = app_name
            ),
            pre = []
        )

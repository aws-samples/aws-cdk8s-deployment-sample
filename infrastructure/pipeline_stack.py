from constructs import Construct
from aws_cdk import Stack
from aws_cdk.aws_codecommit import Repository
from aws_cdk.pipelines import (
    CodePipeline,
    CodePipelineSource,
    ShellStep,
    CodeBuildStep
)
from aws_cdk.aws_codebuild import (
    BuildEnvironment,
    LinuxBuildImage,
    ComputeType
)
from aws_cdk.aws_codebuild import BuildSpec
from .deploy_stage import DeployStage

class PipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, app_name: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        repository = Repository.from_repository_arn(
            self,
            "CodeCommitRepo",
            f'arn:aws:codecommit:{self.region}:{self.account}:{app_name}'
        )

        cdk_install_commands =  ["npm install -g aws-cdk",
            "python3 -m venv .env",
            "chmod +x .env/bin/activate",
            ". .env/bin/activate",
            "pip3 install -r requirements.txt",
            "pip3 install -r requirements-dev.txt"
        ]

        source_stage = CodePipelineSource.code_commit(
            repository,
            "main"
        )

        environment = BuildEnvironment(
            build_image = LinuxBuildImage.STANDARD_7_0,
            compute_type = ComputeType.SMALL
        )

        pylint_step = CodeBuildStep(
            "Linter",
            input = source_stage,
            build_environment = environment,
            project_name = f"{app_name}-pipeline-linter",
            install_commands = cdk_install_commands,
            commands = [
                "find . -name '*.py' ! -path './.env/*' ! -path './cdk.out/*' ! -path './node_modules/*' | xargs pylint"
            ]
        )

        pytest_step = CodeBuildStep(
            "UnitTests",
            input = source_stage,
            build_environment = environment,
            project_name = f"{app_name}-pipeline-unit-tests",
            install_commands = cdk_install_commands,
            commands = [
                "coverage erase && python3 -m coverage run --branch -m pytest -v && coverage report",
                "python3 -m coverage xml -i -o test-results/coverage.xml",
                "python3 -m pytest --junitxml=test-results/results.xml"
            ],
            partial_build_spec = BuildSpec.from_object({
                "reports": {
                    "unit_tests_reports": {
                        "files": "results.xml",
                        "base-directory": "test-results",
                        "file-format": "JUNITXML"
                    },
                    "coverage_reports": {
                        "files": "coverage.xml",
                        "base-directory": "test-results",
                        "file-format": "COBERTURAXML"
                    }
                }
            })
        )

        pipeline = CodePipeline(
            self,
            "Pipeline",
            pipeline_name = f"{app_name}-pipeline",
            self_mutation = True,
            synth = ShellStep(
                "Synth",
                input = source_stage,
                env = {
                    "ACCOUNT" : self.account,
                    "REGION": self.region
                },
                install_commands = cdk_install_commands,
                commands = [
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
            pre = [
                pylint_step,
                pytest_step
            ]
        )

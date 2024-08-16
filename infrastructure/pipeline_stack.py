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
from cdk_nag import NagSuppressions
from .deploy_stage import DeployStage

class PipelineStack(Stack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            app_name: str,
            elb_account_id: str,
            certificate: str,
            hosted_zone_id: str,
            hosted_zone_name: str,
            record_name: str,
            repo_string: str,
            connection_arn: str,
            repo_branch: str,
            **kwargs
        ):
        super().__init__(scope, id, **kwargs)

        cdk_install_commands =  [
            "npm install -g aws-cdk",
            "pip3 install -r requirements.txt",
            "pip3 install -r requirements-dev.txt"
        ]

        source_stage = CodePipelineSource.connection(
            repo_string = repo_string,
            branch = repo_branch,
            connection_arn = connection_arn,
            action_name = "Github_Source",
            code_build_clone_output = True
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
                "find . -name '*.py' ! -path './cdk.out/*' ! -path './node_modules/*' | xargs pylint"
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

        env_vars = {
            "ACCOUNT" : self.account,
            "REGION": self.region,
            "ELB_ACCOUNT_ID": elb_account_id,
        }

        if hosted_zone_name is not None:
            env_vars["HOSTED_ZONE_ID"] = hosted_zone_id

        if hosted_zone_name is not None:
            env_vars["HOSTED_ZONE_NAME"] = hosted_zone_name

        if record_name is not None:
            env_vars["RECORD_NAME"] = record_name

        if certificate is not None:
            env_vars["CERTIFICATE"] = certificate
        pipeline = CodePipeline(
            self,
            "Pipeline",
            pipeline_name = f"{app_name}-pipeline",
            self_mutation = True,
            synth = ShellStep(
                "Synth",
                input = source_stage,
                env = env_vars,
                install_commands = cdk_install_commands,
                commands = [
                    "cdk synth"
                ]
            )
        )

        safety_step = CodeBuildStep(
            "Safety",
            input = source_stage,
            build_environment = environment,
            project_name = f"{app_name}-pipeline-safety",
            install_commands = cdk_install_commands,
            commands = [
                "find requirements*.txt -execdir safety check -r {} \;"
            ]
        )

        bandit_step = CodeBuildStep(
            "Bandit",
            input = source_stage,
            build_environment = environment,
            project_name = f"{app_name}-pipeline-bandit",
            install_commands = cdk_install_commands,
            commands = [
                "bandit -r ."
            ]
        )

        git_leaks_step = CodeBuildStep(
            "GitLeaks",
            input = source_stage,
            build_environment = environment,
            project_name = f"{app_name}-pipeline-git-leaks",
            install_commands = cdk_install_commands,
            commands = [
                "CURRENT_DIR=$(pwd)",
                "CLONE_FOLDER=gitleaks",
                "mkdir $CLONE_FOLDER",
                "git clone --quiet https://github.com/gitleaks/gitleaks.git $CLONE_FOLDER",
                "cd $CLONE_FOLDER",
                "make build",
                "chmod +x gitleaks",
                "mv gitleaks /usr/local/bin/",
                "cd $CURRENT_DIR && rm -rf $CLONE_FOLDER",
                "gitleaks detect --source . -v"
            ]
        )

        pipeline.add_stage(
            DeployStage(
                self,
                'DEV',
                app_name = app_name,
                elb_account_id = elb_account_id,
                certificate = certificate,
                hosted_zone_id =  hosted_zone_id,
                hosted_zone_name = hosted_zone_name,
                record_name = record_name
            ),
            pre = [
                safety_step,
                bandit_step,
                git_leaks_step,
                pylint_step,
                pytest_step
            ]
        )

        # Force the pipeline construct creation forward before applying suppressions.
        pipeline.build_pipeline()

        # CDK-NAG supressions
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            "/cdk8s-samples-pipeline-stack/Pipeline/Pipeline/ArtifactsBucket/Resource",
            [
                {
                    "id": "AwsSolutions-S1",
                    "reason": "S3 bucket automatically created by CDK, I have no control on it on the configuration"
                }
            ]
        )

        for subpath in ["Assets/FileRole","UpdatePipeline/SelfMutation/Role", "Pipeline/Role","Pipeline/Build/Synth/CdkBuildProject/Role", "Pipeline/Source/cdk8s-samples/CodePipelineActionRole"]:
            NagSuppressions.add_resource_suppressions_by_path(
                self,
                f"/cdk8s-samples-pipeline-stack/Pipeline/{subpath}/DefaultPolicy/Resource",
                [
                    {
                        "id": "AwsSolutions-IAM5",
                        "reason": "Automatically generated by CDK, I have no control on it to modify it",
                        "applies_to": [
                            'Action::s3:*',
                        ]
                    }
                ]
            )


        NagSuppressions.add_resource_suppressions(
            [
                git_leaks_step.project,
                bandit_step.project,
                pytest_step.project,
                pylint_step.project,
                safety_step.project
            ],
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": 'This is added automatically by CDK, I cannot controll it',
                    "applies_to": [
                        'Action::s3:*',
                    ],
                },
            ],
            True
        )

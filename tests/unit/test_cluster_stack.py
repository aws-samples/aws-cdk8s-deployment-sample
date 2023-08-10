import random
from aws_cdk import App, Environment
from aws_cdk.assertions import Template, Match
from infrastructure.cluster_stack import KubernetesClusterStack

REGION = "us-east-1"
ACCOUNT = str(random.randint(111111111111, 999999999999))
K8S_VERSION = "1.26"
APP_NAME = "cdk8s-samples"

context_mock = {
    "region": REGION,
    "account": ACCOUNT,
    "appName": APP_NAME,
    "adminRoles": [
        "MockRole"
    ],
    "adminUsers": [
        "MockUser"
    ]
}

app = App(context=context_mock)
app_name = app.node.try_get_context("appName")


stack = KubernetesClusterStack(
    app,
    f"{app_name}-app-stack",
    env=Environment(
        account=ACCOUNT,
        region=REGION
    ),
    admin_users=[],
    admin_roles=app.node.try_get_context("adminRoles")
)

template = Template.from_stack(stack)


def test_eks_cluster():
    template.has_resource_properties(
        "Custom::AWSCDK-EKS-Cluster",
        {
            "ServiceToken": {
                "Fn::GetAtt": [
                    Match.any_value(),
                    Match.any_value()
                ]
            },
            "Config": {
                "name": APP_NAME,
                "version": K8S_VERSION,
                "roleArn": {
                    "Fn::GetAtt": [
                        Match.any_value(),
                        "Arn"
                    ]
                },
                "kubernetesNetworkConfig": {
                    "ipFamily": "ipv4"
                },
                "resourcesVpcConfig": {
                    "subnetIds": [
                        {
                            "Ref": Match.any_value()
                        },
                        {
                            "Ref": Match.any_value()
                        },
                        {
                            "Ref": Match.any_value()
                        },
                        {
                            "Ref": Match.any_value()
                        },
                        {
                            "Ref": Match.any_value()
                        },
                        {
                            "Ref": Match.any_value()
                        }
                    ],
                    "securityGroupIds": [
                        {
                            "Fn::GetAtt": [
                                Match.any_value(),
                                "GroupId"
                            ]
                        }
                    ],
                    "endpointPublicAccess": True,
                    "endpointPrivateAccess": True
                }
            },
            "AssumeRoleArn": {
                "Fn::GetAtt": [
                    Match.any_value(),
                    "Arn"
                ]
            },
            "AttributesRevision": 2
        }
    )
    template.has_resource_properties(
        "Custom::AWSCDKOpenIdConnectProvider",
        {
            "ServiceToken": {
                "Fn::GetAtt": [
                    Match.any_value(),
                    "Arn"
                ]
            },
            "ClientIDList": [
                "sts.amazonaws.com"
            ],
            "Url": {
                "Fn::GetAtt": [
                    Match.any_value(),
                    Match.any_value()
                ]
            },
            "CodeHash": Match.any_value()
        }
    )

    template.has_resource_properties(
        "Custom::AWSCDK-EKS-FargateProfile",
        {
            "ServiceToken": {
                "Fn::GetAtt": [
                    Match.any_value(),
                    Match.any_value()
                ]
            },
            "AssumeRoleArn": {
                "Fn::GetAtt": [
                    Match.any_value(),
                    "Arn"
                ]
            },
            "Config": {
                "clusterName": {
                    "Ref": Match.any_value()
                },
                "podExecutionRoleArn": {
                    "Fn::GetAtt": [
                        Match.any_value(),
                        "Arn"
                    ]
                },
                "selectors": [
                    {
                        "namespace": "default"
                    },
                    {
                        "namespace": "kube-system"
                    }
                ]
            }
        }
    )

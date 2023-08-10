from typing import Sequence
from constructs import Construct
from aws_cdk import Stack, CfnOutput
from aws_cdk.aws_eks import (
    FargateCluster,
    AlbControllerOptions,
    AlbControllerVersion,
    KubernetesVersion,
    AlbScheme
)
from aws_cdk.aws_iam import Role, User
from aws_cdk.lambda_layer_kubectl_v26 import KubectlV26Layer
from cdk8s import App as Ck8sApp
from .app_chart import AppChart

class KubernetesClusterStack(Stack):
    def __init__(self, scope: Construct, id: str, admin_users: Sequence[str], admin_roles: Sequence[str], **kwargs):
        super().__init__(scope, id, **kwargs)

        # EKS Cluster
        self.cluster = FargateCluster(
            self,
            "EKSCluster",
            cluster_name = "cdk8s-samples",
            # Install ALB Ingress Controller
            alb_controller = AlbControllerOptions(
                version = AlbControllerVersion.V2_5_1
            ),
            version = KubernetesVersion.V1_26,
            kubectl_layer = KubectlV26Layer(self, "Kubectl")
        )

        # Cdk8s resources
        #app_chart = AppChart(
        #    Ck8sApp(),
        #    "AppChart",
        #    namespace = "default"
        #)
#
        #added_chart = self.cluster.add_cdk8s_chart(
        #    "AppChart",
        #    app_chart,
        #    # Expose via internet-facing ALB
        #    ingress_alb = True,
        #    ingress_alb_scheme = AlbScheme.INTERNET_FACING
        #)

        # Add IAM users to cluster
        for username in admin_users:
            arn = f'arn:aws:iam::{self.account}:user/{username}'
            self.cluster.aws_auth.add_user_mapping(
                user = User.from_user_arn(self, username, arn),
                groups = [
                    "system:masters"
                ]
            )

        # Add IAM roles to cluster
        for role_name in admin_roles:
            arn = f'arn:aws:iam::{self.account}:role/{role_name}'
            role = Role.from_role_arn(self, f"{role_name}Role", arn, mutable=False)
            self.cluster.aws_auth.add_masters_role(role)

        # The deletion of `app_chart` is what instructs the controller to delete the ELB.
        # So we need to make sure this happens before the controller is deleted.
        #added_chart.node.add_dependency(self.cluster.alb_controller)

        alb_dns = self.cluster.get_ingress_load_balancer_address(app_chart.ingress.name)

        # Return ALB Public DNS in stack outputs
        #CfnOutput(
        #    self,
        #    "ApplicationEndpoint",
        #    value=f"http://{alb_dns}"
        #)

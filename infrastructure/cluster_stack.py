from typing import Sequence
from constructs import Construct
from aws_cdk import Stack, CfnOutput, RemovalPolicy
from aws_cdk.aws_eks import (
    FargateCluster,
    AlbControllerOptions,
    AlbControllerVersion,
    KubernetesVersion,
    AlbScheme,
    ClusterLoggingTypes,
    EndpointAccess
)
from aws_cdk.aws_iam import Role, User
from aws_cdk.aws_s3 import Bucket, BlockPublicAccess, BucketEncryption
from aws_cdk.aws_iam import PolicyStatement, AccountPrincipal
from aws_cdk.aws_route53 import CnameRecord, HostedZone
from aws_cdk.lambda_layer_kubectl_v28 import KubectlV28Layer
from cdk8s import App as Ck8sApp
from .app_chart import AppChart

class KubernetesClusterStack(Stack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            admin_users: Sequence[str],
            admin_roles: Sequence[str],
            elb_account_id: str,
            certificate: str,
            hosted_zone_id: str,
            hosted_zone_name: str,
            record_name: str,
            **kwargs
        ):

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
            # Add logging
            cluster_logging=[
                ClusterLoggingTypes.API,
                ClusterLoggingTypes.AUDIT,
                ClusterLoggingTypes.AUTHENTICATOR,
                ClusterLoggingTypes.CONTROLLER_MANAGER,
                ClusterLoggingTypes.SCHEDULER
            ],
            # Make the endpoint private
            endpoint_access=EndpointAccess.PRIVATE,
            version = KubernetesVersion.V1_28,
            kubectl_layer = KubectlV28Layer(self, "Kubectl")
        )

        logs_bucket = Bucket(
            self,
            "Bucket",
            block_public_access=BlockPublicAccess.BLOCK_ALL,
            encryption=BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
            versioned=True
        )

        logs_bucket.add_to_resource_policy(
            PolicyStatement(
                actions=[
                    "s3:PutObject"
                ],
                resources=[
                    f"{logs_bucket.bucket_arn}/*"
                ],
                principals=[
                    AccountPrincipal(elb_account_id)
                ]
            )
        )

        # Cdk8s resources
        app_chart = AppChart(
            Ck8sApp(),
            "AppChart",
            namespace = "default",
            alb_access_logs_bucket_name = logs_bucket.bucket_name,
            certificate = certificate
        )

        added_chart = self.cluster.add_cdk8s_chart(
            "AppChart",
            app_chart,
            # Expose via internet-facing ALB
            ingress_alb = True,
            ingress_alb_scheme = AlbScheme.INTERNET_FACING
        )

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
        added_chart.node.add_dependency(self.cluster.alb_controller)

        alb_dns = self.cluster.get_ingress_load_balancer_address(app_chart.ingress.name)

        # Return ALB Public DNS in stack outputs
        #if record is None:
        CfnOutput(
            self,
            "ApplicationEndpoint",
            value=f"http://{alb_dns}"
        )

        if hosted_zone_id is not None:
            hosted_zone = HostedZone.from_hosted_zone_attributes(
                self,
                "HostedZone",
                hosted_zone_id=hosted_zone_id,
                zone_name=hosted_zone_name
            )

            CnameRecord(
                self,
                "CnameRecord",
                record_name=record_name,
                zone=hosted_zone,
                domain_name=alb_dns
            )

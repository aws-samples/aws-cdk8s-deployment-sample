from constructs import Construct
from aws_cdk import Stack
from aws_cdk.aws_eks import (
    FargateCluster,
    AlbControllerOptions,
    AlbControllerVersion,
    KubernetesVersion,
    AlbScheme
)
from aws_cdk.lambda_layer_kubectl_v26 import KubectlV26Layer
from cdk8s import App as Ck8sApp
from .app_chart import AppChart

class KubernetesClusterStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        #EKS Cluster
        self.cluster = FargateCluster(
            self,
            "EKSCluster",
            cluster_name = "cdk8s-samples",
            alb_controller = AlbControllerOptions(
                version = AlbControllerVersion.V2_4_1
            ),
            version = KubernetesVersion.V1_26,
            kubectl_layer = KubectlV26Layer(self, "Kubectl")
        )

        #Cdk8s resources
        self.cluster.add_cdk8s_chart(
            "AppChart",
            AppChart(
                Ck8sApp(),
                "AppChart",
                account = self.account,
                region = self.region,
                namespace = "default"
            ),
            ingress_alb = True,
            ingress_alb_scheme = AlbScheme.INTERNET_FACING
        )

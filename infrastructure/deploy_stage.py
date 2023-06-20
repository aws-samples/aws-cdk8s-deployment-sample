from aws_cdk import Stage, Environment
from constructs import Construct
from .cluster_stack import KubernetesClusterStack

class DeployStage(Stage):

    def __init__(self, scope: Construct, construct_id: str, app_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.stack = KubernetesClusterStack(
            self,
            f"{app_name}-app-stack",
             env = Environment(
                account = self.account,
                region = self.region
            )
        )

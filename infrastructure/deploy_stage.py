from aws_cdk import Stage, Environment
from constructs import Construct
from .cluster_stack import KubernetesClusterStack

class DeployStage(Stage):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            app_name: str,
            elb_account_id: str,
            certificate: str = None,
            hosted_zone_id: str = None,
            hosted_zone_name: str = None,
            record_name: str = None,
            **kwargs
        ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.stack = KubernetesClusterStack(
            self,
            f"{app_name}-app-stack",
             env = Environment(
                account = self.account,
                region = self.region
            ),
            admin_users = self.node.try_get_context("adminUsers"),
            admin_roles = self.node.try_get_context("adminRoles"),
            elb_account_id = elb_account_id,
            certificate = certificate,
            hosted_zone_id =  hosted_zone_id,
            hosted_zone_name = hosted_zone_name,
            record_name = record_name
        )

#!/usr/bin/env python
from constructs import Construct
from cdk8s import (
    Chart,
    ApiObjectMetadata
)
from cdk8s_plus_27 import (
    Deployment,
    ContainerProps,
    ImagePullPolicy,
    ContainerResources,
    CpuResources,
    Cpu,
    ServicePort,
    ServiceType,
    Protocol,
    Ingress,
    IngressBackend,
    ContainerSecurityContextProps
)

class AppChart(Chart):
    def __init__(self, scope: Construct, id: str, namespace: str, alb_access_logs_bucket_name: str, certificate: str = None):
        super().__init__(scope, id)

        self.service_target_port = 8080

        # K8s deployment
        self.deployment = Deployment(
            self,
            "MyDeployment",
            metadata = ApiObjectMetadata(
                name = "my-cdk8s-deployment",
                namespace=namespace
            ),
            select = True,
            containers = [
                 ContainerProps(
                    image = "paulbouwer/hello-kubernetes:1.5",
                    image_pull_policy = ImagePullPolicy.ALWAYS,
                    name = "nginx",
                    resources = ContainerResources(
                        cpu = CpuResources(request=Cpu.units(0.25),limit=Cpu.units(1))
                    ),
                    port_number = self.service_target_port,
                    security_context = ContainerSecurityContextProps(
                        user = 1005
                    )
                )
            ]
        )

        # K8s Service
        self.service = self.deployment.expose_via_service(
            name = "my-service",
            ports = [
                ServicePort(
                    protocol = Protocol.TCP,
                    target_port = self.service_target_port,
                    port = 80,
                )
            ],
            service_type = ServiceType.NODE_PORT
        )

        alb_annotations = {
            # Create Target Group with ip targets to work with Fargate
            "alb.ingress.kubernetes.io/target-type": "ip",
            # Set ALB name
            "alb.ingress.kubernetes.io/load-balancer-name": f"{self.service.name}-alb",
            # Enable ALB Access Logs
            "alb.ingress.kubernetes.io/load-balancer-attributes": f"access_logs.s3.enabled=true,access_logs.s3.bucket={alb_access_logs_bucket_name}"
        }

        if certificate is not None:
            # Enable TLS 1.2 and HTTPS
            alb_annotations["alb.ingress.kubernetes.io/certificate-arn"]= certificate
            alb_annotations["alb.ingress.kubernetes.io/listen-ports"]= '[{"HTTPS":443}, {"HTTP":80}]'
            alb_annotations["alb.ingress.kubernetes.io/ssl-policy"] = "ELBSecurityPolicy-TLS-1-2-Ext-2018-06"
            alb_annotations["alb.ingress.kubernetes.io/ssl-redirect"] = '443'

        # K8s ingress
        self.ingress = Ingress(
            self,
            "AppALBIngress",
            metadata = ApiObjectMetadata(
                name = "my-test-ingress",
                annotations = alb_annotations
            )
        )
        ## Route traffic to the service
        self.ingress.add_rule("/", IngressBackend.from_service(self.service))

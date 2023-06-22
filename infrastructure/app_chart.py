#!/usr/bin/env python
from constructs import Construct
from cdk8s import (
    Chart,
    ApiObjectMetadata
)
from cdk8s_plus_26 import (
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
    HorizontalPodAutoscaler,
    Metric,
    MetricTarget,
    ContainerSecurityContextProps
)

class AppChart(Chart):
    def __init__(self, scope: Construct, id: str, namespace: str):
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
        #K8s HPA
        HorizontalPodAutoscaler(
            self,
            "HPA",
            target = self.deployment,
            max_replicas = 5,
            min_replicas = 2,
            metadata = ApiObjectMetadata(
                name = f"{self.deployment.name}-hpa",
                namespace = namespace
            ),
            metrics = [
                Metric.resource_cpu(MetricTarget.average_utilization(70))
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
        # K8s ingress
        self.ingress = Ingress(
            self,
            "AppALBIngress",
            metadata = ApiObjectMetadata(
                name = "my-test-ingress",
                annotations = {
                    # Create Target Group with ip targets to work with Fargate
                    "alb.ingress.kubernetes.io/target-type": "ip"
                }
            )
        )
        # Route traffic to the service
        self.ingress.add_rule("/", IngressBackend.from_service(self.service))

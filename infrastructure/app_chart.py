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
    IngressBackend,
    HorizontalPodAutoscaler,
    Metric,
    MetricTarget
)

class AppChart(Chart):
    def __init__(self, scope: Construct, id: str, namespace: str):
        super().__init__(scope, id)
        
        service_port = 8080

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
                    #image = "public.ecr.aws/nginx/nginx:1.24-alpine",
                    image = "paulbouwer/hello-kubernetes:1.5",
                    image_pull_policy = ImagePullPolicy.ALWAYS,
                    name = "nginx",
                    resources = ContainerResources(
                        cpu = CpuResources(request=Cpu.units(0.25),limit=Cpu.units(1))
                    ),
                    port_number = service_port,
                    security_context={"user": 1005},
                )
            ]
        )

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

        self.service = self.deployment.expose_via_service(
            name = "my-service",
            #ports = [
            #    ServicePort(
            #        protocol = Protocol.TCP,
            #        target_port = 8080,
            #        port = 80,
            #    )
            #],
            service_type = ServiceType.NODE_PORT
        )

        ingress = Ingress(
            self,
            "AppALBIngress",
            metadata = ApiObjectMetadata(
                annotations = {
                    # Create Target Group with ip targets
                    "alb.ingress.kubernetes.io/target-type": "ip",
                }
            )
        )
        
        ingress.add_rule("/", IngressBackend.from_service(self.service))


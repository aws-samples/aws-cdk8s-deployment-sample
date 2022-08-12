#!/usr/bin/env python
from constructs import Construct
from cdk8s import (
    Chart,
    ApiObjectMetadata
)
from cdk8s_plus_22 import (
    Deployment,
    ContainerProps,
    ImagePullPolicy,
    ContainerResources,
    CpuResources,
    Cpu,
    ContainerLifecycle,
    Handler,
    VolumeMount,
    Volume,
    EnvValue,
    ServicePort,
    ServiceType,
    Protocol,
    Ingress,
    IngressRule,
    IngressBackend,
    HttpIngressPathType,

)
from imports.k8s import (
    KubeHorizontalPodAutoscaler,
    ObjectMeta,
    HorizontalPodAutoscalerSpec,
    CrossVersionObjectReference,
)

class AppChart(Chart):
    def __init__(self, scope: Construct, id: str, account: str, region: str, namespace: str, record: str, certificate: str):
        super().__init__(scope, id)

        shared_volume = Volume.from_empty_dir(
            self,
            id = "MyVolume",
            name = "shared-volume",
        )

        self.deployment = Deployment(
             self,
            "MyDeployment",
            metadata = ApiObjectMetadata(
                name = "my-test-deployment", namespace=namespace
            ),
            select = True,
            containers = [
                 ContainerProps(
                    image = f'{account}.dkr.ecr.{region}.amazonaws.com/nginx:latest',
                    image_pull_policy = ImagePullPolicy.ALWAYS,
                    name = "nginx",
                    resources = ContainerResources(
                        cpu = CpuResources(request=Cpu.units(0.25),limit=Cpu.units(1))
                    ),
                    port = 80,
                    env_variables={
                        "key1": EnvValue.from_value(value='value1')
                    },
                     volume_mounts = [
                        VolumeMount(
                            path = "/var/www/html",
                            volume = shared_volume
                        )
                    ],
                ),
                ContainerProps(
                    image = f'{account}.dkr.ecr.{region}.amazonaws.com/php-fpm:latest',
                    image_pull_policy = ImagePullPolicy.ALWAYS,
                    name = "php-fpm",
                    resources = ContainerResources(
                        cpu = CpuResources(request=Cpu.units(0.25),limit=Cpu.units(1))
                    ),
                    port = 9000,
                    lifecycle = ContainerLifecycle(
                        post_start = Handler.from_command(
                            command = ["/bin/bash", "-c", "mv /app/* /var/www/html"]
                        )
                    ),
                    volume_mounts = [
                        VolumeMount(
                            path = "/var/www/html",
                            volume = shared_volume
                        )
                    ],
                    env_variables={
                        "key1": EnvValue.from_value(value='value1')
                    }
                )
            ]
        )

        self.service = self.deployment.expose_via_service(
            name = "my-service",
            ports = [
                ServicePort(
                    protocol = Protocol.TCP,
                    target_port = 80,
                    port = 80,
                )
            ],
            service_type = ServiceType.NODE_PORT
        )

        Ingress(
            self,
            id =  "AppALBIngress",
            metadata = ApiObjectMetadata(
                name = "my-test-ingress",
                namespace = namespace,
                annotations = {
                    "kubernetes.io/ingress.class": "alb",
                    "alb.ingress.kubernetes.io/scheme": "internet-facing",
                    "alb.ingress.kubernetes.io/target-type": "ip",
                    "external-dns.alpha.kubernetes.io/hostname": record,
                    "alb.ingress.kubernetes.io/certificate-arn": certificate,
                    "alb.ingress.kubernetes.io/listen-ports": '[{"HTTP": 80}, {"HTTPS":443}]',
                    "alb.ingress.kubernetes.io/ssl-policy": "ELBSecurityPolicy-TLS-1-2-Ext-2018-06",
                    "alb.ingress.kubernetes.io/actions.ssl-redirect": '{"Type": "redirect", "RedirectConfig": { "Protocol": "HTTPS", "Port": "443", "StatusCode": "HTTP_301"}}'
                }
            ),
            rules = [
                IngressRule(
                    backend = IngressBackend.from_service(
                        serv = self.service,
                        port = 80
                    ),
                    path = "/",
                    path_type = HttpIngressPathType.PREFIX
                )
            ]
        )

        KubeHorizontalPodAutoscaler(
            self,
            "AppHPA",
            metadata = ObjectMeta(
                name = f"{self.deployment.name}-hpa",
                namespace = namespace
            ),
            spec = HorizontalPodAutoscalerSpec(
                max_replicas = 5,
                min_replicas = 2,
                scale_target_ref = CrossVersionObjectReference(
                    kind = "Deployment",
                    name = self.deployment.name,
                    api_version = "apps/v1",
                ),
                target_cpu_utilization_percentage = 80
            )
        )

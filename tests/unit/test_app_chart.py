import cdk8s
from infrastructure.app_chart import AppChart

app = cdk8s.Testing.app(yaml_output_type=cdk8s.YamlOutputType.FOLDER_PER_CHART_FILE_PER_RESOURCE)

NAMESPACE = "default"
LOGS_BUCKET = "mock-bucket"
MOCK_ACM_ARN = "mock-arn"

chart = AppChart(
    app,
    "cdk8s-test",
    namespace = NAMESPACE,
    alb_access_logs_bucket_name = LOGS_BUCKET,
    certificate = MOCK_ACM_ARN
)

synth = cdk8s.Testing.synth(chart)

def test_deployment():
    deployment_synth = synth[0]
    expected_deployment =  {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "my-cdk8s-deployment",
            "namespace": NAMESPACE
        },
        "spec": {
            "minReadySeconds": 0,
            "progressDeadlineSeconds": 600,
            "replicas": 2,
            "selector": {
                "matchLabels": chart.deployment.match_labels
            },
            "strategy": {
                "rollingUpdate": {
                    "maxSurge": "25%",
                    "maxUnavailable": "25%"
                },
                "type": "RollingUpdate"
            },
            "template": {
                "metadata": {
                    "labels": chart.deployment.match_labels
                },
                "spec": {
                    "automountServiceAccountToken": False,
                    "containers": [
                        {
                            "image": "paulbouwer/hello-kubernetes:1.5",
                            "imagePullPolicy": "Always",
                            "name": "nginx",
                            "ports": [
                                {
                                    "containerPort": chart.service_target_port
                                }
                            ],
                            "resources": {
                                "limits": {
                                    "cpu": "1"
                                },
                                "requests": {
                                    "cpu": "0.25"
                                }
                            },
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "privileged": False,
                                "readOnlyRootFilesystem": True,
                                "runAsNonRoot": True,
                                "runAsUser": 1005
                            },
                            "startupProbe": {
                                "failureThreshold": 3,
                                "tcpSocket": {
                                    "port": chart.service_target_port
                                }
                            }
                        }
                    ],
                    "dnsPolicy": "ClusterFirst",
                    "hostNetwork": False,
                    "restartPolicy": "Always",
                    "securityContext": {
                        "fsGroupChangePolicy": "Always",
                        "runAsNonRoot": True
                    },
                    "setHostnameAsFQDN": False,
                    "terminationGracePeriodSeconds": 30
                }
            }
        }
    }

    assert deployment_synth == expected_deployment

def test_service():
    service_synth = synth[1]
    expected_service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "my-service",
            "namespace": NAMESPACE
        },
        "spec": {
            "externalIPs": [],
            "ports": [
                {
                    "port": 80,
                    "protocol": "TCP",
                    "targetPort": chart.service_target_port
                }
            ],
            "selector": chart.deployment.match_labels,
            "type": "NodePort"
        }
    }
    assert service_synth == expected_service

def test_ingress_https():
    ingress_synth = synth[2]
    expected_ingress = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "annotations": {
                "alb.ingress.kubernetes.io/target-type": "ip",
                "alb.ingress.kubernetes.io/load-balancer-name": f'{synth[1]["metadata"]["name"]}-alb',
                "alb.ingress.kubernetes.io/load-balancer-attributes": f"access_logs.s3.enabled=true,access_logs.s3.bucket={LOGS_BUCKET}",
                "alb.ingress.kubernetes.io/certificate-arn": MOCK_ACM_ARN,
                "alb.ingress.kubernetes.io/listen-ports": '[{"HTTPS":443}, {"HTTP":80}]',
                "alb.ingress.kubernetes.io/ssl-policy": "ELBSecurityPolicy-TLS-1-2-Ext-2018-06",
                "alb.ingress.kubernetes.io/ssl-redirect": '443'
            },
            "name": "my-test-ingress"
        },
        "spec": {
            "rules": [
                {
                    "http": {
                        "paths": [
                            {
                                "backend": {
                                    "service": {
                                        "name": chart.service.name,
                                        "port": {
                                            "number": chart.service.port
                                        }
                                    }
                                },
                                "path": "/",
                                "pathType": "Prefix"
                            }
                        ]
                    }
                }
            ]
        }
    }
    assert ingress_synth == expected_ingress

def test_ingress_http():
    synth = cdk8s.Testing.synth(
        AppChart(
            app,
            "cdk8s-test-2",
            namespace = NAMESPACE,
            alb_access_logs_bucket_name = LOGS_BUCKET
        )
    )
    ingress_synth = synth[2]
    expected_ingress = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "annotations": {
                "alb.ingress.kubernetes.io/target-type": "ip",
                "alb.ingress.kubernetes.io/load-balancer-name": f'{synth[1]["metadata"]["name"]}-alb',
                "alb.ingress.kubernetes.io/load-balancer-attributes": f"access_logs.s3.enabled=true,access_logs.s3.bucket={LOGS_BUCKET}",
            },
            "name": "my-test-ingress"
        },
        "spec": {
            "rules": [
                {
                    "http": {
                        "paths": [
                            {
                                "backend": {
                                    "service": {
                                        "name": chart.service.name,
                                        "port": {
                                            "number": chart.service.port
                                        }
                                    }
                                },
                                "path": "/",
                                "pathType": "Prefix"
                            }
                        ]
                    }
                }
            ]
        }
    }
    assert ingress_synth == expected_ingress

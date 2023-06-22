import cdk8s
from infrastructure.app_chart import AppChart

app = cdk8s.Testing.app(yaml_output_type=cdk8s.YamlOutputType.FOLDER_PER_CHART_FILE_PER_RESOURCE)

NAMESPACE = "default"

chart = AppChart(
    app,
    "cdk8s-test",
    namespace = NAMESPACE
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

def test_ingress():
    ingress_synth = synth[3]
    expected_ingress = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "annotations": {
                "alb.ingress.kubernetes.io/target-type": "ip"
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

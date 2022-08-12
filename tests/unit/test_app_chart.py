import random
import cdk8s
from app_chart import AppChart

NAMESPACE = "qa"
REGION = "us-east-1"
ACCOUNT = str(random.randint(111111111111, 999999999999))
RECORD = "k8s-mock.com"
CERTIFICATE = f"arn:aws:acm:{REGION}:{ACCOUNT}:certificate/87a54c1a-7749-49a8-828f-4b94e6b97a89"

app = cdk8s.Testing.app(yaml_output_type=cdk8s.YamlOutputType.FOLDER_PER_CHART_FILE_PER_RESOURCE)
chart = AppChart(
    app,
    "cdk8s-test",
    ACCOUNT,
    REGION,
    NAMESPACE,
    RECORD,
    CERTIFICATE
)

synth = cdk8s.Testing.synth(chart)
deployment_synth = synth[0]
service_synth = synth[1]
ingress_synth = synth[2]

def test_deployment():
    expected_deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "my-test-deployment",
            "namespace": NAMESPACE
        },
        "spec": {
            "minReadySeconds": 0,
            "progressDeadlineSeconds": 600,
            "replicas": 1,
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
                    "automountServiceAccountToken": True,
                    "containers": [
                        {
                            "env": [
                                {
                                    "name": "key1",
                                    "value": "value1"
                                }
                            ],
                            "image": f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/nginx:latest",
                            "imagePullPolicy": "Always",
                            "name": "nginx",
                            "ports": [
                                {
                                    "containerPort": 80
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
                                "privileged": False,
                                "readOnlyRootFilesystem": False,
                                "runAsNonRoot": False
                            },
                            "volumeMounts": [
                                {
                                    "mountPath": "/var/www/html",
                                    "name": "shared-volume"
                                }
                            ]
                        },
                        {
                            "env": [
                                {
                                    "name": "key1",
                                    "value": "value1"
                                }
                            ],
                            "image": f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/php-fpm:latest",
                            "imagePullPolicy": "Always",
                            "lifecycle": {
                                "postStart": {
                                    "exec": {
                                        "command": [
                                            "/bin/bash",
                                            "-c",
                                            "mv /app/* /var/www/html"
                                        ]
                                    }
                                }
                            },
                            "name": "php-fpm",
                            "ports": [
                                {
                                    "containerPort": 9000
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
                                "privileged": False,
                                "readOnlyRootFilesystem": False,
                                "runAsNonRoot": False
                            },
                            "volumeMounts": [
                                {
                                    "mountPath": "/var/www/html",
                                    "name": "shared-volume"
                                }
                            ]
                        }
                    ],
                    "dnsPolicy": "ClusterFirst",
                    "securityContext": {
                        "fsGroupChangePolicy": "Always",
                        "runAsNonRoot": False
                    },
                    "setHostnameAsFQDN": False,
                    "volumes": [
                        {
                            "emptyDir": {},
                            "name": "shared-volume"
                        }
                    ]
                }
            }
        }
    }
    assert deployment_synth == expected_deployment

def test_service():
    expected_service = {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {
            'name': 'my-service',
            'namespace': NAMESPACE
        },
        'spec': {
            'externalIPs': [],
            'ports': [
                {
                    'port': 80,
                    'protocol': 'TCP',
                    'targetPort': 80
                }
            ],
            'selector': chart.deployment.match_labels,
            'type': 'NodePort'
        }
    }
    assert service_synth == expected_service

def test_ingress():
    expected_ingress = {
    "apiVersion": "networking.k8s.io/v1",
    "kind": "Ingress",
    "metadata": {
        "annotations": {
            "alb.ingress.kubernetes.io/actions.ssl-redirect": '{"Type": "redirect", "RedirectConfig": { "Protocol": "HTTPS", "Port": "443", "StatusCode": "HTTP_301"}}',
            "alb.ingress.kubernetes.io/certificate-arn": CERTIFICATE,
            "alb.ingress.kubernetes.io/listen-ports": '[{"HTTP": 80}, {"HTTPS":443}]',
            "alb.ingress.kubernetes.io/scheme": "internet-facing",
            "alb.ingress.kubernetes.io/ssl-policy": "ELBSecurityPolicy-TLS-1-2-Ext-2018-06",
            "alb.ingress.kubernetes.io/target-type": "ip",
            "external-dns.alpha.kubernetes.io/hostname": RECORD,
            "kubernetes.io/ingress.class": "alb"
        },
        "name": "my-test-ingress",
        "namespace": "qa"
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
                                        "number": 80
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

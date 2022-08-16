# K8s deployments as code with cdk8s

This is a sample repository of how to create a k8s deployment using python and cdk8s. It also includes how to expose it as service and how to write unit tests.

## Pre-requisites
* [cdk8s CLI](https://cdk8s.io/docs/latest/getting-started/)
* [Python](https://www.python.org/downloads/)
* [Pipenv](https://pipenv.pypa.io/en/latest/)
* An existing K8s cluster
* If you want to use the [HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) example you will need to have it installed and running in your cluster

## Install

To install the dependencies of the project, just run the following command:

```
pipenv install
```

Then, enable the pipenv using this command:

```
pipenv shell
```

Finally, set the environment variables. Create `.env` file in the root of the repository having this values:

```
ACCOUNT=account-id
REGION=region
NAMESPACE=namespace
RECORD=example.com
CERTIFICATE=acm-certificate-id
```

Fill it with your desired values, where the value of `CERTIFICATE` variable must be the id of a certificate from [AWS ACM](https://aws.amazon.com/certificate-manager/).

## Scripts

### Unit testing
Unit tests were written using [pytest](https://docs.pytest.org/) library. You can find them in `tests/unit`. For more information about cdk8s unit tests check this [link](https://cdk8s.io/docs/latest/concepts/testing/). 

To run unit tests, use this command inside with the pipenv enabled:

```
pytest
```
### Linting
The integrated linting tool is [pylint](https://pypi.org/project/pylint/) library. The `.pylintrc` file indicates the configuration to apply. To run the linting tool use this command with the pipenv enabled:

For a particular file:
```
pylint file
```
For an entire python module
```
pylint module
```

### Dependency audit
The integrated linting tool is [safety](https://pypi.org/project/safety/) library. To run this tool use this commands with the pipenv enabled:

```
pipenv lock -r > requirements.txt
```

```
safety check -r requirements.txt
```
## Apply changes to the cluster
To apply the changes to the cluster, you will need first to create the k8s manisfest files using this command:
```
cdk8s import && cdk8s synth
```
This will create the yaml files into `dist/cdk8s-test` folder so, to apply them use the following command:
```
kubectl apply -f dist/cdk8s-test
```
## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.


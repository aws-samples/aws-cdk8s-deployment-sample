# K8s deployments as code with cdk8s

This is a sample repository of how to create an Amazon EKS cluster with a k8s deployment using python, AWS CDK and cdk8s. It also includes how to expose it as service and python security and quality checks.

![Architecture Diagram](/assets/architercture_diagram.png)

## Pre-requisites

### Mandatory
* [Python](https://www.python.org/downloads/)
* [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install)

### Optional
If you want to enable the HTTPS with TLS listener in the ALB, you will need:

* One Amazon Route53 Hosted Zone
* One certificate in AWS Certificate Manager

## Install

To install the dependencies of the project, just run the following commands:

```
python3 -m venv .venv
```
```
source .venv/bin/activate
```
```
pip3 install -r requirements.txt
```

## Add users and roles to your Amazon EKS Cluster [optional]

You can add roles or users for your Amazon EKS cluster in the `cdk.json` file:

```
"adminRoles": [
    "Role1",
    "Role2"
],
"adminUsers": [
    "User1",
    "User2"
]
```
This way you will be able to see the resources from EKS console.
## Deploy the CI/CD pipeline

First you will need to bootstrap your desired AWS region. Then you will need to create an AWS CodeCommit repository and put the code inside.

First, set the environment variables:
```
export ACCOUNT=your-account-id
```
```
export REGION=desired-aws-region
```
```
export ELB_ACCOUNT_ID=elb-account-id
```
To get this value, check this [link](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/enable-access-logging.html#attach-bucket-policy) to get it based on the target region of your deployment.

If you want to enable the HTTPS listener in the ALB (Best Practice and reommended):
```
export CERTIFICATE=acm-certificate-arn
```
```
export HOSTED_ZONE_ID=hosted-zone-id
```
```
export HOSTED_ZONE_NAME=hosted-zone-name
```
```
export RECORD_NAME=my-record.$HOSTED_ZONE
```
The values of `CERTIFICATE`, `HOSTED_ZONE_ID` and `HOSTED_ZONE_NAME` need to be replaced using an existing AWS ACM certificate and an existing Amazon Route53 hosted zone. The value of `RECORD_NAME` is the record name that you want to create inside the hosted zone.

Then, create the repository:
```
chmod +x init_environment.sh
```
```
./init_environment.sh
```
NOTE: replace the `ACCOUNT` variable value with your account id and the `REGION` with the desired AWS region.

Finally, run the deploy command:

```
cdk deploy
```

This will create an AWS CloudFormation stack called `cdk8s-samples-pipeline-stack` and an AWS CodePipeline pipeline called `cdk8s-samples-pipeline`. Once the pipeline finishes its execution you will have your Amazon EKS cluster with the resources inside deployed.


## Quality Scripts

In order to run quality tools, follow the **Setup** instructions and also install the requirements-dev.txt dependencies:

```
pip3 install -r requirements-dev.txt
```

NOTE: All this checks will run as part of the CI/CD pipeline.
### Unit testing
Unit tests were written using [pytest](https://docs.pytest.org/) library. You can find them in `tests/unit`. For more information about cdk8s unit tests check:

* [Unit testing on cdk8s](https://cdk8s.io/docs/latest/concepts/testing/)
* [Unit testing on AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/testing.html)

To run unit tests, use this command with the virtual env enabled:

```
python3 -m pytest
```
To collect coverage run the following:
```
python3 -m coverage run -m pytest
```
```
python3 -m coverage report
```
### Linting
The integrated linting tool is [pylint](https://pypi.org/project/pylint/) library. The `.pylintrc` file indicates the configuration to apply. To run the linting tool use this command with the virtual env enabled:

For a particular file:
```
python3 -m pylint file
```
For an entire python module
```
python3 -m pylint module
```
## Security Scripts
In order to run quality tools, follow the **Setup** instructions and also install the requirements-dev.txt dependencies:

```
pip3 install -r requirements-dev.txt
```

NOTE: All this checks will run as part of the CI/CD pipeline.
### Bandit

[Bandit](https://bandit.readthedocs.io/en/latest/) library allows you to find common security issues in Python code. To do this, Bandit processes each file, builds an AST from it, and runs appropriate plugins against the AST nodes. The `.bandit` file indicates the configuration to apply. To run bandit, use these command with the virtual env enabled:
```
bandit -r .
```

### Dependency audit
[Safety](https://pypi.org/project/safety/) library is used to scan dependencies for known vulnerabilities. To run safety, use these commands with the virtual env enabled:

```
safety check -r requirements.txt
```
```
safety check -r requirements-dev.txt
```

### GitLeaks
[GitLeaks](https://gitleaks.io/) is a fast, light-weight, portable, and open-source secret scanner for git repositories, files, and directories. You can scan both the current commit or the commit history from your repository. After following the installation, you can use the following commands:

Scan all remote commits history:
```
gitleaks detect --source . -v
```
Scan only current commit:
```
gitleaks protect --source . -v
```
## Cleanup

You can delete the pipeline stack by running this command in the root of the cloned repository:

```
cdk destroy
```

The expected output should look like this:
```
Are you sure you want to delete: cdk8s-samples-pipeline-stack (y/n)? y
cdk8s-samples-pipeline-stack: destroying... [1/1]

✅ cdk8s-samples-pipeline-stack: destroyed
```

Then, delete the resources stack:

```
aws cloudformation delete-stack —stack-name DEV-cdk8s-samples-app-stack —region $REGION
```

You can wait until the stack deletion with this command:

```
aws cloudformation wait stack-delete-complete --stack-name DEV-cdk8s-samples-app-stack --region $REGION
```

Finally, run this command to delete the CodeCommit repository:
```
aws codecommit delete-repository --repository-name cdk8s-samples --region $REGION
```
The expected output should look like this:
```
{
    "repositoryId": "0de60c79-c170-4f98-acd7-8105b51d3daf"
}
```
In case you don't need AWS CDK in your region, you can delete the CDKToolkit stack with this command:
```
aws cloudformation delete-stack --stack-name CDKToolkit --region $REGION
```
## Contributing
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.
## License

This library is licensed under the MIT-0 License. See the LICENSE file.


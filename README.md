# aws-cdk-serverless-pipeline

This repository is an AWS CDK project for building a CI/CD pipeline for general serverless applications.
It builds based on the `buildspec.yml` included in the source code, generates a SAM template (`packaged.yaml`), and executes CloudFormation based on that template.

## Features

- Supports **GitHub** or **CodeCommit** as source repositories.
- Automatically builds and deploys serverless applications using **CodeBuild** and **CodePipeline**.
- Flexible customization of environment and repository settings.

## Setup
Install aws-cdk
```bash
$ npm install -g aws-cdk
```

Install the required dependencies:

```bash
$ pip install -r requirements.txt
```

### CDK Commands

The following CDK commands are available:

- `cdk synth`: Generates a CloudFormation template.
- `cdk deploy`: Deploys the stack to your AWS account/region.
- `cdk diff`: Compares the deployed stack with the current state.
- `cdk destroy`: Deletes the stack.

For more information, see the [AWS CDK Developer Guide](https://docs.aws.amazon.com/cdk/v2/guide/home.html).

## Context Values

The following context values can be specified during deployment:

- `applicationName`: The application name. Used as the CloudFormation stack name, CodeBuild name, and CodePipeline name.
- `environment`: The environment name. Specify one of `dev`, `stg`, or `prd`. Used as the `ENV` environment variable in CodeBuild and for handling environment-specific logic in `buildspec.yml`.
- `sourceType`: The type of source repository. Specify either `github` or `codecommit`.

These values can be defined in the `cdk.json` file or specified during deployment using the `--context` or `-c` option.

#### Example `cdk.json`

```json
{
  "app": "python3 app.py",
  "context": {
    "applicationName": "MyServerlessApp",
    "environment": "dev",
    "sourceType": "github"
  }
}
```

## Parameters

The following parameters can be specified during deployment:

- `RepositoryName`: The name of the source repository.
- `BranchName`: The branch name of the source repository.
- `TemplateFileName`: The name of the packaged template file (default: `packaged.yaml`).
- `GithubOwner`: The owner name of the GitHub repository. Required if `source_type` is `github`.
- `GithubConnectionArn`: The ARN of the CodeStar Connection. Required if `source_type` is `github`.

These values can be specified using the `--parameters` option during deployment.

### Example Deployment Command

Github Source
```bash
$ cdk deploy \
  --parameters RepositoryName=MyRepo \
  --parameters BranchName=main \
  --parameters TemplateFileName=packaged.yaml \
  --parameters GithubOwner=my-github-user \
  --parameters GithubConnectionArn=arn:aws:codeconnections:region:account-id:connection/connection-id \
  -c applicationName=MyServerlessApp \
  -c environment=dev \
  -c sourceType=github
```

Codecommit Source
```bash
$ cdk deploy \
  --parameters RepositoryName=MyRepo \
  --parameters BranchName=main \
  --parameters TemplateFileName=packaged.yaml \
  -c applicationName=MyServerlessApp \
  -c environment=dev \
  -c sourceType=codecommit
```

## Build Process

This project uses `buildspec.yml` to define the build process. The following steps are performed to build and deploy the application:

1. Fetch the source code (GitHub or CodeCommit).
2. Execute the build based on `buildspec.yml`.
3. Generate a SAM template (`packaged.yaml`).
4. Deploy resources using CloudFormation.

## Notes

- This project is designed to build a CI/CD pipeline for AWS serverless applications.
- Ensure that your AWS credentials are properly configured before deployment.

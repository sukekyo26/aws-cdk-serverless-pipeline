# generate-chalice-pipeline

This repository provides an AWS CDK stack to build a CI/CD pipeline for deploying AWS Chalice applications.
While Chalice offers the `chalice generate-pipeline` command to create CloudFormation templates, it has not been maintained for a long time and uses outdated configurations. This project was created to address those limitations and provide a modern solution.

## Features

- Supports **CodeCommit** as the source repository.
- Automatically builds and deploys Chalice applications using **CodeBuild** and **CodePipeline**.
- Allows customization through parameters like `application_name` and `existing_codecommit_repository_name`.

## Setup

install the required dependencies:

```bash
$ pip install -r requirements.txt
```

### CDK Commands

The following CDK commands are available:

- `cdk synth`: Synthesizes the CloudFormation template.
- `cdk deploy`: Deploys the stack to your AWS account/region.
- `cdk diff`: Compares the deployed stack with the current state.
- `cdk destroy`: Deletes the stack.

### Parameters

When deploying the stack, you can specify the following parameters:

- `application_name`: The name of your Chalice application. This will be used to name resources like the CodeCommit repository or CodePipeline.
- `existing_codecommit_repository_name`: (Optional) If you already have a CodeCommit repository, specify its name here. Otherwise, a new repository will be created.

Example deployment command:

```bash
$ cdk deploy --parameters application_name=MyChaliceApp --parameters existing_codecommit_repository_name=MyExistingRepo
```

## Useful Commands

- `cdk ls`: List all stacks in the app.
- `cdk synth`: Emit the synthesized CloudFormation template.
- `cdk deploy`: Deploy this stack to your default AWS account/region.
- `cdk diff`: Compare the deployed stack with the current state.
- `cdk destroy`: Destroy the stack.

## Notes

- This project is designed to work with AWS Chalice applications.
- Ensure that your AWS credentials are properly configured before deploying the stack.
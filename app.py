#!/usr/bin/env python3

import aws_cdk as cdk

from aws_cdk_serverless_pipeline.aws_cdk_serverless_pipeline_stack import AwsCdkServerlessPipelineStack


app = cdk.App()

stack_name = app.node.try_get_context("stackName")
environment = app.node.try_get_context("environment")
existing_repo_name = app.node.try_get_context("existingCodeCommitRepositoryName")

ALLOWED_ENVIRONMENTS = ["dev", "stg", "prd"]

if environment not in ALLOWED_ENVIRONMENTS:
    raise ValueError(
        f"Invalid environment '{environment}'. Allowed values are: {', '.join(ALLOWED_ENVIRONMENTS)}"
    )

AwsCdkServerlessPipelineStack(
    app,
    "AwsCdkServerlessPipelineStack",
    stack_name=stack_name,
    environment=environment,
    existing_codecommit_repository_name=existing_repo_name,
)

app.synth()

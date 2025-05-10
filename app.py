#!/usr/bin/env python3

import aws_cdk as cdk

from aws_cdk_serverless_pipeline.aws_cdk_serverless_pipeline_stack import AwsCdkServerlessPipelineStack


ALLOWED_ENVIRONMENTS = ["dev", "stg", "prd"]
ALLOWED_SOURCE_TYPES = ["github", "codecommit"]

app = cdk.App()

stack_name = app.node.try_get_context("stackName")
environment = app.node.try_get_context("environment")
source_type = app.node.try_get_context("sourceType")

# Validation context
missing_contexts = []

if not stack_name:
    missing_contexts.append("stackName")
if not environment:
    missing_contexts.append("environment")
if not source_type:
    missing_contexts.append("sourceType")

if missing_contexts:
    raise ValueError(
        f"The following context values are required but missing: {', '.join(missing_contexts)}. "
        "Please provide them using the '-c <key>=<value>' option."
    )

if environment not in ALLOWED_ENVIRONMENTS:
    raise ValueError(
        f"Invalid environment '{environment}'. Allowed values are: {', '.join(ALLOWED_ENVIRONMENTS)}"
    )

if source_type not in ALLOWED_SOURCE_TYPES:
    raise ValueError(
        f"Invalid source type '{source_type}'. Allowed values are: {', '.join(ALLOWED_SOURCE_TYPES)}"
    )

AwsCdkServerlessPipelineStack(
    app,
    "AwsCdkServerlessPipelineStack",
    stack_name=stack_name,
    environment=environment,
    source_type=source_type,
)

app.synth()

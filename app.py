#!/usr/bin/env python3

import re

import aws_cdk as cdk

from aws_cdk_serverless_pipeline.aws_cdk_serverless_pipeline_stack import AwsCdkServerlessPipelineStack


ALLOWED_ENVIRONMENTS = ["dev", "stg", "prd"]
ALLOWED_SOURCE_TYPES = ["github", "codecommit"]
PASCAL_CASE_PATTERN = r'^[A-Z][a-zA-Z0-9]*$'

app = cdk.App()

# Application name for use as the name of cloudformation stack ,codebuild, and codepipeline
# Enter in Pascal case.
application_name = app.node.try_get_context("applicationName")
# The environment name. Specify one of dev, stg, or prd.
# Used as the ENV environment variable in CodeBuild and for handling environment-specific logic in buildspec.yml
environment = app.node.try_get_context("environment")
# The type of source repository. Specify either github or codecommit.
source_type = app.node.try_get_context("sourceType")

# Validation context
missing_contexts = []

if not application_name:
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

# check Application name is pascal case
if not re.match(PASCAL_CASE_PATTERN, application_name):
    raise ValueError(
        f"The application name '{application_name}' is invalid. It must be in PascalCase format."
    )

# check Source type is `github` or `codecommit`
if source_type not in ALLOWED_SOURCE_TYPES:
    raise ValueError(
        f"Invalid source type '{source_type}'. Allowed values are: {', '.join(ALLOWED_SOURCE_TYPES)}"
    )

AwsCdkServerlessPipelineStack(
    app,
    "AwsCdkServerlessPipelineStack",
    stack_name=f"{application_name}Stack",
    application_name=application_name,
    environment=environment,
    source_type=source_type,
)

app.synth()

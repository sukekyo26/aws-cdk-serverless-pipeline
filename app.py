#!/usr/bin/env python3

import aws_cdk as cdk

from generate_chalice_pipeline.generate_chalice_pipeline_stack import GenerateChalicePipelineStack


app = cdk.App()

repository_name = app.node.try_get_context("repository_name")
existing_repo_name = app.node.try_get_context("existing_codecommit_repo_name")

GenerateChalicePipelineStack(
    app,
    "GenerateChalicePipelineStack",
    repository_name=repository_name,
    existing_codecommit_repo_name=existing_repo_name,
)

app.synth()

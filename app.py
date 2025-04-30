#!/usr/bin/env python3

import aws_cdk as cdk

from generate_chalice_pipeline.generate_chalice_pipeline_stack import GenerateChalicePipelineStack


app = cdk.App()

application_name = app.node.try_get_context("application_name")
existing_repo_name = app.node.try_get_context("existing_codecommit_repository_name")

GenerateChalicePipelineStack(
    app,
    "GenerateChalicePipelineStack",
    application_name==application_name,
    existing_codecommit_repository_name=existing_repo_name,
)

app.synth()

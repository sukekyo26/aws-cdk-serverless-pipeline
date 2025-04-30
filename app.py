#!/usr/bin/env python3

import aws_cdk as cdk

from generate_chalice_pipeline.generate_chalice_pipeline_stack import GenerateChalicePipelineStack


app = cdk.App()

existing_repo_name = app.node.try_get_context("existingCodeCommitRepositoryName")

GenerateChalicePipelineStack(
    app,
    "GenerateChalicePipelineStack",
    existing_codecommit_repository_name=existing_repo_name
)

app.synth()

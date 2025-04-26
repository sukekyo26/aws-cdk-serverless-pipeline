#!/usr/bin/env python3

import aws_cdk as cdk

from generate_chalice_pipeline.generate_chalice_pipeline_stack import GenerateChalicePipelineStack


app = cdk.App()
GenerateChalicePipelineStack(app, "GenerateChalicePipelineStack")

app.synth()

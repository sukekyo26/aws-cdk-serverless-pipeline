import aws_cdk as core
import aws_cdk.assertions as assertions
from aws_cdk_serverless_pipeline.aws_cdk_serverless_pipeline_stack import AwsCdkServerlessPipelineStack


def test_application_bucket_created():
    app = core.App()
    stack = AwsCdkServerlessPipelineStack(
        app,
        "AwsCdkServerlessPipelineStack",
        application_name="TestApp",
        environment="dev",
        source_type="codecommit"
    )
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::S3::Bucket", 2)  # ApplicationBucket and ArtifactBucketStore


def test_artifact_bucket_created():
    app = core.App()
    stack = AwsCdkServerlessPipelineStack(
        app,
        "AwsCdkServerlessPipelineStack",
        application_name="TestApp",
        environment="dev",
        source_type="codecommit"
    )
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::S3::Bucket", 2)  # ApplicationBucket and ArtifactBucketStore
    template.has_resource_properties("AWS::S3::Bucket", {
        "VersioningConfiguration": {
            "Status": "Enabled"
        }
    })


def test_codebuild_role_created():
    app = core.App()
    stack = AwsCdkServerlessPipelineStack(
        app,
        "AwsCdkServerlessPipelineStack",
        application_name="TestApp",
        environment="dev",
        source_type="codecommit"
    )
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "codebuild.amazonaws.com"
                    }
                }
            ],
            "Version": "2012-10-17"
        }
    })


def test_codebuild_project_created():
    application_name = "TestApp"
    environment = "dev"

    app = core.App()
    stack = AwsCdkServerlessPipelineStack(
        app,
        "AwsCdkServerlessPipelineStack",
        application_name=application_name,
        environment=environment,
        source_type="codecommit"
    )
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::CodeBuild::Project", {
        "Name": f"{application_name}Build",
        "Artifacts": {
            "Type": "CODEPIPELINE"
        },
        "Cache": {
            "Type": "NO_CACHE"
        },
        "Environment": {
            "ComputeType": "BUILD_GENERAL1_SMALL",
            "EnvironmentVariables": [
                {
                    "Name": "ENV",
                    "Type": "PLAINTEXT",
                    "Value": environment
                },
                {
                    "Name": "APP_S3_BUCKET",
                    "Type": "PLAINTEXT",
                }
            ],
            "Image": "aws/codebuild/amazonlinux2-x86_64-standard:5.0",
            "Type": "LINUX_CONTAINER"
        },
        "Source": {
            "BuildSpec": "buildspec.yml",
            "Type": "CODEPIPELINE"
        }
    })


def test_codepipeline_role_created():
    app = core.App()
    stack = AwsCdkServerlessPipelineStack(
        app,
        "AwsCdkServerlessPipelineStack",
        application_name="TestApp",
        environment="dev",
        source_type="codecommit"
    )
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "codepipeline.amazonaws.com"
                    }
                }
            ],
            "Version": "2012-10-17",
        }
    })


def test_cfn_deploy_role_created():
    app = core.App()
    stack = AwsCdkServerlessPipelineStack(
        app,
        "AwsCdkServerlessPipelineStack",
        application_name="TestApp",
        environment="dev",
        source_type="codecommit"
    )
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudformation.amazonaws.com"
                    }
                }
            ],
            "Version": "2012-10-17"
        }
    })


def test_pipeline_created():
    application_name = "TestApp"
    environment = "dev"

    app = core.App()
    stack = AwsCdkServerlessPipelineStack(
        app,
        "AwsCdkServerlessPipelineStack",
        application_name=application_name,
        environment=environment,
        source_type="codecommit"
    )
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::CodePipeline::Pipeline", {
        "Name": f"{application_name}Pipeline",
        "PipelineType": "V2",
        "Stages": assertions.Match.array_with([
            assertions.Match.object_like({"Name": "Source"}),
            assertions.Match.object_like({"Name": "Build"}),
            assertions.Match.object_like({"Name": "CfnDeploy"})
        ])
    })


def test_cloudformation_outputs_created():
    app = core.App()
    stack = AwsCdkServerlessPipelineStack(
        app,
        "AwsCdkServerlessPipelineStack",
        application_name="TestApp",
        environment="dev",
        source_type="codecommit"
    )
    template = assertions.Template.from_stack(stack)

    template.has_output("S3ApplicationBucket", {})
    template.has_output("CodeBuildRoleArn", {})
    template.has_output("S3PipelineBucket", {})
    template.has_output("CodePipelineRoleArn", {})
    template.has_output("CFNDeployRoleArn", {})

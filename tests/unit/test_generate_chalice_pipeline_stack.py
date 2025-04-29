import aws_cdk as core
import aws_cdk.assertions as assertions
from generate_chalice_pipeline.generate_chalice_pipeline_stack import GenerateChalicePipelineStack


def test_s3_application_bucket_created():
    app = core.App()
    stack = GenerateChalicePipelineStack(app, "generate-chalice-pipeline", repository_name="TestRepo")
    template = assertions.Template.from_stack(stack)

    print(template.to_json())
    template.resource_count_is("AWS::S3::Bucket", 2)  # ApplicationBucket and ArtifactBucketStore


def test_codecommit_repository_created():
    app = core.App()
    stack = GenerateChalicePipelineStack(app, "generate-chalice-pipeline", repository_name="TestRepo")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::CodeCommit::Repository", {
        "RepositoryName": "TestRepo"
    })


def test_artifact_bucket_created():
    app = core.App()
    stack = GenerateChalicePipelineStack(app, "generate-chalice-pipeline", repository_name="TestRepo")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::S3::Bucket", 2)  # ApplicationBucket and ArtifactBucketStore
    template.has_resource_properties("AWS::S3::Bucket", {
        "VersioningConfiguration": {
            "Status": "Enabled"
        }
    })


def test_codebuild_role_created():
    app = core.App()
    stack = GenerateChalicePipelineStack(app, "generate-chalice-pipeline", repository_name="TestRepo")
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
    app = core.App()
    stack = GenerateChalicePipelineStack(app, "generate-chalice-pipeline", repository_name="TestRepo")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::CodeBuild::Project", {
        "Name": "TestRepoBuild",
        "Environment": {
            "ComputeType": "BUILD_GENERAL1_SMALL",
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
    stack = GenerateChalicePipelineStack(app, "generate-chalice-pipeline", repository_name="TestRepo")
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
            "Version": "2012-10-17"
        }
    })


def test_cfn_deploy_role_created():
    app = core.App()
    stack = GenerateChalicePipelineStack(app, "generate-chalice-pipeline", repository_name="TestRepo")
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
    app = core.App()
    stack = GenerateChalicePipelineStack(app, "generate-chalice-pipeline", repository_name="TestRepo")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::CodePipeline::Pipeline", {
        "Name": "TestRepoPipeline",
        "PipelineType": "V2",
        "Stages": assertions.Match.array_with([
            assertions.Match.object_like({"Name": "Source"}),
            assertions.Match.object_like({"Name": "Build"}),
            assertions.Match.object_like({"Name": "Approval"}),
            assertions.Match.object_like({"Name": "Deploy"})
        ])
    })


def test_cloudformation_outputs_created():
    app = core.App()
    stack = GenerateChalicePipelineStack(app, "generate-chalice-pipeline", repository_name="TestRepo")
    template = assertions.Template.from_stack(stack)

    template.has_output("SourceRepoURL", {})
    template.has_output("S3ApplicationBucket", {})
    template.has_output("CodeBuildRoleArn", {})
    template.has_output("S3PipelineBucket", {})
    template.has_output("CodePipelineRoleArn", {})
    template.has_output("CFNDeployRoleArn", {})

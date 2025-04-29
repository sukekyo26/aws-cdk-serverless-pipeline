from typing import Optional

from aws_cdk import (
    CfnOutput,
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
)
from constructs import Construct


class GenerateChalicePipelineStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        repository_name: str,
        existing_codecommit_repo_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #############################################################
        # CodeCommit
        #############################################################
        if existing_codecommit_repo_name:
            source_repository = codecommit.Repository.from_repository_name(
                self,
                "SourceRepository",
                repository_name=existing_codecommit_repo_name
            )
        else:
            source_repository = codecommit.Repository(
                self,
                "SourceRepository",
                repository_name=repository_name,
                description=f"Source code for {repository_name}",
            )

        #############################################################
        # CodeBuild
        #############################################################
        application_bucket = s3.Bucket(self, "ApplicationBucket")

        code_build_role = iam.Role(
            self,
            "CodeBuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
        )
        code_build_policy = iam.Policy(
            self,
            "CodeBuildPolicy",
            policy_name="CodeBuildPolicy",
            statements=[
                iam.PolicyStatement(
                    actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    actions=["s3:GetObject", "s3:GetObjectVersion", "s3:PutObject"],
                    resources=["arn:*:s3:::*"],
                ),
            ],
        )
        code_build_policy.attach_to_role(code_build_role)

        app_package_build = codebuild.PipelineProject(
            self,
            "AppPackageBuild",
            project_name=f"{repository_name}Build",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.from_docker_registry("aws/codebuild/amazonlinux2-x86_64-standard:5.0"),
                compute_type=codebuild.ComputeType.SMALL,
                environment_variables={
                    "APP_S3_BUCKET": {"value": application_bucket.bucket_name}
                },
            ),
            environment_variables={
                "APP_S3_BUCKET": {"value": application_bucket.bucket_name}
            },
            role=code_build_role,
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
        )

        #############################################################
        # CodePipeline
        #############################################################
        artifact_bucket_store = s3.Bucket(self, "ArtifactBucketStore", versioned=True)

        code_pipeline_role = iam.Role(
            self,
            "CodePipelineRole",
            assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com"),
            inline_policies={
                "DefaultPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "s3:GetObject",
                                "s3:GetObjectVersion",
                                "s3:GetBucketVersioning",
                                "s3:CreateBucket",
                                "s3:PutObject",
                                "s3:PutBucketVersioning",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "codecommit:CancelUploadArchive",
                                "codecommit:GetBranch",
                                "codecommit:GetCommit",
                                "codecommit:GetUploadArchiveStatus",
                                "codecommit:UploadArchive",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["cloudwatch:*", "iam:PassRole"],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["lambda:InvokeFunction", "lambda:ListFunctions"],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "cloudformation:CreateStack",
                                "cloudformation:DeleteStack",
                                "cloudformation:DescribeStacks",
                                "cloudformation:UpdateStack",
                                "cloudformation:CreateChangeSet",
                                "cloudformation:DeleteChangeSet",
                                "cloudformation:DescribeChangeSet",
                                "cloudformation:ExecuteChangeSet",
                                "cloudformation:SetStackPolicy",
                                "cloudformation:ValidateTemplate",
                                "iam:PassRole",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["codebuild:BatchGetBuilds", "codebuild:StartBuild"],
                            resources=["*"],
                        ),
                    ]
                )
            },
        )

        cfn_deploy_role = iam.Role(
            self,
            "CFNDeployRole",
            assumed_by=iam.ServicePrincipal("cloudformation.amazonaws.com"),
            inline_policies={
                "DeployAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["*"],
                            resources=["*"],
                        )
                    ]
                )
            },
        )

        source_output = codepipeline.Artifact("SourceRepo")
        build_output = codepipeline.Artifact("CompiledCFNTemplate")

        codepipeline.Pipeline(
            self,
            "AppPipeline",
            pipeline_name=f"{repository_name}Pipeline",
            artifact_bucket=artifact_bucket_store,
            role=code_pipeline_role,
            pipeline_type=codepipeline.PipelineType.V2,
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        codepipeline_actions.CodeCommitSourceAction(
                            action_name="Source",
                            repository=source_repository,
                            branch="master",
                            output=source_output,
                        )
                    ],
                ),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="CodeBuild",
                            project=app_package_build,
                            input=source_output,
                            outputs=[build_output],
                        )
                    ],
                ),
                codepipeline.StageProps(
                    stage_name="Approval",
                    actions=[
                        codepipeline_actions.ManualApprovalAction(
                            action_name="ManualApproval",
                            additional_information="Please review the build artifacts before deploying.",
                        )
                    ],
                ),
                codepipeline.StageProps(
                    stage_name="Deploy",
                    actions=[
                        codepipeline_actions.CloudFormationCreateReplaceChangeSetAction(
                            action_name="CreateBetaChangeSet",
                            stack_name=f"{repository_name}BetaStack",
                            change_set_name=f"{repository_name}ChangeSet",
                            admin_permissions=True,
                            template_path=build_output.at_path("transformed.yaml"),
                            run_order=1,
                            role=cfn_deploy_role,
                        ),
                        codepipeline_actions.CloudFormationExecuteChangeSetAction(
                            action_name="ExecuteChangeSet",
                            stack_name=f"{repository_name}BetaStack",
                            change_set_name=f"{repository_name}ChangeSet",
                            run_order=2,
                            output=codepipeline.Artifact("AppDeploymentValues"),
                        )
                    ],
                ),
            ],
        )

        #############################################################
        # CloudFormation Outputs
        #############################################################
        CfnOutput(self, "SourceRepoURL", value=source_repository.repository_clone_url_http)
        CfnOutput(self, "S3ApplicationBucket", value=application_bucket.bucket_name)
        CfnOutput(self, "CodeBuildRoleArn", value=code_build_role.role_arn)
        CfnOutput(self, "S3PipelineBucket", value=artifact_bucket_store.bucket_name)
        CfnOutput(self, "CodePipelineRoleArn", value=code_pipeline_role.role_arn)
        CfnOutput(self, "CFNDeployRoleArn", value=cfn_deploy_role.role_arn)

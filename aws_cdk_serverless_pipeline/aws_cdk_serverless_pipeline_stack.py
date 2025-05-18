from typing import Any, cast

from aws_cdk import (
    CfnOutput,
    CfnParameter,
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
)
from constructs import Construct


class AwsCdkServerlessPipelineStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        application_name: str,
        environment: str, # environment name (dev, stg, prd)
        source_type: str, # source code repository type (github or codecommit)
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #############################################################
        # Parameters
        #############################################################
        repository_name_param = CfnParameter(
            self,
            "RepositoryName",
            type="String",
            description="The name of source code repository codecommit or github.",
        )
        branch_name_param = CfnParameter(
            self,
            "BranchName",
            type="String",
            description="The name of repository branch.",
        )
        github_owner_param = CfnParameter(
            self,
            "GithubOwner",
            default="",
            type="String",
            description="The name of github repository owner. Required if source_type context is github.",
        )
        github_connection_arn_param = CfnParameter(
            self,
            "GithubConnectionArn",
            default="",
            type="String",
            description="The name of code star connection arn of github. Required if source_type context is github.",
            no_echo=True,
        )

        repository_name = repository_name_param.value_as_string
        branch_name = branch_name_param.value_as_string
        github_owner_name = github_owner_param.value_as_string
        github_connection_arn_name = github_connection_arn_param.value_as_string

        #############################################################
        # CodePipeline Role
        #############################################################
        codepipeline_project_name = f"{application_name}Pipeline"
        artifact_bucket = s3.Bucket(self, "ArtifactBucketStore", versioned=True)

        codepipeline_role: iam.Role = self._generate_codepipeline_role(
            repository_name=repository_name,
            codepipeline_project_name=codepipeline_project_name,
            artifact_bucket=artifact_bucket,
        )

        #############################################################
        # Source
        #############################################################
        source_output = codepipeline.Artifact("SourceRepo")
        codepipeline_source_action = None
        if source_type == "github":
            codepipeline_source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
                action_name="GitHubSource",
                owner=github_owner_name,
                repo=repository_name,
                branch=branch_name,
                connection_arn=github_connection_arn_name,
                output=source_output,
            )
        elif source_type == "codecommit":
            codepipeline_source_action_role: iam.Role = self._generate_codepipeline_source_action_role(
                codepipeline_role=cast(iam.IRole, codepipeline_role),
                repository_name=repository_name
            )
            codepipeline_source_action = codepipeline_actions.CodeCommitSourceAction(
                action_name="CodeCommitSource",
                repository=codecommit.Repository.from_repository_name(
                    self,
                    "SourceRepository",
                    repository_name=repository_name
                ),
                branch=branch_name,
                output=source_output,
                role=cast(iam.IRole, codepipeline_source_action_role)
            )
        else:
            raise ValueError(f"Unsupported source_type: {source_type}")

        #############################################################
        # CodeBuild
        #############################################################
        codebuild_project_name = f"{application_name}Build"
        application_bucket = s3.Bucket(self, "ApplicationBucket")
        build_output = codepipeline.Artifact("CompiledCFNTemplate")

        codebuild_role: iam.Role = self._generate_codebuild_role(
            codebuild_project_name=codebuild_project_name,
            application_bucket=application_bucket
        )
        codepipeline_build_action_role: iam.Role = self._generate_codepipeline_build_action_role(
            codepipeline_role=cast(iam.IRole, codepipeline_role),
            codebuild_project_name=codebuild_project_name
        )

        codepipeline_build_action = codepipeline_actions.CodeBuildAction(
            action_name="CodeBuild",
            project=cast(codebuild.IProject, codebuild.PipelineProject(
                self,
                "AppPackageBuild",
                project_name=codebuild_project_name,
                environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
                    compute_type=codebuild.ComputeType.SMALL,
                    environment_variables={
                        "ENV": codebuild.BuildEnvironmentVariable(value=environment),
                        "APP_S3_BUCKET": codebuild.BuildEnvironmentVariable(value=application_bucket.bucket_name)
                    },
                ),
                role=cast(iam.IRole, codebuild_role),
                build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            )),
            input=source_output,
            outputs=[build_output],
            role=cast(iam.IRole, codepipeline_build_action_role)
        )

        #############################################################
        # Approval only stg and prd
        #############################################################
        codepipeline_manual_approval_action = None
        if environment in ["stg", "prd"]:
            codepipeline_manual_approval_action = codepipeline_actions.ManualApprovalAction(
                action_name="ManualApproval",
                additional_information="Please review the build artifacts before deploying.",
            )

        #############################################################
        # CfnDeploy
        #############################################################
        codepipeline_cfn_deploy_action_role: iam.Role = self._generate_codepipeline_cfn_deploy_action_role(
            codepipeline_role=cast(iam.IRole, codepipeline_role)
        )

        codepipeline_cloudformation_create_replace_change_set_action = codepipeline_actions.CloudFormationCreateReplaceChangeSetAction(
            action_name="CreateReplaceChangeSet",
            stack_name=f"{application_name}BetaStack",
            change_set_name=f"{application_name}ChangeSet",
            admin_permissions=True,
            template_path=build_output.at_path("transformed.yaml"),
            run_order=1,
            role=cast(iam.IRole, codepipeline_cfn_deploy_action_role),
        )

        codepipeline_cloudformation_execute_change_set_action = codepipeline_actions.CloudFormationExecuteChangeSetAction(
            action_name="ExecuteChangeSet",
            stack_name=f"{application_name}BetaStack",
            change_set_name=f"{application_name}ChangeSet",
            run_order=2,
            output=codepipeline.Artifact("AppDeploymentValues"),
        )

        #############################################################
        # CodePipeline
        #############################################################
        codepipeline_project = codepipeline.Pipeline(
            self,
            "AppPipeline",
            pipeline_name=codepipeline_project_name,
            artifact_bucket=artifact_bucket,
            role=cast(iam.IRole, codepipeline_role),
            pipeline_type=codepipeline.PipelineType.V2,
        )

        codepipeline_project.add_stage(
            stage_name="Source",
            actions=[codepipeline_source_action],
        )

        codepipeline_project.add_stage(
            stage_name="Build",
            actions=[codepipeline_build_action],
        )

        if codepipeline_manual_approval_action is not None:
            codepipeline_project.add_stage(
                stage_name="Approval",
                actions=[codepipeline_manual_approval_action],
            )

        codepipeline_project.add_stage(
            stage_name="CfnDeploy",
            actions=[
                codepipeline_cloudformation_create_replace_change_set_action,
                codepipeline_cloudformation_execute_change_set_action
            ],
        )


        #############################################################
        # CloudFormation Outputs
        #############################################################
        CfnOutput(self, "S3ApplicationBucket", value=application_bucket.bucket_name)
        CfnOutput(self, "CodeBuildRoleArn", value=codebuild_role.role_arn)
        CfnOutput(self, "S3PipelineBucket", value=artifact_bucket.bucket_name)
        CfnOutput(self, "CodePipelineRoleArn", value=codepipeline_role.role_arn)
        CfnOutput(self, "CFNDeployRoleArn", value=codepipeline_cfn_deploy_action_role.role_arn)


    def _generate_codebuild_role(
        self,
        codebuild_project_name: str,
        application_bucket: s3.Bucket
    ) -> iam.Role:
        codebuild_role = iam.Role(
            self,
            "CodeBuildRole",
            assumed_by=cast(iam.IPrincipal, iam.ServicePrincipal("codebuild.amazonaws.com")),
        )
        codebuild_policy = iam.Policy(
            self,
            "CodeBuildPolicy",
            policy_name="CodeBuildPolicy",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    resources=[
                        f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/codebuild/{codebuild_project_name}*"
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        "s3:GetObject",
                        "s3:GetObjectVersion",
                        "s3:PutObject"
                    ],
                    resources=[
                        f"arn:aws:s3:::{application_bucket.bucket_name}/*"
                    ],
                ),
            ],
        )
        codebuild_policy.attach_to_role(cast(iam.IRole, codebuild_role))

        return codebuild_role

    def _generate_codepipeline_role(
        self,
        repository_name: str,
        codepipeline_project_name: str,
        artifact_bucket: s3.Bucket,
    ) -> iam.Role:
        code_pipeline_policy_statments = [
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:GetBucketVersioning",
                    "s3:CreateBucket",
                    "s3:PutObject",
                    "s3:PutBucketVersioning",
                ],
                resources=[
                    f"arn:aws:s3:::{artifact_bucket.bucket_name}",
                    f"arn:aws:s3:::{artifact_bucket.bucket_name}/*",
                ],
            ),
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:*"
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/codepipeline/{codepipeline_project_name}*"
                ],
            ),
            iam.PolicyStatement(
                actions=[
                    "lambda:InvokeFunction",
                    "lambda:ListFunctions"
                ],
                resources=[
                    f"arn:aws:lambda:{self.region}:{self.account}:function:{repository_name}*"
                ],
            ),
            iam.PolicyStatement(
                actions=[
                    "iam:PassRole"
                ],
                resources=["*"]
            )
        ]

        return iam.Role(
            self,
            "CodePipelineRole",
            assumed_by=cast(iam.IPrincipal, iam.ServicePrincipal("codepipeline.amazonaws.com")),
            inline_policies={
                "DefaultPolicy": iam.PolicyDocument(
                    statements=code_pipeline_policy_statments
                )
            },
        )

    def _generate_codepipeline_source_action_role(
        self,
        codepipeline_role: iam.IRole,
        repository_name: str
    ) -> iam.Role:
        return iam.Role(
            self,
            "SourceActionRole",
            assumed_by=cast(iam.IPrincipal, iam.CompositePrincipal(
                cast(iam.IPrincipal, iam.ServicePrincipal("codepipeline.amazonaws.com")),
                cast(iam.IPrincipal, iam.ArnPrincipal(codepipeline_role.role_arn))),
            ),
            inline_policies={
                "SourceAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "codecommit:GetBranch",
                                "codecommit:GetCommit",
                                "codecommit:UploadArchive",
                                "codecommit:GetUploadArchiveStatus",
                                "codecommit:CancelUploadArchive",
                            ],
                            resources=[
                                f"arn:aws:codecommit:{self.region}:{self.account}:{repository_name}"
                            ],
                        )
                    ]
                )
            },
        )

    def _generate_codepipeline_build_action_role(
        self,
        codepipeline_role: iam.IRole,
        codebuild_project_name: str
    ) -> iam.Role:
        return iam.Role(
            self,
            "BuildActionRole",
            assumed_by=cast(iam.IPrincipal, iam.CompositePrincipal(
                cast(iam.IPrincipal, iam.ServicePrincipal("codebuild.amazonaws.com")),
                cast(iam.IPrincipal, iam.ArnPrincipal(codepipeline_role.role_arn))),
            ),
            inline_policies={
                "BuildAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "codebuild:BatchGetBuilds",
                                "codebuild:StartBuild",
                            ],
                            resources=[
                                f"arn:aws:codebuild:{self.region}:{self.account}:project/{codebuild_project_name}"
                            ],
                        )
                    ]
                )
            },
        )

    def _generate_codepipeline_cfn_deploy_action_role(
            self,
            codepipeline_role: iam.IRole,
        ) -> iam.Role:
        return iam.Role(
            self,
            "CFNDeployRole",
            assumed_by=cast(iam.IPrincipal, iam.CompositePrincipal(
                cast(iam.IPrincipal, iam.ServicePrincipal("cloudformation.amazonaws.com")),
                cast(iam.IPrincipal, iam.ArnPrincipal(codepipeline_role.role_arn))),
            ),
            inline_policies={
                "DeployAccess": iam.PolicyDocument(
                    statements=[
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
                            ],
                            resources=[
                                f"arn:aws:cloudformation:{self.region}:{self.account}:stack/{self.stack_name}*"
                            ],
                        )
                    ]
                )
            },
        )

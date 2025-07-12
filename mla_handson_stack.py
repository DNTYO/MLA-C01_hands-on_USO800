from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_sagemaker as sagemaker,
    aws_glue as glue,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    RemovalPolicy,
    Duration
)
from constructs import Construct

class MlaHandsonStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC for secure networking
        vpc = ec2.Vpc(self, "MlaVpc", max_azs=2)

        # S3 Buckets for data storage
        raw_data_bucket = s3.Bucket(
            self, "RawDataBucket",
            bucket_name=f"mla-raw-data-{self.account}-{self.region}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        processed_data_bucket = s3.Bucket(
            self, "ProcessedDataBucket", 
            bucket_name=f"mla-processed-data-{self.account}-{self.region}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        model_artifacts_bucket = s3.Bucket(
            self, "ModelArtifactsBucket",
            bucket_name=f"mla-model-artifacts-{self.account}-{self.region}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # DynamoDB for real-time data
        inference_cache_table = dynamodb.Table(
            self, "InferenceCacheTable",
            table_name="mla-inference-cache",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # RDS Aurora for structured data
        aurora_cluster = rds.DatabaseCluster(
            self, "AuroraCluster",
            engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_8_0_35),
            instance_props=rds.InstanceProps(
                instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.SMALL),
                vpc=vpc
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        # IAM Role for SageMaker
        sagemaker_execution_role = iam.Role(
            self, "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
            ]
        )

        # SageMaker Domain for Studio
        sagemaker_domain = sagemaker.CfnDomain(
            self, "SageMakerDomain",
            auth_mode="IAM",
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=sagemaker_execution_role.role_arn
            ),
            domain_name="mla-handson-domain",
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
            vpc_id=vpc.vpc_id
        )

        # SageMaker User Profile
        sagemaker.CfnUserProfile(
            self, "SageMakerUserProfile",
            domain_id=sagemaker_domain.attr_domain_id,
            user_profile_name="mla-user",
            user_settings=sagemaker.CfnUserProfile.UserSettingsProperty(
                execution_role=sagemaker_execution_role.role_arn
            )
        )

        # Glue Database for Data Catalog
        glue_database = glue.CfnDatabase(
            self, "GlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="mla_data_catalog",
                description="MLA handson data catalog"
            )
        )

        # IAM Role for Glue
        glue_role = iam.Role(
            self, "GlueRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
            ]
        )

        # Lambda function for lightweight processing
        lambda_function = lambda_.Function(
            self, "DataProcessingLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import json
import boto3

def handler(event, context):
    # Simple data processing logic
    return {
        'statusCode': 200,
        'body': json.dumps('Data processed successfully')
    }
            """),
            timeout=Duration.minutes(5)
        )

        # Grant Lambda permissions to access S3 buckets
        raw_data_bucket.grant_read_write(lambda_function)
        processed_data_bucket.grant_read_write(lambda_function)
        inference_cache_table.grant_read_write_data(lambda_function)

        # API Gateway for Lambda
        api = apigateway.RestApi(
            self, "MlaApi",
            rest_api_name="MLA Handson API"
        )

        lambda_integration = apigateway.LambdaIntegration(lambda_function)
        api.root.add_method("POST", lambda_integration)
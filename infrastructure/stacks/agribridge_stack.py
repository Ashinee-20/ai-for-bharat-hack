"""Main CDK stack for AgriBridge AI platform."""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_logs as logs,
    aws_iam as iam,
    aws_opensearchservice as opensearch,
)
from constructs import Construct


class AgriBridgeStack(Stack):
    """Main infrastructure stack for AgriBridge AI platform."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC for RDS and OpenSearch
        vpc = ec2.Vpc(
            self,
            "AgriBridgeVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Isolated", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=24
                ),
            ],
        )

        # DynamoDB Tables
        self.create_dynamodb_tables()

        # RDS PostgreSQL
        self.create_rds_database(vpc)

        # OpenSearch
        self.create_opensearch_domain(vpc)

        # S3 Bucket
        self.create_s3_bucket()

        # Lambda Layer for shared dependencies
        self.create_lambda_layer()

        # API Gateway
        self.create_api_gateway()

    def create_dynamodb_tables(self) -> None:
        """Create DynamoDB tables."""
        
        # Farmers Table
        self.farmers_table = dynamodb.Table(
            self,
            "FarmersTable",
            table_name="agribridge-farmers",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

        # GSI for district-based queries
        self.farmers_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK", type=dynamodb.AttributeType.STRING
            ),
        )

        # Price Cache Table
        self.price_cache_table = dynamodb.Table(
            self,
            "PriceCacheTable",
            table_name="agribridge-price-cache",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="TTL",
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

        # Query Log Table
        self.query_log_table = dynamodb.Table(
            self,
            "QueryLogTable",
            table_name="agribridge-query-logs",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

        # Conversation Context Table
        self.conversation_table = dynamodb.Table(
            self,
            "ConversationTable",
            table_name="agribridge-conversations",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="TTL",
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

    def create_rds_database(self, vpc: ec2.Vpc) -> None:
        """Create RDS PostgreSQL database with PostGIS."""
        
        # Security group for RDS
        db_security_group = ec2.SecurityGroup(
            self,
            "DBSecurityGroup",
            vpc=vpc,
            description="Security group for RDS PostgreSQL",
            allow_all_outbound=True,
        )

        # RDS instance
        self.database = rds.DatabaseInstance(
            self,
            "AgriBridgeDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15_4
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[db_security_group],
            multi_az=True,
            allocated_storage=20,
            max_allocated_storage=100,
            storage_encrypted=True,
            database_name="agribridge",
            backup_retention=Duration.days(7),
            deletion_protection=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

    def create_opensearch_domain(self, vpc: ec2.Vpc) -> None:
        """Create OpenSearch domain for vector search."""
        
        # Security group for OpenSearch
        opensearch_security_group = ec2.SecurityGroup(
            self,
            "OpenSearchSecurityGroup",
            vpc=vpc,
            description="Security group for OpenSearch",
            allow_all_outbound=True,
        )

        self.opensearch_domain = opensearch.Domain(
            self,
            "AgriBridgeOpenSearch",
            version=opensearch.EngineVersion.OPENSEARCH_2_11,
            capacity=opensearch.CapacityConfig(
                data_node_instance_type="t3.small.search",
                data_nodes=2,
            ),
            ebs=opensearch.EbsOptions(
                volume_size=20,
                volume_type=ec2.EbsDeviceVolumeType.GP3,
            ),
            vpc=vpc,
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)],
            security_groups=[opensearch_security_group],
            encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True),
            node_to_node_encryption=True,
            enforce_https=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

    def create_s3_bucket(self) -> None:
        """Create S3 bucket for storage."""
        
        self.storage_bucket = s3.Bucket(
            self,
            "AgriBridgeStorage",
            bucket_name="agribridge-storage",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    noncurrent_version_expiration=Duration.days(90),
                )
            ],
        )

    def create_lambda_layer(self) -> None:
        """Create Lambda layer for shared dependencies."""
        
        self.lambda_layer = lambda_.LayerVersion(
            self,
            "AgriBridgeDependencies",
            code=lambda_.Code.from_asset("../lambda-layer"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Shared dependencies for AgriBridge Lambda functions",
        )

    def create_api_gateway(self) -> None:
        """Create API Gateway."""
        
        # REST API
        self.api = apigateway.RestApi(
            self,
            "AgriBridgeAPI",
            rest_api_name="AgriBridge API",
            description="API for AgriBridge AI platform",
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                throttling_rate_limit=1000,
                throttling_burst_limit=2000,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
            ),
        )

        # CloudWatch log group for API Gateway
        logs.LogGroup(
            self,
            "APIGatewayLogs",
            log_group_name=f"/aws/apigateway/{self.api.rest_api_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )

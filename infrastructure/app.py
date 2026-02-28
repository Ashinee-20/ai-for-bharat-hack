#!/usr/bin/env python3
"""AWS CDK application entry point."""

import aws_cdk as cdk
from stacks.agribridge_stack import AgriBridgeStack

app = cdk.App()

AgriBridgeStack(
    app,
    "AgriBridgeStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "ap-south-1",
    ),
    description="AgriBridge AI Platform Infrastructure",
)

app.synth()

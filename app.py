#!/usr/bin/env python3
import aws_cdk as cdk
from mla_handson_stack import MlaHandsonStack

app = cdk.App()
MlaHandsonStack(app, "MlaHandsonStack")
app.synth()
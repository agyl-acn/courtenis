"""
Lambda handler — the only file that changes between local and AWS.
Mangum is the adapter that makes FastAPI run on AWS Lambda.
"""

from mangum import Mangum
from src.api import app

# This handler is invoked by AWS Lambda
handler = Mangum(app, lifespan="off")

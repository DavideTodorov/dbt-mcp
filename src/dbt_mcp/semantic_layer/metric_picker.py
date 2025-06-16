import boto3
import logging as log
import os


def get_bedrock_client():
    """
    Creates and returns a properly configured AWS Bedrock client based on environment variables.

    Returns:
        boto3.client: Configured Bedrock client
    """
    try:
        # Get AWS credentials from environment variables
        aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        aws_region = os.environ.get("AWS_REGION", "eu-west-1")

        # Create the Bedrock client with explicit credentials
        if aws_access_key and aws_secret_key:
            log.info(
                f"Initializing Bedrock client with explicit credentials in region {aws_region}")
            bedrock_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=aws_region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        else:
            raise Exception("AWS credentials are not present!")

        return bedrock_client
    except Exception as e:
        log.error(f"Failed to initialize Bedrock client: {str(e)}")
        raise


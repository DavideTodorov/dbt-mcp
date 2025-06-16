import boto3
import logging
import os
from dbt_mcp.semantic_layer.client import get_semantic_layer_fetcher
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """
    Creates and returns a properly configured AWS Bedrock client based on environment variables.

    Returns:
        boto3.client: Configured Bedrock client
    """
    try:
        load_dotenv()
        # Get AWS credentials from environment variables
        aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        aws_region = os.environ.get("AWS_REGION", "eu-west-1")

        # Create the Bedrock client with explicit credentials
        if aws_access_key and aws_secret_key:
            logger.info(
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
        logger.error(f"Error creating Bedrock client: {e}")
        raise


def determine_correct_metric(all_metrics: list[str], user_input) -> list[str]:
    llm = get_bedrock_client()

    prompt = f"""
    You are a helpful assistant that helps users find the correct metric based on their input.
    The user input is: "{user_input}"
    The available metrics are: {all_metrics}
    Please return the most relevant metric(s) that match the user's input.
    If no metrics match, return an empty list.
    You need to be 100% sure about the metric you return.
    If you are not sure, return an empty list. Do not make any assumptions or guesses.
    """

    try:
        load_dotenv()
        bedrock_model = os.getenv("AWS_BEDROCK_MODEL_ID")
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "temperature": 0.0
        }

        response = llm.invoke_model(
            model_id=bedrock_model,
            body=request_body
        )
        response_body = response.get("body").read().decode("utf-8")
    except Exception as e:
        logger.error(f"Error invoking Bedrock model: {e}")
        return []

    print(f"Response from Bedrock: {response_body}")

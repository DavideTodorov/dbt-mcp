from urllib import response
import boto3
import logging
import os
from dbt_mcp.semantic_layer.client import get_semantic_layer_fetcher
from dotenv import load_dotenv
import json
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


def determine_correct_metric(all_metrics: list, user_input) -> list:
    """
    Determines the most relevant metric based on user input using a Bedrock LLM.
    
    Args:
        all_metrics: List of MetricToolResponse objects containing available metrics
        user_input: The user's natural language query
        
    Returns:
        list: Either an empty list if no match is found, or a list containing the single
             MetricToolResponse object that best matches the user's query
    """
    logger.info("Starting metric determination process...")
    llm = get_bedrock_client()

    prompt = f"""
    You are a data analytics expert tasked with identifying the single most relevant metric from a dbt semantic layer based on a user query.

    # User Query
    "{user_input}"

    # Available Metrics
    {all_metrics}

    # Task
    Identify the SINGLE most relevant MetricToolResponse object from the available metrics list that best matches the user's query.

    # Analysis Instructions
    1. Analyze the semantic meaning of the user query to understand their data need
    2. Carefully compare the query against each metric's properties:
       - name: The technical identifier of the metric
       - label: The human-readable display name
       - description: The detailed explanation of what the metric measures
       - type: The calculation type (e.g., SIMPLE)
    3. Use these criteria for determining relevance:
       - Direct semantic match between query intent and metric purpose
       - Business terminology alignment between query and metric descriptions
       - Implicit business need that the metric would satisfy
       - Consider common synonyms and related business terms (e.g., "revenue" ~ "sales" ~ "income")

    # Response Format
    Return the COMPLETE single most relevant MetricToolResponse object AS IS, exactly as it appears in the input list.
    If no metrics match with high confidence, return an empty list [].

    # Example Response (if a match is found)
    MetricToolResponse(name='total_revenue', type='SIMPLE', label='Total Revenue', description='Total revenue from all orders')

    # Critical Requirements
    - Return ONE complete MetricToolResponse object, not just its name
    - If multiple metrics seem relevant, choose only the SINGLE best match
    - Do not modify the metric object's structure or content
    - Do not add explanations or additional text in your response
    - If no metrics match with high confidence, return an empty list []
    """

    logger.info(f"Prompt for Bedrock: {prompt}")
    try:
        load_dotenv()
        bedrock_model = os.environ.get("AWS_BEDROCK_MODEL")
        logger.info(f"Using Bedrock model: {bedrock_model}")
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
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
            modelId=bedrock_model,
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
    except Exception as e:
        logger.error(f"Error invoking Bedrock model: {e}")
        return []

    logger.info(f"Response from Bedrock: {response_body}")

    try:
        assistant_response = response_body.get('content', [])
        if assistant_response and len(assistant_response) > 0:
            result_text = assistant_response[0].get('text', '').strip()
            logger.info(f"Extracted response text: {result_text}")

            if result_text == "[]" or "empty list" in result_text.lower():
                logger.info("No matching metric found, returning empty list")
                return []

            for metric in all_metrics:
                metric_str = str(metric).replace(" ", "")
                result_text_normalized = result_text.replace(" ", "")

                if metric_str in result_text_normalized:
                    logger.info(f"Found matching metric: {metric}")
                    return [metric]

            logger.warning(
                f"Couldn't find exact match for LLM response: {result_text}")
            return []

        else:
            logger.warning("Empty or invalid response from LLM")
            return []

    except Exception as e:
        logger.error(f"Error parsing LLM response: {e}")
        return []

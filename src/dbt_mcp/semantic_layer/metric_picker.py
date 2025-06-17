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
        list: Either an empty list if no match is found, or a list containing the name
             of the single metric that best matches the user's query
    """
    logger.info("Starting metric determination process...")
    llm = get_bedrock_client()

    prompt = f"""
    You are a data analytics expert tasked with identifying the single most relevant metric from a dbt semantic layer based on a user query. You MUST be extremely conservative and precise in your matching.
    # User Query
    "{user_input}"

    # Available Metrics
    {all_metrics}

    # Task
    Identify the SINGLE most relevant MetricToolResponse object from the available metrics list that best matches the user's query. If there is ANY uncertainty, ambiguity, or imperfect match, return an empty list.

    # Strict Analysis Requirements
    1. The user query MUST have a clear, unambiguous intent that directly corresponds to ONE specific metric
    2. The metric's name, label, OR description MUST contain explicit terminology that directly matches the user's request
    3. There MUST be semantic alignment between:
       - The user's explicit data request AND the metric's stated purpose
       - The user's business context AND the metric's business domain
       - The user's measurement intent AND the metric's calculation scope

    # Matching Criteria (ALL must be satisfied)
    - EXACT semantic correspondence: The metric must measure precisely what the user is asking for
    - TERMINOLOGY alignment: Key terms in the query must be explicitly present or directly synonymous in the metric's properties
    - SCOPE compatibility: The metric's measurement scope must exactly match the user's intended analysis scope
    - CONTEXT appropriateness: The metric must be relevant to the user's implied business context

    # Assumptions STRICTLY FORBIDDEN
    - Do NOT assume related metrics are equivalent (e.g., "revenue" ≠ "profit" ≠ "sales")
    - Do NOT assume business context not explicitly stated in the query
    - Do NOT assume time periods, aggregation levels, or filtering criteria
    - Do NOT assume the user means something broader or narrower than stated
    - Do NOT make inferential leaps about user intent
    - Do NOT consider "close enough" matches as valid

    # Quality Thresholds for Match Acceptance
    - Confidence level: 99.99999% certainty required
    - Semantic match: Must be direct and unambiguous
    - Terminology overlap: Must be explicit, not inferred
    - Business relevance: Must be explicitly demonstrable from the metric description

    # Response Format
    Return the COMPLETE single most relevant MetricToolResponse object AS IS, exactly as it appears in the input list.
    If there is ANY doubt, uncertainty, ambiguity, or imperfect alignment, return an empty list [].

    # Example Response (ONLY if perfect match exists)
    MetricToolResponse(name='total_revenue', type='SIMPLE', label='Total Revenue', description='Total revenue from all orders')

    # Critical Requirements
    - Return ONE complete MetricToolResponse object ONLY if match confidence is 99.99999%
    - If multiple metrics seem relevant, return empty list [] (ambiguity = no match)
    - If the query is vague, unclear, or could apply to multiple metrics, return empty list []
    - If you need to make ANY assumption about user intent, return empty list []
    - Do not modify the metric object's structure or content
    - Do not add explanations, reasoning, or additional text in your response
    - When in doubt, return empty list []

    # Conservative Matching Philosophy
    Better to return no match than an imperfect match. Precision over recall. Zero tolerance for assumptions.
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
                    return [metric.name]

            logger.warning(
                f"Couldn't find exact match for LLM response: {result_text}")
            return []

        else:
            logger.warning("Empty or invalid response from LLM")
            return []

    except Exception as e:
        logger.error(f"Error parsing LLM response: {e}")
        return []

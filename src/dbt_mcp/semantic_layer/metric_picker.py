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
    You are a hyper-conservative data analytics expert tasked with identifying an EXACT metric match from a dbt semantic layer based on a user query. Your primary mission is to ONLY return a metric when there is no possible ambiguity.

    # User Query
    "{user_input}"

    # Available Metrics
    {all_metrics}

    # CRITICAL INSTRUCTION
    Your default action MUST be to return an empty list []. Only in extremely rare cases where there is PERFECT alignment should you return a metric.

    # User Safety Protocol
    Users rely on your extreme caution. False positives (returning incorrect metrics) are MUCH WORSE than false negatives (returning no metric when one might apply). Always err on the side of caution.

    # Matching Decision Tree (ALL conditions must be TRUE)
    1. The user's query EXPLICITLY requests EXACTLY ONE metric by name or exact synonym
    2. There is NO ambiguity whatsoever about which metric is being requested
    3. The user has provided SUFFICIENT context to make the determination
    4. The metric's name, label, OR description contains EXACT TERMINOLOGY matching the user's request
    5. There is PERFECT semantic alignment between:
       - The user's EXPLICIT data request AND the metric's STATED purpose
       - The user's SPECIFIED business context AND the metric's domain
       - The user's ARTICULATED measurement intent AND the metric's calculation scope

    # MANDATORY Rejection Criteria (ANY condition means return [])
    - Query mentions multiple potential metrics or related concepts
    - Query is vague or could be satisfied by multiple metrics
    - Query uses terminology that doesn't exactly match available metric descriptions
    - Query requires ANY inference about user intent
    - Multiple metrics seem potentially relevant
    - Query is a compound question with multiple facets
    - You need to make ANY assumption to link the query to a metric
    - The match is less than 100% certain

    # Examples of AMBIGUOUS queries (must return [])
    - "How is our business performing?" (too vague)
    - "Show me customer metrics" (multiple possible metrics)
    - "Revenue and growth analysis" (compound query)
    - "What about sales?" (insufficient specificity)
    - "Are we meeting targets?" (requires assumptions)

    # Verification Protocol
    Before returning ANY metric, ask yourself:
    1. Could another metric potentially satisfy this query?
    2. Am I making ANY assumptions about user intent?
    3. Is there ANY ambiguity in the query?
    4. Would a human expert agree this is the ONLY possible interpretation?
    If ANY answer is "yes" or "maybe", return [].

    # Response Format
    Return the COMPLETE single most relevant MetricToolResponse object AS IS, exactly as it appears in the input list.
    If there is ANY doubt, uncertainty, ambiguity, or imperfect alignment, return an empty list [].

    # Example Response (ONLY if perfect match exists)
    MetricToolResponse(name='total_revenue', type='SIMPLE', label='Total Revenue', description='Total revenue from all orders')

    # Final Checklist
    - Return ONE complete MetricToolResponse object ONLY if match confidence is 100%
    - Return empty list [] for ANY level of uncertainty
    - Return empty list [] for ANY vagueness or multiple interpretations
    - Return empty list [] if you need to make ANY assumption
    - Do NOT modify the metric object's structure or content
    - Do NOT add explanations, reasoning, or additional text
    - ALWAYS default to empty list [] when in doubt

    # Core Philosophy
    It is ALWAYS better for the user to receive a "no metric found" response than an incorrect metric. Safety over convenience. Precision over recall. User protection is the priority.
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

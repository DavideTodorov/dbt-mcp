import logging

from dbtsl.api.shared.query_params import GroupByParam
from mcp.server.fastmcp import FastMCP

from dbt_mcp.config.config import SemanticLayerConfig
from dbt_mcp.prompts.prompts import get_prompt
from dbt_mcp.semantic_layer.client import get_semantic_layer_fetcher
from dbt_mcp.semantic_layer.types import (
    DimensionToolResponse,
    EntityToolResponse,
    MetricToolResponse,
    OrderByParam,
    QueryMetricsSuccess,
)
from dbt_mcp.semantic_layer.metric_picker import determine_correct_metric

logger = logging.getLogger(__name__)


def register_sl_tools(dbt_mcp: FastMCP, config: SemanticLayerConfig) -> None:
    semantic_layer_fetcher = get_semantic_layer_fetcher(config)

    @dbt_mcp.tool(description=get_prompt("semantic_layer/list_metrics"))
    def list_metrics() -> list[MetricToolResponse] | str:
        return semantic_layer_fetcher.list_metrics()

    @dbt_mcp.tool(description=get_prompt("semantic_layer/get_dimensions"))
    def get_dimensions(metrics: list[str]) -> list[DimensionToolResponse] | str:
        return semantic_layer_fetcher.get_dimensions(metrics=metrics)

    @dbt_mcp.tool(description=get_prompt("semantic_layer/get_entities"))
    def get_entities(metrics: list[str]) -> list[EntityToolResponse] | str:
        return semantic_layer_fetcher.get_entities(metrics=metrics)

    @dbt_mcp.tool(description=get_prompt("semantic_layer/query_metrics"))
    def query_metrics(
        query: str
    ) -> str:

        all_metrics = semantic_layer_fetcher.list_metrics()

        logger.info(f"Before bedrock. Available metrics: {all_metrics}")
        metrics = determine_correct_metric(
            all_metrics=all_metrics,
            user_input=query,
        )
        logger.info(f"After bedrock. Selected metrics: {metrics}")
        
        # Check if determine_correct_metric returned an empty list
        if not metrics:
            # Format available metrics for display
            available_metrics = "\n".join([f"- {metric.name} ({metric.label}): {metric.description}" 
                                         for metric in all_metrics])
            return (f"I couldn't determine which specific metric you're looking for. "
                   f"Please be more specific and choose one of the available metrics:\n\n{available_metrics}")
        
        result = semantic_layer_fetcher.query_metrics(
            metrics=metrics,
        )
        if isinstance(result, QueryMetricsSuccess):
            return result.result
        else:
            return result.error

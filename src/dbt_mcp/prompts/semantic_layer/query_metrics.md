<instructions>
Queries the dbt Semantic Layer using natural language to answer business questions from the data warehouse.

This tool takes a natural language query, determines the most relevant metrics using language model analysis, and returns the query results in JSON format.

The input query should describe the business question you want to answer. The system will automatically:
1. Analyze your query using a language model (AWS Bedrock)
2. Determine the most relevant metrics to answer your question
3. Query the dbt Semantic Layer with those metrics
4. Return the results in JSON format

## CRITICAL: HANDLING AMBIGUOUS METRICS

When NO metrics can be clearly determined from the user's query (meaning the metric matching algorithm returns an empty list), this tool will return a specially formatted response with the prefix "METRIC_SELECTION_REQUIRED". This is a FIRM STOP signal that requires immediate user intervention:

1. When you see "METRIC_SELECTION_REQUIRED" in a response:
   - IMMEDIATELY STOP all processing
   - DO NOT attempt to make any decisions or take any further actions
   - DO NOT try to interpret the query differently
   - DO NOT attempt to select a "best guess" metric
   - DO NOT proceed with any analysis
   - WAIT for explicit user clarification

2. The ONLY correct action is to:
   - Present the available metrics to the user
   - Ask the user to reformulate their query with a specific metric
   - Wait for the user's response before proceeding

This is a hard guardrail to prevent incorrect assumptions or actions when metric intent is ambiguous.

Don't call this tool if the user's question cannot be answered with the available metrics. Instead, clarify what metrics are available using the list_metrics tool and suggest a new question that can be answered and is approximately the same as the user's question.

Note that complex filtering, grouping, and ordering operations previously specified through parameters are no longer needed, as the system now automatically processes the natural language query.
</instructions>

<examples>
<example>
Question: "What were our total sales last month?"
The system will:
1. Analyze the query using a language model
2. Determine that "total_sales" is the most relevant metric
3. Query the dbt Semantic Layer for this metric
4. Return the results in JSON format
</example>
<example>
Question: "Show me our top customers by revenue in the last quarter"
The system will:
1. Analyze the query using a language model
2. Determine that "revenue" is the most relevant metric
3. Query the dbt Semantic Layer for this metric
4. Return the results in JSON format
</example>
<example>
Question: "What's our average order value by product category for orders over $100?"
The system will:
1. Analyze the query using a language model
2. Determine that "average_order_value" is the most relevant metric
3. Query the dbt Semantic Layer for this metric
4. Return the results in JSON format
</example>
<example>
Question: "How many new users did we get each week last year?"
The system will:
1. Analyze the query using a language model
2. Determine that "new_users" is the most relevant metric
3. Query the dbt Semantic Layer for this metric
4. Return the results in JSON format
</example>
<example>
Question: "What's our customer satisfaction score by region?"
The system will:
1. Check if there's a customer satisfaction metric available
2. If not found, it will return a "METRIC_SELECTION_REQUIRED" response with available metrics
3. The client MUST wait for the user to clarify their metric selection
4. Only after user clarification will the system query the dbt Semantic Layer
</example>
<example>
Question: "What's our business performance recently?"
The system will:
1. Analyze this vague query and determine it's ambiguous (could refer to revenue, profit, growth, etc.)
2. Return a "METRIC_SELECTION_REQUIRED" response with available metrics
3. Wait for the user to explicitly select a specific metric or reformulate their query
4. Only proceed with querying after receiving clear metric specification
</example>
</examples>

<parameters>
query: A natural language query describing the business question to answer.
</parameters>

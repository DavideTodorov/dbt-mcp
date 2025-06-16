<instructions>
Queries the dbt Semantic Layer using natural language to answer business questions from the data warehouse.

This tool takes a natural language query, determines the most relevant metrics using language model analysis, and returns the query results in JSON format.

The input query should describe the business question you want to answer. The system will automatically:
1. Analyze your query using a language model (AWS Bedrock)
2. Determine the most relevant metrics to answer your question
3. Query the dbt Semantic Layer with those metrics
4. Return the results in JSON format

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
2. If not found, it may suggest an alternative like "net_promoter_score" as a proxy
3. Query the dbt Semantic Layer for the most relevant metric
4. Return the results in JSON format
</example>
</examples>

<parameters>
query: A natural language query describing the business question to answer.
</parameters>

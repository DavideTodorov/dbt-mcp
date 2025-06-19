# Query Metrics Tool Description

Queries the dbt Semantic Layer using natural language to answer business questions from the data warehouse.

This tool takes a natural language query, determines the most relevant metrics using language model analysis, and returns the query results in JSON format.

The input query should describe the business question you want to answer. The system will automatically:
1. Analyze your query using a language model (AWS Bedrock)
2. Determine the most relevant metrics to answer your question
3. Query the dbt Semantic Layer with those metrics
4. Return the results in JSON format

## CRITICAL: MANDATORY USER INTERVENTION FOR AMBIGUOUS QUERIES

When NO metrics can be clearly determined from the user's query (meaning the metric matching algorithm returns an empty list), this tool will return a specially formatted response with the prefix "METRIC_SELECTION_REQUIRED". This is an ABSOLUTE STOP signal that **MANDATES** immediate user intervention:

### STRICT PROTOCOL FOR MCP CLIENTS:

1. **IMMEDIATE HALT**: When you see "METRIC_SELECTION_REQUIRED" in any response:
   - **IMMEDIATELY CEASE** all processing and tool execution
   - **ABORT** any planned follow-up actions or queries
   - **DO NOT** attempt to make decisions on behalf of the user
   - **DO NOT** try alternative interpretations of the query
   - **DO NOT** attempt to select any "best guess" or "likely" metric
   - **DO NOT** proceed with any analysis, computation, or data processing
   - **DO NOT** call any other tools or functions
   - **STOP ALL AUTONOMOUS ACTIONS**

2. **MANDATORY USER ENGAGEMENT**: The MCP client **MUST**:
   - Present the complete list of available metrics to the user
   - Explicitly request the user to select a specific metric or reformulate their query
   - **WAIT** for explicit user input before taking any further action
   - **REQUIRE** the user to provide a clarified query that specifies the desired metric

3. **ABSOLUTE PROHIBITION**: Under **NO CIRCUMSTANCES** should the MCP client:
   - Continue processing without user clarification
   - Make assumptions about user intent
   - Select metrics autonomously
   - Attempt workarounds or alternative approaches
   - Take ANY action until the user provides explicit guidance

4. **RESUMPTION CONDITION**: The MCP client may **ONLY** resume operations after:
   - The user has provided a reformulated query with clear metric specification
   - The user has explicitly selected from the available metrics
   - The user has given direct instructions on how to proceed

This protocol serves as a hard guardrail to prevent incorrect assumptions, unauthorized actions, or unintended data processing when metric intent is ambiguous.

**IMPLEMENTATION NOTE**: If the user's question cannot be answered with the available metrics, use the `list_metrics` tool first to clarify available options, then suggest a reformulated question that matches available metrics and addresses the user's original intent.

## Examples

### Successful Query Processing
**Question**: "What were our total sales last month?"
**Process**:
1. Analyze query using language model
2. Determine "total_sales" is the relevant metric
3. Query dbt Semantic Layer
4. Return results in JSON format

### Ambiguous Query Requiring User Intervention
**Question**: "What's our business performance recently?"
**Process**:
1. Analyze vague query and determine it's ambiguous
2. Return "METRIC_SELECTION_REQUIRED" response with available metrics
3. **MANDATORY STOP** - Wait for user to specify desired metric
4. **ONLY** proceed after user clarification with specific metric selection

### Parameters
- `query`: A natural language query describing the business question to answer
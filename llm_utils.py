import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, Field # For data validation
from typing import List, Optional

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "o3-mini") # Using your preferred model

if not API_KEY:
    raise ValueError("CRITICAL: OPENAI_API_KEY not found in .env file or environment variables.")

client = OpenAI(api_key=API_KEY)

# --- Pydantic Models for LLM Response Validation ---
class LLMAnalysisResponse(BaseModel):
    summary: str
    queries: List[str] = Field(default_factory=list) # Default to empty list

# --- Core LLM Interaction ---
def get_llm_response(prompt_text, system_message="You are a helpful research assistant."):
    # ... (this function remains the same as before) ...
    print(f"💬 Calling LLM (model: {MODEL_NAME})...")
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt_text}
            ],
            #temperature=0.7,
            # response_format={"type": "json_object"}, # Consider if 'o3-mini' supports it well
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error calling OpenAI API: {e}")
        return None

# --- Prompt Generation Functions ---
# analyze_content_prompt and refine_answer_prompt remain the same as before.
# Just ensure analyze_content_prompt asks for "summary" and "queries" keys in JSON.
def analyze_content_prompt(current_query, content_from_url, source_url, research_so_far_context=""):
    # ... (same as the version in our last iteration of llm_utils.py) ...
    # Make sure the example JSON and instructions specify "summary" and "queries"
    context_section = "No prior research context available for this analysis."
    if research_so_far_context:
        context_section = f"""Your current research context based on previous findings is:
---
{research_so_far_context}
---"""

    return f"""{context_section}

You are an AI research assistant. Your current high-level research query is: "{current_query}".
You have just scraped the following content from the URL: {source_url}
--- BEGIN CONTENT ---
{content_from_url}
--- END CONTENT ---

Based *only* on the content provided above from {source_url}, and considering the overall research query and prior context:
1.  Provide a concise summary of the information from the scraped content that is relevant to the query "{current_query}". The summary should be self-contained and directly address the query based on this specific content. (max 150 words)
2.  Identify up to 3 new, specific, and distinct search queries (as a JSON list of strings). These queries should aim to dive deeper into related aspects, explore unanswered questions from this content, or clarify ambiguities relevant to the original query "{current_query}". They should be actionable search terms.

Return your response *only* as a JSON object with two keys: "summary" (a string) and "queries" (a list of strings).
Example JSON format:
{{
  "summary": "The content from the URL discusses X, Y, and Z in relation to the query. It specifically highlights A and B.",
  "queries": ["detailed explanation of X in context of query", "impact of Y on Z regarding query", "future of topic A related to query"]
}}
"""

def refine_answer_prompt(initial_query, research_findings_context):
    # ... (same as the version in our last iteration of llm_utils.py) ...
    return f"""You are an AI research synthesizer.
Your task is to provide a comprehensive answer to an initial research question based on a collection of summaries from various sources.

Initial Research Question: "{initial_query}"

Collected Research Summaries (Context):
---
{research_findings_context}
---

Based *only* on the provided collected research summaries, synthesize a comprehensive and coherent answer to the initial research question: "{initial_query}".
Structure your answer clearly. If there are conflicting points in the summaries, acknowledge them if significant. Do not introduce external knowledge.
"""


# --- Response Parsing with Pydantic Validation ---
def parse_llm_analysis_response(response_text: Optional[str]):
    """
    Parses the JSON response from the LLM for content analysis using Pydantic.
    Expects keys "summary" and "queries".
    """
    if not response_text:
        print("⚠️ LLM response was empty, cannot parse.")
        return "", []
    
    raw_json_str = response_text
    try:
        # Attempt to strip markdown code block fences if present
        if response_text.strip().startswith("```json"):
            raw_json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.strip().startswith("```"):
            raw_json_str = response_text.split("```")[1].strip()
        else:
            raw_json_str = response_text.strip()

        data = json.loads(raw_json_str) # First, ensure it's valid JSON
        
        # Validate with Pydantic
        validated_data = LLMAnalysisResponse(**data)
        print("✅ LLM response JSON structure validated with Pydantic.")
        return validated_data.summary, validated_data.queries

    except json.JSONDecodeError as e:
        print(f"❌ LLM response was not valid JSON: {e}")
        print(f"   Raw response snippet: {response_text[:500]}")
        return "", []
    except ValidationError as e:
        print(f"❌ LLM response JSON did not match expected schema (Pydantic validation failed):")
        for error in e.errors():
             print(f"   Field: {error['loc']}, Message: {error['msg']}, Type: {error['type']}")
        print(f"   Raw JSON attempted: {raw_json_str[:500]}")
        # Attempt to salvage if possible, or return defaults
        # For example, if only 'summary' is present and 'queries' is missing, Pydantic handles default_factory
        # If summary is missing, it's a bigger issue. For now, return defaults on validation error.
        summary_salvaged = ""
        queries_salvaged = []
        if isinstance(data, dict): # if json.loads worked but pydantic failed
            summary_salvaged = data.get("summary", "")
            queries_salvaged = data.get("queries", [])
            if not isinstance(queries_salvaged, list): queries_salvaged = []
            if summary_salvaged or queries_salvaged:
                 print(f"   Attempting to use salvaged data: summary present = {bool(summary_salvaged)}, queries found = {len(queries_salvaged)}")
                 return summary_salvaged, queries_salvaged
        return "", [] # Default on critical Pydantic error and no salvage
    except Exception as e:
        print(f"❌ Unexpected error parsing LLM response: {e}")
        print(f"   Raw response snippet: {response_text[:500]}")
        return "", []

# ... (if __name__ == '__main__': block for testing can be updated to use Pydantic model if needed)
if __name__ == '__main__':
    print("--- Testing llm_utils.py (with Pydantic) ---")
    
    # Mock LLM response for parsing
    mock_llm_json_response_valid = """
    ```json
    {
      "summary": "The content states that photosynthesis is a process.",
      "queries": ["how do plants store energy?", "what bacteria perform photosynthesis?"]
    }
    ```
    """
    mock_llm_json_response_missing_queries = """
    ```json
    {
      "summary": "Summary without queries field."
    }
    ```
    """
    mock_llm_json_response_invalid_queries_type = """
    ```json
    {
      "summary": "Summary with invalid queries type.",
      "queries": "this should be a list"
    }
    ```
    """
    mock_llm_json_response_bad_json = "```json { summary: 'bad json' "

    print("\nTesting valid response:")
    summary, queries = parse_llm_analysis_response(mock_llm_json_response_valid)
    print(f"  Parsed Summary: {summary}")
    print(f"  Parsed Queries: {queries}")

    print("\nTesting response missing 'queries' (should default to empty list):")
    summary, queries = parse_llm_analysis_response(mock_llm_json_response_missing_queries)
    print(f"  Parsed Summary: {summary}")
    print(f"  Parsed Queries: {queries}") # Should be []

    print("\nTesting response with invalid 'queries' type:")
    summary, queries = parse_llm_analysis_response(mock_llm_json_response_invalid_queries_type)
    print(f"  Parsed Summary: {summary}") # Might be salvaged
    print(f"  Parsed Queries: {queries}") # Should be [] due to salvage or pydantic error

    print("\nTesting bad JSON response:")
    summary, queries = parse_llm_analysis_response(mock_llm_json_response_bad_json)
    print(f"  Parsed Summary: {summary}")
    print(f"  Parsed Queries: {queries}")
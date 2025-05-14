import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("OPENAI_API_KEY")
# Default model is gpt-3.5-turbo, matching the Go project's likely default if unspecified
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "o3-mini")

if not API_KEY:
    raise ValueError("CRITICAL: OPENAI_API_KEY not found in .env file or environment variables.")

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY)

# --- Core LLM Interaction ---
def get_llm_response(prompt_text, system_message="You are a helpful research assistant."):
    """
    Sends a prompt to the LLM and returns its text response.
    """
    print(f"💬 Calling LLM (model: {MODEL_NAME})...")
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt_text}
            ],
            #temperature=0.7,  # A common default for balanced creativity/factuality
            # response_format={"type": "json_object"}, # Enable if consistently getting valid JSON and model supports it
        )
        # print(f"LLM Raw Response: {response.choices[0].message.content[:200]}...") # For debugging
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error calling OpenAI API: {e}")
        return None

# --- Prompt Generation Functions ---
def analyze_content_prompt(current_query, content_from_url, source_url, research_so_far_context=""):
    """
    Generates the prompt for the LLM to analyze scraped web content.
    This prompt asks the LLM to summarize the content and suggest new search queries.
    It mirrors the structure and intent of the Go project's `researcherPrompt`.
    """
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
    """
    Generates the prompt for the LLM to synthesize a final answer from all gathered research.
    Mirrors the Go project's `refinePrompt`.
    """
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

# --- Response Parsing ---
def parse_llm_analysis_response(response_text):
    """
    Parses the JSON response from the LLM's content analysis.
    Expects keys "summary" and "queries" as per `analyze_content_prompt`.
    """
    if not response_text:
        print("⚠️ LLM response was empty, cannot parse.")
        return "", []
    try:
        # Attempt to strip markdown code block fences if present
        if response_text.strip().startswith("```json"):
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.strip().startswith("```"): # More generic ``` stripping
            json_str = response_text.split("```")[1].strip()
        else:
            json_str = response_text.strip()

        data = json.loads(json_str)
        summary = data.get("summary", "")
        new_queries = data.get("queries", []) # Expecting "queries" key as per Go
        
        if not isinstance(new_queries, list):
            print(f"⚠️ LLM 'queries' field was not a list, received: {type(new_queries)}. Treating as no new queries.")
            new_queries = []
        return summary, new_queries
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing LLM JSON response: {e}")
        print(f"   Raw response snippet: {response_text[:500]}")
        # Fallback: try to find summary and queries heuristically (less reliable)
        # This part is optional and can be complex to make robust.
        # For now, returning empty on parse failure is safer.
        return "", [] 
    except Exception as e:
        print(f"❌ Unexpected error parsing LLM response: {e}")
        print(f"   Raw response snippet: {response_text[:500]}")
        return "", []

if __name__ == '__main__':
    # Example usage for testing this module directly
    print("--- Testing llm_utils.py ---")
    
    # Test analyze_content_prompt
    test_analyze_prompt = analyze_content_prompt(
        current_query="What is photosynthesis?",
        content_from_url="Photosynthesis is a process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy.",
        source_url="http://example.com/photosynthesis",
        research_so_far_context="Initial findings suggest photosynthesis is related to plants and energy."
    )
    print("\nGenerated Analysis Prompt:\n", test_analyze_prompt)
    
    # Mock LLM response for parsing
    mock_llm_json_response = """
    ```json
    {
      "summary": "The content states that photosynthesis is a process where plants, algae, and some bacteria convert sunlight into chemical energy.",
      "queries": ["how do plants store chemical energy from photosynthesis?", "what types of bacteria perform photosynthesis?"]
    }
    ```
    """
    summary, queries = parse_llm_analysis_response(mock_llm_json_response)
    print(f"\nParsed Summary: {summary}")
    print(f"Parsed Queries: {queries}")

    # Test refine_answer_prompt
    test_refine_prompt = refine_answer_prompt(
        initial_query="What are the benefits of exercise?",
        research_findings_context="Summary 1: Exercise improves cardiovascular health.\n\n---\n\nSummary 2: Regular physical activity can boost mood and reduce stress."
    )
    print("\nGenerated Refine Prompt:\n", test_refine_prompt)
    
    # To actually call the LLM (requires API key to be set)
    # if API_KEY:
    #     print("\nAttempting live LLM call for analysis (mocked content)...")
    #     live_response = get_llm_response(test_analyze_prompt)
    #     if live_response:
    #         summary, queries = parse_llm_analysis_response(live_response)
    #         print(f"Live Parsed Summary: {summary}")
    #         print(f"Live Parsed Queries: {queries}")
    #     else:
    #         print("Live LLM call failed or returned no response.")
    # else:
    #     print("\nSkipping live LLM call test as OPENAI_API_KEY is not set.")
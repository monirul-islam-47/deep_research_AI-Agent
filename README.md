
## Setup

1.  **Clone the Repository (or Create Files):**
    If this were a Git repository:
    ```bash
    git clone <repository-url>
    cd deep-research-py
    ```
    Otherwise, create the `deep-research-py` directory and place all the Python files (`main.py`, `research_agent.py`, etc.) into it as described.

2.  **Create a Python Virtual Environment (Recommended):**
    Open your terminal in the `deep-research-py` directory.
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    -   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```
    -   On Windows (Command Prompt):
        ```bash
        venv\Scripts\activate.bat
        ```
    -   On Windows (PowerShell):
        ```bash
        venv\Scripts\Activate.ps1
        ```
    You should see `(venv)` at the beginning of your terminal prompt.

3.  **Install Dependencies:**
    With the virtual environment activated, install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Key and Settings (`.env` file):**
    Create a file named `.env` in the root of the `deep-research-py` directory. Add your OpenAI API key and any optional overrides:

    ```env
    # Required: Your OpenAI API Key
    OPENAI_API_KEY="your_openai_api_key_here"

    # Optional: Override default settings
    # OPENAI_MODEL_NAME="gpt-4-turbo-preview"  # Default in llm_utils.py is "gpt-3.5-turbo"
    # MAX_DEPTH=2                             # Default in main.py is 2
    # MAX_SEARCH_RESULTS_PER_QUERY=5          # Default in research_agent.py is 5
    ```
    **Important:** Replace `"your_openai_api_key_here"` with your actual OpenAI API key.
    If you plan to use Git, add `.env` to your `.gitignore` file to prevent committing your API key.

## Usage

Once set up, you can run the tool from your terminal (ensure your virtual environment is active).

**Basic command:**
```bash
python main.py --query "Your research question here"
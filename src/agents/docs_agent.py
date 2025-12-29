import google.generativeai as genai
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv() # Load environment variables from .env file

# Retrieve API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class DocsAgent:
    """
    An agent that automatically generates professional, internship-ready documentation.
    """

    def __init__(self):
        if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
            print("WARNING: GEMINI_API_KEY not configured. Using simulated API calls.")
            self.model = None # Indicates using simulated calls
        else:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')

    def _make_gemini_api_call(self, prompt: str) -> str:
        """
        Makes a call to the Gemini API or simulates it if API key is not configured.
        """
        if self.model:
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Error making Gemini API call: {e}. Falling back to simulated response.")
                # This is a hardcoded response for demonstration purposes.
                return "\n# Project: Automated AI Workspace\n\n## 1. Introduction\nThis document provides an overview of the Automated AI Workspace, a project that integrates Microsoft Teams, a Gemini Coding Agent, and an MCP Server to create a seamless, automated workflow for software development tasks.\n\n## 2. High-Level Architecture\nThe system is composed of the following key components:\n- **Microsoft Teams Bot**: The user-facing interface for task management.\n- **Orchestrator Agent**: The \"brain\" of the system, responsible for task routing.\n- **MCP Server**: The backbone that provides tools and services.\n- **Gemini Coding Agent**: The agent responsible for code generation and modification.\n- **Automated Documentation Agent**: The agent that generates this documentation.\n\n## 3. Core Components\n(Detailed descriptions of each component would go here.)\n"

        else:
            print(f"--- Simulating Doc Generation API call with prompt: ---\n{prompt}\n-------------------------------------------")
            # This is a hardcoded response for demonstration purposes.
            return "\n# Project: Automated AI Workspace\n\n## 1. Introduction\nThis document provides an overview of the Automated AI Workspace, a project that integrates Microsoft Teams, a Gemini Coding Agent, and an MCP Server to create a seamless, automated workflow for software development tasks.\n\n## 2. High-Level Architecture\nThe system is composed of the following key components:\n- **Microsoft Teams Bot**: The user-facing interface for task management.\n- **Orchestrator Agent**: The \"brain\" of the system, responsible for task routing.\n- **MCP Server**: The backbone that provides tools and services.\n- **Gemini Coding Agent**: The agent responsible for code generation and modification.\n- **Automated Documentation Agent**: The agent that generates this documentation.\n\n## 3. Core Components\n(Detailed descriptions of each component would go here.)\n"


    def generate_architecture_docs(self, task_description: str, project_overview: str, git_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates comprehensive architecture documentation for the project.
        """
        if git_context:
            print(f"DocsAgent received Git context: {git_context}")

        prompt = f"""
        **Task:** {task_description}

        **Project Overview:**
        {project_overview}

        **Instructions:**
        1.  Analyze the project overview and the task description.
        2.  Generate a detailed architecture document that is easy to read and understand.
        3.  The document should be suitable for a new team member to get up to speed on the project.
        4.  Provide the output in Markdown format.
        """
        generated_docs = self._make_gemini_api_call(prompt)
        return generated_docs

    def generate_readme(self, project_name: str, description: str, git_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a README.md file for the project.
        """
        if git_context:
            print(f"DocsAgent received Git context: {git_context}")

        prompt = f"""
        **Project Name:** {project_name}

        **Description:**
        {description}

        **Instructions:**
        Generate a professional README.md file for the project.
        """
        return self._make_gemini_api_call(prompt)


# Example usage (for testing purposes)
if __name__ == "__main__":
    agent = DocsAgent()

    # --- Example 1: Generate Architecture Docs ---
    print("--- Example 1: Generate Architecture Docs ---")
    task1 = "Generate the initial architecture documentation for the project."
    overview1 = "An automated AI workspace integrating Teams, Gemini, and MCP."
    generated_docs = agent.generate_architecture_docs(task1, overview1)
    print(f"Generated Architecture Docs:\n```markdown\n{generated_docs}\n```")

    # --- Example 2: Generate a README ---
    print("\n--- Example 2: Generate a README ---")
    project_name2 = "My Awesome Project"
    description2 = "A project that does amazing things."
    generated_readme = agent.generate_readme(project_name2, description2)
    print(f"Generated README:\n```markdown\n{generated_readme}\n```")
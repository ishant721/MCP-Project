# Automated AI Workspace

This project is an automated AI workspace that integrates GitHub, a Gemini Coding Agent, an MCP Server, and Microsoft Teams to create a seamless, automated workflow for software development tasks, facilitating collaborative development by responding to Git events and providing status updates.

## 🚀 Getting Started

### Prerequisites

*   **Python 3.10+**
*   **pip** (Python package installer)
*   **Neo4j Desktop** (or a running Neo4j instance)
*   **ngrok** (recommended for local testing with GitHub Webhooks)
*   **GitHub Repository** (to set up webhooks)
*   **Microsoft Teams Account** (for receiving notifications)

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/automated-ai-workspace.git
    cd automated-ai-workspace
    ```
2.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
    *Note: You might encounter dependency resolution warnings during installation related to `langchain-core` and other `langchain` packages. These are typically `pip` trying to find the best compatible versions. For the current functionality, the installed versions should work, but keep an eye on them if you experience unexpected behavior.*

3.  **Configure environment variables:**
    *   Create a `.env` file in the root directory of the project.
    *   Add the following variables to the `.env` file, replacing the placeholder values:
        ```
        # .env file for configuration

        # Gemini API Key (required for Gemini Coding Agent and Docs Agent)
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

        # Microsoft Teams Incoming Webhook URL (for sending updates TO Teams)
        # Obtain this by creating an Incoming Webhook connector in a Teams channel.
        TEAMS_WEBHOOK_URL="YOUR_TEAMS_WEBHOOK_URL"

        # Neo4j Database Connection Details
        NEO4J_URI="bolt://localhost:7687"
        NEO4J_USER="neo4j"
        NEO4J_PASSWORD="password"

        # GitHub Webhook Secret (optional, for securing webhooks)
        # Generate a random strong string (e.g., using `openssl rand -hex 20`)
        GITHUB_WEBHOOK_SECRET="YOUR_GITHUB_WEBHOOK_SECRET"
        ```
        *   Obtain your `GEMINI_API_KEY` from the Google AI Studio.
        *   Create an Incoming Webhook connector in your desired Microsoft Teams channel (see instructions below) to get your `TEAMS_WEBHOOK_URL`.
        *   Adjust `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` if your Neo4j setup is different from the default.
        *   Generate a `GITHUB_WEBHOOK_SECRET` if you want to secure your GitHub webhooks. This should also be configured in your GitHub repository's webhook settings.

4.  **Start your Neo4j database:**
    *   Ensure it's running on the URI specified in your `.env` file (default: `bolt://localhost:7687`).

### Running the Application

This application consists of the **MCP Server** (FastAPI) which needs to run continuously.

1.  **Make the run script executable:**
    ```bash
    chmod +x run.sh
    ```
2.  **Run the MCP Server using the provided script:**
    ```bash
    ./run.sh
    ```
    This script will start the MCP Server (on `http://localhost:8000`) in the background. It will display its process ID.

    To stop the server, you can use `kill <PID>` (PID is displayed when `run.sh` starts), or `killall uvicorn` (use with caution).

### Integrations Setup

#### 1. GitHub Webhook Setup

This allows you to trigger your application's workflows based on GitHub events (e.g., push, pull request).

1.  **Expose your local MCP Server (for GitHub Webhooks):**
    *   Since your MCP Server runs locally (by default on `http://localhost:8000`), GitHub needs a way to reach it. **ngrok** is recommended for local development:
        ```bash
        ngrok http 8000
        ```
    *   ngrok will provide a public HTTPS URL (e.g., `https://xxxxxx.ngrok.io`). This is the URL GitHub will use to send webhook payloads. Keep ngrok running while testing.
2.  **Configure GitHub Webhook:**
    *   Go to your GitHub repository's settings (`Settings` -> `Webhooks`).
    *   Click "Add webhook".
    *   **Payload URL:** Enter your ngrok HTTPS URL followed by `/github-webhook`.
        *   Example: `https://xxxxxx.ngrok.io/github-webhook`
    *   **Content type:** Select `application/json`.
    *   **Secret:** If you configured `GITHUB_WEBHOOK_SECRET` in your `.env`, **enter the exact same secret string here.** This is crucial for signature verification.
    *   **Which events would you like to trigger this webhook?**
        *   Select "Let me select individual events."
        *   For a start, select:
            *   `Pushes` (for new commits)
            *   `Pull requests` (for PR activity)
        *   You might want others later (e.g., `Issues`, `Issue comments`).
    *   Ensure "Active" is checked.
    *   Click "Add webhook".

#### 2. Microsoft Teams Outbound Messaging Setup

This allows your application to send status updates and notifications to a Microsoft Teams channel.

1.  **Create an Incoming Webhook in Teams:**
    *   Go to the Microsoft Teams channel where you want your application to post updates.
    *   Click `...` (more options) next to the channel name, then select "Connectors".
    *   Search for "Incoming Webhook" and click "Add".
    *   Give it a name (e.g., "AI Workspace Notifications") and click "Create".
    *   **Copy the generated URL.** Paste this into your `.env` file for the `TEAMS_WEBHOOK_URL` variable. This URL allows your app to send Adaptive Cards to this specific Teams channel.
    *   Click "Done".

### How to Trigger Workflows and Receive Notifications

1.  **Ensure your MCP Server is running** (using `./run.sh`).
2.  **Ensure ngrok is running** and forwarding to port 8000 (if using GitHub webhooks).
3.  **Perform a Git action** in your configured GitHub repository (e.g., push a new commit, open a pull request).
4.  **Observe the console output** of the MCP Server for processing logs related to the GitHub event.
5.  **Check your configured Microsoft Teams channel** for task completion notifications from your application.

## 🧠 High-Level Architecture

*   **GitHub Webhooks**: The trigger for initiating workflows based on code changes and development activity.
*   **Orchestrator Agent (LangGraph)**: The "brain" of the system, responsible for task routing and understanding Git context.
*   **MCP Server (FastAPI)**: The backbone that provides tools and services, including the GitHub webhook listener.
*   **Gemini Coding Agent**: The agent responsible for code generation and modification.
*   **Automated Documentation Agent**: The agent that generates this documentation.
*   **Neo4j Context Graph**: Stores long-term memory of the project, linking tasks to Git events.
*   **Microsoft Teams (Incoming Webhook)**: Receives structured status updates and notifications from the application.

## 🧩 Core Components (Located in `src/`)

*   **`src/orchestrator/`**: Contains the LangGraph implementation of the orchestrator.
*   **`src/mcp-server/`**: Contains the FastAPI application for the MCP server, its tools, and the GitHub webhook listener.
*   **`src/agents/`**: Contains the Gemini Coding Agent and the Docs Agent.
*   **`src/memory/`**: Contains the Neo4j context graph related files.
*   **`src/docs/`**: Intended for generated documentation.
*   **`src/teams_messaging/`**: Contains the utility for sending messages to Microsoft Teams.

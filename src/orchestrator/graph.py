import requests
import json
from typing import TypedDict, Annotated, List, Union, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# --- MCP Server Configuration ---
MCP_SERVER_URL = "http://localhost:8000"

# --- 1. Define Graph State ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.
    """
    task_description: str
    task_id: Annotated[int, "The ID of the task in the MCP"]
    status_message: Annotated[str, "A message about the current status of the operation"]
    agent_outcome: Annotated[Union[BaseMessage, List[BaseMessage]], "The outcome of any agent/tool execution"]
    file_path: Annotated[str, "The path to the file to be modified"]
    code_changes: Annotated[List[str], "A list of code changes made by the coding agent"]
    documentation: Annotated[str, "The generated documentation"]
    loom_checklist: Annotated[str, "The generated Loom checklist"]
    
    # New GitHub-related fields
    repo_url: Optional[str]
    head_commit_id: Optional[str]
    changed_files: Annotated[List[str], "Files changed in the commit/PR"]
    github_event_type: Optional[str]
    github_payload: Optional[Dict[str, Any]] # Store full payload for detailed analysis if needed
    git_context: Optional[Dict[str, Any]] # Add git_context to GraphState

# --- 2. MCP API Client ---
def create_mcp_task(description: str, context: Dict[str, Any] = None) -> dict:
    """Creates a new task in the MCP server."""
    if context is None:
        context = {}
    response = requests.post(f"{MCP_SERVER_URL}/tasks/", params={"task_description": description}, json={"context": context})
    response.raise_for_status()
    return response.json()

def update_mcp_task_status(task_id: int, status: str) -> dict:
    """Updates the status of an existing task in the MCP server."""
    response = requests.put(f"{MCP_SERVER_URL}/tasks/{task_id}", params={"status": status})
    response.raise_for_status()
    return response.json()

def write_file(file_path: str, content: str) -> str:
    """Writes content to a file."""
    response = requests.post(f"{MCP_SERVER_URL}/tools/generate_code/write_file", json={"file_path": file_path, "content": content})
    response.raise_for_status()
    return response.json()

def add_neo4j_node(label: str, properties: dict) -> dict:
    """Adds a node to the Neo4j graph."""
    response = requests.post(f"{MCP_SERVER_URL}/tools/neo4j_memory/add_node", json={"label": label, "properties": properties})
    response.raise_for_status()
    return response.json()

def add_neo4j_relationship(start_node_label: str, start_node_properties: dict,
                             end_node_label: str, end_node_properties: dict,
                             relationship_type: str) -> dict:
    """Adds a relationship between two nodes in the Neo4j graph."""
    response = requests.post(f"{MCP_SERVER_URL}/tools/neo4j_memory/add_relationship", json={
        "start_node_label": start_node_label,
        "start_node_properties": start_node_properties,
        "end_node_label": end_node_label,
        "end_node_properties": end_node_properties,
        "relationship_type": relationship_type
    })
    response.raise_for_status()
    return response.json()

def generate_loom_checklist(task_description: str, code_changes: list[str]) -> str:
    """Generates a Loom checklist."""
    response = requests.post(f"{MCP_SERVER_URL}/tools/loom_helper/generate_demo_checklist", json={"task_description": task_description, "code_changes": code_changes})
    response.raise_for_status()
    return response.json()

# --- Utility to extract task from GitHub context ---
def extract_task_from_git_context(git_context: Dict[str, Any]) -> str:
    event_type = git_context.get("event_type")
    payload = git_context.get("payload", {})
    repo_name = git_context.get("repo_name", "unknown/unknown")

    if event_type == "push":
        head_commit = payload.get("head_commit", {})
        message = head_commit.get("message", f"New push to {repo_name}")
        return f"Analyze recent push to {repo_name}: {message}"
    elif event_type == "pull_request":
        pr = payload.get("pull_request", {})
        action = payload.get("action", "activity")
        title = pr.get("title", f"Pull request activity in {repo_name}")
        return f"Process pull request '{title}' ({action}) in {repo_name}"
    elif event_type == "issues" and payload.get("action") == "opened":
        issue = payload.get("issue", {})
        title = issue.get("title", "New issue")
        body = issue.get("body", "")
        return f"Task from new issue '{title}': {body}"
    else:
        return f"Handle GitHub event '{event_type}' for {repo_name}"

def get_changed_files_from_git_context(git_context: Dict[str, Any]) -> List[str]:
    event_type = git_context.get("event_type")
    payload = git_context.get("payload", {})
    
    changed_files = []
    if event_type == "push":
        head_commit = payload.get("head_commit", {})
        changed_files.extend(head_commit.get("added", []))
        changed_files.extend(head_commit.get("modified", []))
        changed_files.extend(head_commit.get("removed", []))
    elif event_type == "pull_request":
        # For PRs, getting changed files usually requires an extra API call.
        # For simplicity, we'll just indicate a PR event triggered changes.
        # In a real scenario, you'd use PyGithub to fetch PR files.
        changed_files.append(f"Pull Request #{payload.get('number')} changed files")
    return list(set(changed_files)) # Remove duplicates

# --- 3. Define Graph Nodes ---

def create_task_node(state: GraphState) -> GraphState:

    """Node to create a task in the MCP based on initial state or GitHub context."""

    print(f"--- Node: create_task_node ---")

    print(f"Input: task_description='{state['task_description']}', git_context_present={bool(state.get('git_context'))}")

    

    task_description = state["task_description"]

    git_context = state.get("git_context")



    if git_context:

        task_description = extract_task_from_git_context(git_context)

        # Pass GitHub context to MCP task for later retrieval

        task = create_mcp_task(task_description, context=git_context)

        

        # Populate state with GitHub details

        repo_url = git_context.get("repo_url")

        head_commit_id = None

        changed_files = get_changed_files_from_git_context(git_context)



        if git_context["event_type"] == "push":

            head_commit_id = git_context.get("payload", {}).get("head_commit", {}).get("id")

        elif git_context["event_type"] == "pull_request":

            head_commit_id = git_context.get("payload", {}).get("pull_request", {}).get("head", {}).get("sha")



        state.update({

            "task_id": task["id"],

            "status_message": f"Task created from GitHub event: {task_description}",

            "repo_url": repo_url,

            "head_commit_id": head_commit_id,

            "changed_files": changed_files,

            "github_event_type": git_context["event_type"],

            "github_payload": git_context["payload"]

        })

        print(f"Output: Task ID: {task['id']}, Status: {state['status_message']}, Repo: {repo_url}")

    else:

        task = create_mcp_task(task_description)

        state.update({

            "task_id": task["id"],

            "status_message": f"Task created: {task_description}"

        })

        print(f"Output: Task ID: {task['id']}, Status: {state['status_message']}")

    

    return state



class RouteQuery(BaseModel):

    """Route a user query to the most relevant agent."""

    datasource: str = Field(

        description="Given a user query choose which agent to route it to.",

        enum=["coding", "docs", "general"],

    )



import os
import shutil
import subprocess
from agents.gemini_coder import GeminiCodingAgent
import requests
import json
from typing import TypedDict, Annotated, List, Union, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# --- MCP Server Configuration ---
MCP_SERVER_URL = "http://localhost:8000"

# --- 1. Define Graph State ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.
    """
    task_description: str
    task_id: Annotated[int, "The ID of the task in the MCP"]
    status_message: Annotated[str, "A message about the current status of the operation"]
    agent_outcome: Annotated[Union[BaseMessage, List[BaseMessage]], "The outcome of any agent/tool execution"]
    file_path: Annotated[str, "The path to the file to be modified"]
    code_changes: Annotated[List[str], "A list of code changes made by the coding agent"]
    documentation: Annotated[str, "The generated documentation"]
    loom_checklist: Annotated[str, "The generated Loom checklist"]
    
    # New GitHub-related fields
    repo_url: Optional[str]
    head_commit_id: Optional[str]
    changed_files: Annotated[List[str], "Files changed in the commit/PR"]
    github_event_type: Optional[str]
    github_payload: Optional[Dict[str, Any]] # Store full payload for detailed analysis if needed
    git_context: Optional[Dict[str, Any]] # Add git_context to GraphState

# --- 2. MCP API Client ---
def create_mcp_task(description: str, context: Dict[str, Any] = None) -> dict:
    """Creates a new task in the MCP server."""
    if context is None:
        context = {}
    response = requests.post(f"{MCP_SERVER_URL}/tasks/", params={"task_description": description}, json={"context": context})
    response.raise_for_status()
    return response.json()

def update_mcp_task_status(task_id: int, status: str) -> dict:
    """Updates the status of an existing task in the MCP server."""
    response = requests.put(f"{MCP_SERVER_URL}/tasks/{task_id}", params={"status": status})
    response.raise_for_status()
    return response.json()

def write_file(file_path: str, content: str) -> str:
    """Writes content to a file."""
    response = requests.post(f"{MCP_SERVER_URL}/tools/generate_code/write_file", json={"file_path": file_path, "content": content})
    response.raise_for_status()
    return response.json()

def add_neo4j_node(label: str, properties: dict) -> dict:
    """Adds a node to the Neo4j graph."""
    response = requests.post(f"{MCP_SERVER_URL}/tools/neo4j_memory/add_node", json={"label": label, "properties": properties})
    response.raise_for_status()
    return response.json()

def add_neo4j_relationship(start_node_label: str, start_node_properties: dict,
                             end_node_label: str, end_node_properties: dict,
                             relationship_type: str) -> dict:
    """Adds a relationship between two nodes in the Neo4j graph."""
    response = requests.post(f"{MCP_SERVER_URL}/tools/neo4j_memory/add_relationship", json={
        "start_node_label": start_node_label,
        "start_node_properties": start_node_properties,
        "end_node_label": end_node_label,
        "end_node_properties": end_node_properties,
        "relationship_type": relationship_type
    })
    response.raise_for_status()
    return response.json()

def generate_loom_checklist(task_description: str, code_changes: list[str]) -> str:
    """Generates a Loom checklist."""
    response = requests.post(f"{MCP_SERVER_URL}/tools/loom_helper/generate_demo_checklist", json={"task_description": task_description, "code_changes": code_changes})
    response.raise_for_status()
    return response.json()

# --- Utility to extract task from GitHub context ---
def extract_task_from_git_context(git_context: Dict[str, Any]) -> str:
    event_type = git_context.get("event_type")
    payload = git_context.get("payload", {})
    repo_name = git_context.get("repo_name", "unknown/unknown")

    if event_type == "push":
        head_commit = payload.get("head_commit", {})
        message = head_commit.get("message", f"New push to {repo_name}")
        return f"Analyze recent push to {repo_name}: {message}"
    elif event_type == "pull_request":
        pr = payload.get("pull_request", {})
        action = payload.get("action", "activity")
        title = pr.get("title", f"Pull request activity in {repo_name}")
        return f"Process pull request '{title}' ({action}) in {repo_name}"
    elif event_type == "issues" and payload.get("action") == "opened":
        issue = payload.get("issue", {})
        title = issue.get("title", "New issue")
        body = issue.get("body", "")
        return f"Task from new issue '{title}': {body}"
    else:
        return f"Handle GitHub event '{event_type}' for {repo_name}"

def get_changed_files_from_git_context(git_context: Dict[str, Any]) -> List[str]:
    event_type = git_context.get("event_type")
    payload = git_context.get("payload", {})
    
    changed_files = []
    if event_type == "push":
        head_commit = payload.get("head_commit", {})
        changed_files.extend(head_commit.get("added", []))
        changed_files.extend(head_commit.get("modified", []))
        changed_files.extend(head_commit.get("removed", []))
    elif event_type == "pull_request":
        # For PRs, getting changed files usually requires an extra API call.
        # For simplicity, we'll just indicate a PR event triggered changes.
        # In a real scenario, you'd use PyGithub to fetch PR files.
        changed_files.append(f"Pull Request #{payload.get('number')} changed files")
    return list(set(changed_files)) # Remove duplicates

# --- 3. Define Graph Nodes ---

def create_task_node(state: GraphState) -> GraphState:

    """Node to create a task in the MCP based on initial state or GitHub context."""

    print(f"--- Node: create_task_node ---")

    print(f"Input: task_description='{state['task_description']}', git_context_present={bool(state.get('git_context'))}")

    

    task_description = state["task_description"]

    git_context = state.get("git_context")



    if git_context:

        task_description = extract_task_from_git_context(git_context)

        # Pass GitHub context to MCP task for later retrieval

        task = create_mcp_task(task_description, context=git_context)

        

        # Populate state with GitHub details

        repo_url = git_context.get("repo_url")

        head_commit_id = None

        changed_files = get_changed_files_from_git_context(git_context)



        if git_context["event_type"] == "push":

            head_commit_id = git_context.get("payload", {}).get("head_commit", {}).get("id")

        elif git_context["event_type"] == "pull_request":

            head_commit_id = git_context.get("payload", {}).get("pull_request", {}).get("head", {}).get("sha")



        state.update({

            "task_id": task["id"],

            "status_message": f"Task created from GitHub event: {task_description}",

            "repo_url": repo_url,

            "head_commit_id": head_commit_id,

            "changed_files": changed_files,

            "github_event_type": git_context["event_type"],

            "github_payload": git_context["payload"]

        })

        print(f"Output: Task ID: {task['id']}, Status: {state['status_message']}, Repo: {repo_url}")

    else:

        task = create_mcp_task(task_description)

        state.update({

            "task_id": task["id"],

            "status_message": f"Task created: {task_description}"

        })

        print(f"Output: Task ID: {task['id']}, Status: {state['status_message']}")

    

    return state



class RouteQuery(BaseModel):

    """Route a user query to the most relevant agent."""

    datasource: str = Field(

        description="Given a user query choose which agent to route it to.",

        enum=["coding", "docs", "general"],

    )



def planner_node(state: GraphState) -> GraphState:

    """Node to decide which agent to use."""

    print("--- Node: planner_node ---")

    print(f"Input: task_description='{state['task_description']}', github_event_type='{state.get('github_event_type')}'")

    

    # This is a placeholder for a real model.

    # You can replace this with a call to a real classification model.

    prompt = ChatPromptTemplate.from_messages(

        [

            ("system", "You are an expert at routing a user query to a specialist agent."),

            ("human", "Given the user query below, classify it as either `coding`, `docs`, or `general`."),

            ("human", "Query: {query}"),

        ]

    )

    

    # This is a simulated model for routing.

    # In a real scenario, you would use a proper classification model.

    description = state["task_description"].lower()

    

    # Enhanced routing based on GitHub event type or task description

    event_type = state.get("github_event_type")

    if event_type == "pull_request" or event_type == "issues":

        route = "coding" # PRs and Issues are routed to the coding agent

        print(f"Routing: Coding Agent (due to {event_type} event)")

    elif "code" in description or "implement" in description or "fix" in description:

        route = "coding"

        print(f"Routing: Coding Agent")

    elif "docs" in description or "documentation" in description or event_type == "push":

        # Pushes often mean documentation updates or general code commits that need docs

        # More sophisticated logic would inspect commit messages/diffs

        route = "docs" if "docs" in description or "documentation" in description else "coding"

        print(f"Routing: {'Docs Agent' if route == 'docs' else 'Coding Agent'} (based on description/push event)")

    else:

        route = "general"

        print(f"Routing: General Task")



    print(f"Output: agent_outcome='{route}'")

    return {**state, "agent_outcome": route}


def coding_agent_node(state: GraphState) -> GraphState:
    """Node for the coding agent."""
    print("--- Node: coding_agent_node ---")
    print(f"Input: task_description='{state['task_description']}', repo_url='{state.get('repo_url')}'")

    # === REAL AGENT IMPLEMENTATION ===

    # 1. Get repository URL from state
    repo_url = state.get("repo_url")
    if not repo_url:
        # IMPORTANT: Replace this placeholder with the actual HTTPS URL of your new project's repository
        repo_url = "https://github.com/ishant721/MCP-Testing-..git" 
        print(f"Warning: repo_url not found in state. Using placeholder: {repo_url}")
        # In a real scenario, you might want to raise an error if the URL is missing.
        # For this educational step, we'll proceed with a placeholder.

    # 2. Create a temporary workspace
    # We use the task_id to create a unique directory for this task.
    workspace_dir = os.path.join("/tmp/mcp_workspace", str(state["task_id"]))
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
    os.makedirs(workspace_dir)
    print(f"Created temporary workspace: {workspace_dir}")

    try:
        # 3. Clone the repository
        print(f"Cloning repository: {repo_url}")
        subprocess.run(["git", "clone", repo_url, workspace_dir], check=True, capture_output=True, text=True)

        # 4. Define the task for the Gemini Coder
        # The task is derived from the state's task_description.
        coding_task = state["task_description"]
        
        # 5. Instantiate and run the Gemini Coder Agent
        print("Initializing Gemini Coder Agent...")
        coder_agent = GeminiCodingAgent() # Assumes Gemini API key is configured in the environment
        # For now, we'll assume the agent generates code for a single file `fibonacci.py`
        # A more advanced agent would return the file name as well.
        file_path = os.path.join(workspace_dir, "fibonacci.py")
        print(f"Generating code for task: '{coding_task}' in file '{file_path}'")
        generated_code = coder_agent.generate_code(coding_task, file_path=file_path)
        print("Code generation complete.")

        # 6. Write the generated code to a file
        print(f"Writing generated code to: {file_path}")
        with open(file_path, "w") as f:
            f.write(generated_code)

        # 7. Commit and push the changes
        print("Committing and pushing changes to the repository...")
        git_commands = [
            ["git", "add", "fibonacci.py"],
            ["git", "commit", "-m", "MCP: Implement Fibonacci script"],
            ["git", "push"]
        ]
        for cmd in git_commands:
            result = subprocess.run(cmd, cwd=workspace_dir, check=True, capture_output=True, text=True)
            print(f"Ran command: '{' '.join(cmd)}'. Output:\n{result.stdout}\n{result.stderr}")
        
        print("Changes pushed successfully.")
        
        # Update state with the outcome
        new_state = {
            **state,
            "code_changes": [f"Created fibonacci.py with the requested implementations."],
            "status_message": "Autonomous code generation and push successful."
        }

    except subprocess.CalledProcessError as e:
        print(f"Error during Git operation: {e.stderr}")
        new_state = {
            **state,
            "status_message": f"Error during Git operation: {e.stderr}"
        }
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        new_state = {
            **state,
            "status_message": f"An unexpected error occurred: {e}"
        }
    finally:
        # 8. Clean up the workspace
        print(f"Cleaning up workspace: {workspace_dir}")
        shutil.rmtree(workspace_dir)

    print(f"Output: status_message='{new_state['status_message']}'")
    return new_state


def docs_agent_node(state: GraphState) -> GraphState:

    """Node for the docs agent."""

    print("--- Node: docs_agent_node ---")

    print(f"Input: task_description='{state['task_description']}', repo_url='{state.get('repo_url')}'")



    # In a real scenario, this would involve a call to the Docs Agent

    # For now, we'll just simulate generating a README

    readme_content = f"This is a sample README generated by the docs agent via API call based on GitHub event. Task: {state['task_description']}.";

    # write_file("README.md", readme_content) # Simulate documentation generation, commented out to avoid polluting repo

    

    new_state = {

        **state,

        "documentation": readme_content,

        "status_message": "Documentation generated by docs agent"

    }

    print(f"Output: status_message='{new_state['status_message']}', documentation_length={len(new_state['documentation'])}")

    return new_state


def store_context_node(state: GraphState) -> GraphState:

    """Node to store the context of the task in Neo4j."""

    print("--- Node: store_context_node ---")

    print(f"Input: task_id={state['task_id']}, task_description='{state['task_description']}', agent_outcome='{state['agent_outcome']}'")



    task_id = state["task_id"]

    task_description = state["task_description"]

    

    # Add a node for the task

    add_neo4j_node("Task", {"id": task_id, "description": task_description, "status": state["status_message"]})

    print(f"Logged Task {task_id} to Neo4j.")



    # Store GitHub context if present

    if state.get("github_payload"):

        repo_name = state["github_payload"].get("repository", {}).get("full_name")

        # Extract owner/repo from full_name

        repo_parts = repo_name.split('/')

        repo_owner = repo_parts[0] if len(repo_parts) > 1 else repo_name

        repo_short_name = repo_parts[1] if len(repo_parts) > 1 else repo_name

        

        # Add Repo Node

        add_neo4j_node("Repository", {"name": repo_name, "url": state["repo_url"], "owner": repo_owner, "short_name": repo_short_name})

        add_neo4j_relationship(

            "Task", {"id": task_id},

            "Repository", {"url": state["repo_url"]},

            "RELATED_TO_REPO"

        )

        print(f"Logged Repository {repo_name} to Neo4j.")



        if state.get("head_commit_id"):

            commit_id_short = state["head_commit_id"][:7]

            add_neo4j_node("Commit", {"sha": state["head_commit_id"], "repo_url": state["repo_url"], "event_type": state["github_event_type"]})

            add_neo4j_relationship(

                "Task", {"id": task_id},

                "Commit", {"sha": state["head_commit_id"]},

                "TRIGGERED_BY_COMMIT"

            )

            print(f"Logged Commit {commit_id_short} to Neo4j.")

        

        for changed_file_path in state["changed_files"]:

            add_neo4j_node("File", {"path": changed_file_path, "repo_url": state["repo_url"]})

            add_neo4j_relationship(

                "Task", {"id": task_id},

                "File", {"path": changed_file_path},

                "AFFECTS_FILE"

            )

        print(f"Logged {len(state['changed_files'])} changed files to Neo4j.")



    if state["agent_outcome"] == "coding" and state["code_changes"]:

        for change_summary in state["code_changes"]:

            # Example of logging generated/modified files by agent

            add_neo4j_node("GeneratedFile", {"path": change_summary, "task_id": task_id}) # Use a unique ID for the file

            add_neo4j_relationship(

                "Task", {"id": task_id},

                "GeneratedFile", {"path": change_summary},

                "GENERATED_CODE"

            )

        print(f"Logged coding agent changes to Neo4j.")

            

    elif state["agent_outcome"] == "docs" and state["documentation"]:

        # Add a node for the documentation

        add_neo4j_node("DocumentationOutput", {"content_preview": state["documentation"][:100], "task_id": task_id})

        add_neo4j_relationship(

            "Task", {"id": task_id},

            "DocumentationOutput", {"content_preview": state["documentation"][:100]},

            "GENERATED_DOCS"

        )

        print(f"Logged documentation output to Neo4j.")

        

    new_state = {**state, "status_message": "Context stored in Neo4j"}

    print(f"Output: status_message='{new_state['status_message']}'")

    return new_state


def loom_checklist_node(state: GraphState) -> GraphState:

    """Node to generate a Loom checklist."""

    print("--- Node: loom_checklist_node ---")

    print(f"Input: task_description='{state['task_description']}', code_changes={state['code_changes']}")

    checklist = generate_loom_checklist(state["task_description"], state["code_changes"])

    new_state = {**state, "loom_checklist": checklist, "status_message": "Loom checklist generated"}

    print(f"Output: status_message='{new_state['status_message']}', loom_checklist_length={len(new_state['loom_checklist'])}")

    return new_state


def status_update_node(state: GraphState) -> GraphState:

    """Node to update the task status in the MCP."""

    print("--- Node: status_update_node ---")

    print(f"Input: task_id={state['task_id']}, current_status='{state['status_message']}'")

    update_mcp_task_status(state["task_id"], "completed")

    new_state = {**state, "status_message": "Task status updated to completed in MCP"}

    print(f"Output: status_message='{new_state['status_message']}'")

    return new_state




# --- 4. Build the Graph ---

workflow = StateGraph(GraphState)



workflow.add_node("create_task", create_task_node)

workflow.add_node("planner", planner_node)

workflow.add_node("coding_agent", coding_agent_node)

workflow.add_node("docs_agent", docs_agent_node)

workflow.add_node("store_context", store_context_node)

workflow.add_node("loom_checklist", loom_checklist_node)

workflow.add_node("status_update", status_update_node)



workflow.set_entry_point("create_task")

workflow.add_edge("create_task", "planner")



workflow.add_conditional_edges(

    "planner",

    lambda x: x["agent_outcome"],

    {

        "coding": "coding_agent",

        "docs": "docs_agent",

        "general": END,

    },

)



workflow.add_edge("coding_agent", "store_context")

workflow.add_edge("docs_agent", "store_context")

workflow.add_edge("store_context", "loom_checklist")

workflow.add_edge("loom_checklist", "status_update")

workflow.add_edge("status_update", END)



app = workflow.compile()
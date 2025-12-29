from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from mcp_server.models import (
    Task,
    FileContent,
    FileUpdate,
    DirectoryPath,
    ReadmeRequest,
    ArchDocsRequest,
    Neo4jNode,
    Neo4jRelationship,
    Neo4jQuery,
    LoomChecklistRequest,
)
from mcp_server.tools.task_tracker import TaskTrackerTool
from mcp_server.tools.generate_code import CodeGenerationTool
from mcp_server.tools.read_repo import RepoReadTool
from mcp_server.tools.write_docs import DocsWriteTool
from mcp_server.tools.neo4j_memory import Neo4jMemoryTool
from mcp_server.tools.loom_helper import LoomHelperTool
from orchestrator.graph import app as orchestrator_app_graph

# --- In-Memory Database ---
tasks_db: List[Task] = []
task_id_counter = 1

# --- FastAPI Application ---
app = FastAPI(
    title="MCP Server (Mission Control Platform)",
    description="Acts as the central tool registry, context manager, and execution engine for the automated AI workspace.",
    version="0.1.0",
)

# --- Initialize Tools ---
task_tracker = TaskTrackerTool(tasks_db, task_id_counter)
code_generation = CodeGenerationTool()
repo_read = RepoReadTool()
docs_write = DocsWriteTool()
neo4j_memory = Neo4jMemoryTool()
loom_helper = LoomHelperTool()

# --- API Endpoints ---
@app.get("/")
def read_root():
    """A simple endpoint to confirm the server is running."""
    return {"message": "MCP Server is running"}

class OrchestratorRequest(BaseModel):
    task_description: str

@app.post("/trigger-orchestrator")
async def trigger_orchestrator(request: OrchestratorRequest):
    import threading
    initial_state = {
        "task_description": request.task_description,
        "task_id": 0, # Task ID will be set by create_task_node
        "status_message": "Orchestrator initiated...",
        "agent_outcome": "",
        "file_path": "",
        "code_changes": [],
        "documentation": "",
        "loom_checklist": "",
        "git_context": None
    }
    threading.Thread(target=orchestrator_app_graph.invoke, args=(initial_state,)).start()

    return {"message": "Orchestrator triggered", "status": "processing", "task_description": request.task_description}

# --- Task Management Endpoints ---
@app.post("/tasks/", response_model=Task, status_code=201)
def create_task_api(task_description: str):
    return task_tracker.create_task(task_description)

@app.get("/tasks/", response_model=List[Task])
def get_tasks_api():
    return task_tracker.list_tasks()

@app.get("/tasks/{task_id}", response_model=Task)
def get_task_api(task_id: int):
    try:
        return task_tracker.get_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/tasks/{task_id}", response_model=Task)
def update_task_status_api(task_id: int, status: str):
    try:
        return task_tracker.update_task_status(task_id, status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- Code Generation Endpoints ---
@app.post("/tools/generate_code/write_file", status_code=201)
def write_file_api(file_content: FileContent):
    return code_generation.write_file(file_content.file_path, file_content.content)

@app.put("/tools/generate_code/update_file")
def update_file_api(file_update: FileUpdate):
    return code_generation.update_file(file_update.file_path, file_update.new_content, file_update.old_content)

# --- Repo Read Endpoints ---
@app.get("/tools/read_repo/list_files", response_model=List[str])
def list_files_api(directory_path: DirectoryPath):
    return repo_read.list_files(directory_path.directory)

@app.get("/tools/read_repo/read_file", response_model=str)
def read_file_api(file_path: str):
    return repo_read.read_file(file_path)

# --- Docs Write Endpoints ---
@app.post("/tools/write_docs/generate_readme", status_code=201)
def generate_readme_api(request: ReadmeRequest):
    return docs_write.generate_readme(request.project_name, request.description, request.file_path)

@app.post("/tools/write_docs/generate_architecture_docs", status_code=201)
def generate_architecture_docs_api(request: ArchDocsRequest):
    return docs_write.generate_architecture_docs(request.architecture_overview, request.file_path)

# --- Neo4j Memory Endpoints ---
@app.post("/tools/neo4j_memory/add_node", status_code=201)
def add_node_api(node: Neo4jNode):
    return neo4j_memory.add_node(node.label, node.properties)

@app.post("/tools/neo4j_memory/add_relationship", status_code=201)
def add_relationship_api(relationship: Neo4jRelationship):
    return neo4j_memory.add_relationship(
        relationship.start_node_label,
        relationship.start_node_properties,
        relationship.end_node_label,
        relationship.end_node_properties,
        relationship.relationship_type,
    )

@app.post("/tools/neo4j_memory/query")
def query_neo4j_api(query: Neo4jQuery):
    return neo4j_memory.query(query.query)

# --- Loom Helper Endpoints ---
@app.post("/tools/loom_helper/generate_demo_checklist")
def generate_demo_checklist_api(request: LoomChecklistRequest):
    return loom_helper.generate_demo_checklist(request.task_description, request.code_changes)
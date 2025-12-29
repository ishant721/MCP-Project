from pydantic import BaseModel
from typing import List, Dict, Any

class Task(BaseModel):
    id: int
    description: str
    status: str = "pending"
    context: Dict[str, Any] = {}

class FileContent(BaseModel):
    file_path: str
    content: str

class FileUpdate(BaseModel):
    file_path: str
    new_content: str
    old_content: str = None

class DirectoryPath(BaseModel):
    directory: str

class ReadmeRequest(BaseModel):
    project_name: str
    description: str
    file_path: str = "README.md"

class ArchDocsRequest(BaseModel):
    architecture_overview: str
    file_path: str = "docs/architecture.md"

class Neo4jNode(BaseModel):
    label: str
    properties: dict

class Neo4jRelationship(BaseModel):
    start_node_label: str
    start_node_properties: dict
    end_node_label: str
    end_node_properties: dict
    relationship_type: str

class Neo4jQuery(BaseModel):
    query: str

class LoomChecklistRequest(BaseModel):
    task_description: str
    code_changes: List[str]

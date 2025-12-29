from typing import List, Dict, Any
from mcp_server.models import Task

class TaskTrackerTool:
    """
    A simple tool to interact with the MCP's task management system.
    """

    def __init__(self, tasks_db: List[Task], task_id_counter: int):
        self.tasks_db = tasks_db
        self.task_id_counter = task_id_counter

    def create_task(self, description: str, context: Dict[str, Any] = None) -> Task:
        """
        Creates a new task in the MCP.
        """
        new_task = Task(id=self.task_id_counter, description=description, context=context if context else {})
        self.tasks_db.append(new_task)
        self.task_id_counter += 1
        return new_task

    def get_task(self, task_id: int) -> Task:
        """
        Retrieves a task by its ID.
        """
        task = next((t for t in self.tasks_db if t.id == task_id), None)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found.")
        return task

    def update_task_status(self, task_id: int, status: str) -> Task:
        """
        Updates the status of an existing task.
        """
        task = self.get_task(task_id)
        task.status = status
        return task

    def list_tasks(self) -> List[Task]:
        """
        Lists all available tasks.
        """
        return self.tasks_db

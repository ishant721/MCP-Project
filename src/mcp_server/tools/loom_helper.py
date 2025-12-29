class LoomHelperTool:
    """
    A tool to generate a checklist for creating a Loom video demo.
    """

    def generate_demo_checklist(self, task_description: str, code_changes: list[str]) -> str:
        """
        Generates a checklist for a Loom video demo based on the task and code changes.
        """
        checklist = f"## Loom Demo Checklist: {task_description}\n\n"
        checklist += "### 1. Introduction\n"
        checklist += "- [ ] Briefly explain the task and its goal.\n"
        checklist += "- [ ] Mention the key changes that were made.\n\n"
        checklist += "### 2. Code Walkthrough\n"
        for change in code_changes:
            checklist += f"- [ ] Explain the changes in `{change}`.\n"
        checklist += "\n"
        checklist += "### 3. Demonstration\n"
        checklist += "- [ ] Show the new feature or bug fix in action.\n"
        checklist += "- [ ] If applicable, show the updated documentation.\n\n"
        checklist += "### 4. Conclusion\n"
        checklist += "- [ ] Summarize the work that was done.\n"
        checklist += "- [ ] Mention any next steps.\n"

        return checklist

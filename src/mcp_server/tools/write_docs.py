from mcp_server.tools.generate_code import CodeGenerationTool

class DocsWriteTool:
    """
    A tool for generating READMEs and architecture documents.
    """

    def __init__(self):
        self.code_gen_tool = CodeGenerationTool()

    def generate_readme(self, project_name: str, description: str, file_path: str = "README.md") -> str:
        """
        Generates a basic README.md file.
        """
        content = f"# {project_name}\n\n{description}\n"
        return self.code_gen_tool.write_file(file_path, content)

    def generate_architecture_docs(self, architecture_overview: str, file_path: str = "docs/architecture.md") -> str:
        """
        Generates an architecture documentation file.
        """
        return self.code_gen_tool.write_file(file_path, architecture_overview)

import os

class CodeGenerationTool:
    """
    A tool to write or update files in the workspace.
    """

    def write_file(self, file_path: str, content: str) -> str:
        """
        Writes content to a file. If the file exists, it will be overwritten.
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing to file: {e}"

    def update_file(self, file_path: str, new_content: str, old_content: str = None) -> str:
        """
        Updates a file with new content. If old_content is provided, it will be replaced.
        If not, the new content will be appended to the file.
        """
        if old_content:
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                content = content.replace(old_content, new_content)
                with open(file_path, "w") as f:
                    f.write(content)
                return f"Successfully updated {file_path}"
            except FileNotFoundError:
                return f"Error: {file_path} not found."
            except Exception as e:
                return f"Error updating file: {e}"
        else:
            try:
                with open(file_path, "a") as f:
                    f.write(new_content)
                return f"Successfully appended to {file_path}"
            except Exception as e:
                return f"Error appending to file: {e}"

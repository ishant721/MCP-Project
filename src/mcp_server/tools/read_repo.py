import os

class RepoReadTool:
    """
    A tool to analyze existing code in the repository.
    """

    def list_files(self, directory: str) -> list[str]:
        """
        Lists all files in a given directory, recursively.
        """
        all_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                all_files.append(os.path.join(root, file))
        return all_files

    def read_file(self, file_path: str) -> str:
        """
        Reads the content of a file.
        """
        try:
            with open(file_path, "r") as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return f"Error: {file_path} not found."
        except Exception as e:
            return f"Error reading file: {e}"

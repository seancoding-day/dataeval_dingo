import tempfile
from pathlib import Path

from dingo.config import InputArgs
from dingo.exec import Executor


def run_md_single_file_demo():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        md_file = tmp_path / "single.md"
        md_file.write_text("# Single File Demo\n\nThis is markdown content.:", encoding="utf-8")

        input_data = {
            "input_path": str(md_file),
            "dataset": {
                "source": "local",
                "format": "md",
            },
            "evaluator": [
                {
                    "fields": {"id": "id", "content": "content"},
                    "evals": [
                        {"name": "RuleColonEnd"},
                    ],
                }
            ],
        }

        input_args = InputArgs(**input_data)
        executor = Executor.exec_map["local"](input_args)
        result = executor.execute()
        print("single file demo:")
        print(result)


def run_md_directory_demo():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "a.md").write_text("## A\n\nalpha content:", encoding="utf-8")
        (tmp_path / "b.md").write_text("## B\n\nbeta content:", encoding="utf-8")
        (tmp_path / "ignore.txt").write_text("this file will be ignored in md format", encoding="utf-8")

        input_data = {
            "input_path": str(tmp_path),
            "dataset": {
                "source": "local",
                "format": "md",
            },
            "evaluator": [
                {
                    "fields": {"id": "id", "content": "content"},
                    "evals": [
                        {"name": "RuleColonEnd"},
                    ],
                }
            ],
        }

        input_args = InputArgs(**input_data)
        executor = Executor.exec_map["local"](input_args)
        result = executor.execute()
        print("directory demo:")
        print(result)


if __name__ == "__main__":
    run_md_single_file_demo()
    run_md_directory_demo()

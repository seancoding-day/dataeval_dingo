from dingo.config import InputArgs
from dingo.exec import Executor


def huggingface_plaintext():
    input_data = {
        "input_path": "chupei/format-text",
        "dataset": {
            "format": "plaintext",
            "field": {
                "content": "text"
            }
        },
        "executor": {
            "eval_group": "sft"
        }
    }

    input_args = InputArgs(**input_data)
    executor = Executor.exec_map["local"](input_args)
    result = executor.execute()
    print(result)


def huggingface_json():
    input_data = {
        "input_path": "chupei/format-json",
        "dataset": {
            "format": "json",
            "field": {
                "prompt": "origin_prompt",
                "content": "prediction"
            }
        },
        "executor": {
            "eval_group": "sft",
        }
    }

    input_args = InputArgs(**input_data)
    executor = Executor.exec_map["local"](input_args)
    result = executor.execute()
    print(result)


def huggingface_jsonl():
    input_data = {
        "input_path": "chupei/format-jsonl",
        "dataset": {
            "format": "jsonl",
            "field": {
                "content": "content"
            }
        },
        "executor": {
            "eval_group": "sft",
        }
    }

    input_args = InputArgs(**input_data)
    executor = Executor.exec_map["local"](input_args)
    result = executor.execute()
    print(result)


def huggingface_listjson():
    input_data = {
        "input_path": "chupei/format-listjson",
        "dataset": {
            "format": "listjson",
            "field": {
                "prompt": "instruction",
                "content": "output"
            }
        },
        "executor": {
            "eval_group": "sft",
        }
    }

    input_args = InputArgs(**input_data)
    executor = Executor.exec_map["local"](input_args)
    result = executor.execute()
    print(result)


if __name__ == '__main__':
    huggingface_plaintext()
    huggingface_json()
    huggingface_jsonl()
    huggingface_listjson()

from dingo.config import InputArgs
from dingo.exec import Executor


def local_plaintext():
    input_data = {
        "input_path": "../../test/data/test_local_plaintext.txt",
        "dataset": {
            "source": "local",
            "format": "plaintext",
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


def local_json():
    input_data = {
        "input_path": "../../test/data/test_local_json.json",
        "dataset": {
            "source": "local",
            "format": "json",
            "field": {
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


def local_jsonl():
    input_data = {
        "input_path": "../../test/data/test_local_jsonl.jsonl",
        "dataset": {
            "source": "local",
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


def local_listjson():
    input_data = {
        "input_path": "../../test/data/test_local_listjson.json",
        "dataset": {
            "source": "local",
            "format": "listjson",
            "field": {
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
    local_plaintext()
    local_json()
    local_jsonl()
    local_listjson()

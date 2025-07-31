from dingo.config import InputArgs
from dingo.exec import Executor


def image_repeat():
    input_data = {
        "input_path": "../../test/data/test_img_repeat.jsonl",
        "dataset": {
            "source": "local",
            "format": "jsonl",
            "field": {
                "content": "content"
            }
        },
        "executor": {
            "rule_list": ["RuleImageRepeat"],
            "result_save": {
                "bad": True,
                "good": True
            }
        }
    }
    input_args = InputArgs(**input_data)
    executor = Executor.exec_map["local"](input_args)
    result = executor.execute()
    print(result)


if __name__ == '__main__':
    image_repeat()

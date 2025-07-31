from dingo.config import InputArgs
from dingo.exec import Executor


def classify_3H():
    input_data = {
        "input_path": "../../test/data/test_3h_jsonl.jsonl",
        "dataset": {
            "source": "local",
            "format": "jsonl",
            "field": {
                "prompt": "input",
                "content": "response"
            }
        },
        "executor": {
            "prompt_list": ["PromptTextHarmless"],  # options:['PromptIsHelpful', 'PromptIsHonest']
            "result_save": {
                "bad": True,
                "good": True
            }
        },
        "evaluator": {
            "llm_config": {
                "LLMText3HHarmless": {
                    "key": "",
                    "api_url": ""
                }
            }
        }
    }
    input_args = InputArgs(**input_data)
    executor = Executor.exec_map["local"](input_args)
    result = executor.execute()
    print(result)


if __name__ == '__main__':
    classify_3H()

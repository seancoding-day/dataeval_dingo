from dingo.exec import Executor
from dingo.io import InputArgs

input_data = {
    "input_path": "../../test/data/test_local_jsonl.jsonl",
    "log_level": "INFO",

    "database": {
        "source": "local",
        "format": "jsonl",
        "field": {
            "content": "content"
        }
    },
    "executor": {
        "rule_list": ["RuleColonEnd"],
        "prompt_list": ["PromptRepeat"],
        "result_save": {
            "bad": True,
            "all": True
        }
    },
    "evaluator": {
        "llm_config": {
            "LLMTextQualityPromptBase": {
                "key": "enter your key, such as:EMPTY",
                "api_url": "enter your local llm api url, such as:http://127.0.0.1:8080/v1",
            }
        }
    }
}
input_args = InputArgs(**input_data)
executor = Executor.exec_map["local"](input_args)
result = executor.execute()
print(result)

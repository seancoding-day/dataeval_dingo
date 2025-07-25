from dingo.config import InputArgs
from dingo.exec import Executor

input_data = {
    "input_path": "../../test/data/test_local_jsonl.jsonl",
    "log_level": "INFO",

    "dataset": {
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
            "good": True
        }
    },
    "evaluator": {
        "llm_config": {
            "LLMTextQualityPromptBase": {
                "key": "EMPTY",
                "api_url": "http://10.140.54.48:29990/v1",
            }
        }
    }
}
input_args = InputArgs(**input_data)
executor = Executor.exec_map["local"](input_args)
result = executor.execute()
print(result)

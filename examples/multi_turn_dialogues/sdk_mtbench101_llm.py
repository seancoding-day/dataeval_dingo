from dingo.config import InputArgs
from dingo.exec import Executor

input_data = {
    "input_path": "../../test/data/test_mtbench101_jsonl.jsonl",
    "dataset": {
        "source": "local",
        "format": "multi_turn_dialog",
        "field": {
            "id": "id",
            "content": "history"  # the column name of multi-turn dialogues, e.g.: history, dialogues
        }
    },
    "executor": {
        "prompt_list": ["PromptTextQualityV3"],
        "result_save": {
            "bad": True,
            "good": True
        },
        "multi_turn_mode": "all"
    },
    "evaluator": {
        "llm_config": {
            "detect_text_quality_detail": {
                "key": "",
                "api_url": "",
            }
        }
    }
}
input_args = InputArgs(**input_data)
executor = Executor.exec_map["local"](input_args)
result = executor.execute()
print(result)

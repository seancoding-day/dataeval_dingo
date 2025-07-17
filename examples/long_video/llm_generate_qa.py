from dingo.exec import Executor
from dingo.io import InputArgs

input_data = {
    "input_path": "../../test/data/test_long_video_qa.jsonl",
    "save_data": True,
    "save_correct": True,
    "dataset": "local",
    "data_format": "jsonl",
    "column_id": "video_id",
    "column_content": "summary",
    "custom_config": {
        "prompt_list": ["PromptLongVideoQa"],
        "llm_config": {
            "LLMLongVideoQa": {
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

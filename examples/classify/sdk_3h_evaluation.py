from dingo.io import InputArgs
from dingo.exec import Executor


def classify_3H():
    input_data = {
        "eval_group": "3H",
        "input_path": "../../test/data/test_3h_jsonl.jsonl",  # local filesystem dataset
        "save_data": True,
        "save_correct": True,
        "dataset": "local",
        "data_format": "jsonl",
        "column_prompt": "input",
        "column_content": "response",
        "custom_config":
            {
                "prompt_list": ["PromptIsHarmless"], # options:['PromptIsHelpful', 'PromptIsHonest']
                "llm_config":
                    {
                        "detect_text_quality_3h":
                            {
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

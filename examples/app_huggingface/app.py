import json

import gradio as gr
from dingo.exec import Executor
from dingo.io import InputArgs


def dingo_demo(input_path, data_format, column_content, input_rules, input_prompts, key, api_url):
    if not input_path:
        return 'ValueError: input_path can not be empty, please input.'
    if not data_format:
        return 'ValueError: data_format can not be empty, please input.'
    if not column_content:
        return 'ValueError: column_content can not be empty, please input.'
    if not input_rules and not input_prompts:
        return 'ValueError: input_rules and input_prompts can not be empty at the same time.'

    input_data = {
        "input_path": input_path,
        "data_format": data_format,
        "column_content": column_content,
        "custom_config":
            {
                "rule_list": input_rules,
                "prompt_list": input_prompts,
                "llm_config":
                    {
                        "detect_text_quality_detail":
                            {
                                "key": key,
                                "api_url": api_url,
                            }
                    }
            }
    }
    input_args = InputArgs(**input_data)
    executor = Executor.exec_map["local"](input_args)
    result = executor.execute()
    summary = result[0].to_dict()
    return json.dumps(summary, indent=4)


if __name__ == '__main__':
    rule_options = ['RuleAbnormalChar', 'RuleAbnormalHtml', 'RuleContentNull', 'RuleContentShort', 'RuleEnterAndSpace', 'RuleOnlyUrl']
    prompt_options = ['PromptRepeat', 'PromptContentChaos']

    #接口创建函数
    #fn设置处理函数，inputs设置输入接口组件，outputs设置输出接口组件
    #fn,inputs,outputs都是必填函数
    demo = gr.Interface(
        fn=dingo_demo,
        inputs=[
            gr.Textbox(value='chupei/format-jsonl', placeholder="please input huggingface dataset path"),
            gr.Dropdown(["jsonl", "json", "plaintext", "listjson"], label="data_format"),
            gr.Textbox(value="content", placeholder="please input column name of content in dataset"),
            gr.CheckboxGroup(choices=rule_options, label="rule_list"),
            gr.CheckboxGroup(choices=prompt_options, label="prompt_list"),
            'text',
            'text',
        ],
        outputs="text")
    demo.launch()

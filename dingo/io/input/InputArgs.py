import json
import os
import time
import uuid
from typing import Dict, List, Optional

from pydantic import BaseModel, ValidationError

from dingo.config.config import DynamicLLMConfig, DynamicRuleConfig


class DatabaseFieldArgs(BaseModel):
    id: str = ''
    prompt: str = ''
    content: str = ''
    context: str = ''
    image: str = ''


class DatabaseArgs(BaseModel):
    source: str = 'hugging_face'
    format: str = 'json'
    field: DatabaseFieldArgs = DatabaseFieldArgs()


class ExecutorResultSaveArgs(BaseModel):
    bad: bool = False
    all: bool = False
    raw: bool = False


class ExecutorArgs(BaseModel):
    eval_group: str = ""
    rule_list: Optional[List[str]] = []
    prompt_list: Optional[List[str]] = []
    start_index: int = 0
    end_index: int = -1
    max_workers: int = 1
    batch_size: int = 1
    result_save: ExecutorResultSaveArgs = ExecutorResultSaveArgs()


class EvaluatorArgs(BaseModel):
    rule_config: Optional[Dict[str, DynamicRuleConfig]] = {}
    llm_config: Optional[Dict[str, DynamicLLMConfig]] = {}


class InputArgs(BaseModel):
    """
    Input arguments, input of project.
    """
    task_name: str = "dingo"
    input_path: str = "test/data/test_local_json.json"
    output_path: str = "outputs/"

    log_level: str = "WARNING"
    use_browser: bool = False

    database: DatabaseArgs = DatabaseArgs()
    executor: ExecutorArgs = ExecutorArgs()
    evaluator: EvaluatorArgs = EvaluatorArgs()

    ########################### old args ###########################
    eval_group: str = ""
    save_data: bool = False
    save_correct: bool = False
    save_raw: bool = False
    # Resume settings
    start_index: int = 0
    end_index: int = -1
    # Concurrent settings
    max_workers: int = 1
    batch_size: int = 1
    # Dataset setting
    dataset: str = "hugging_face"  # ['local', 'hugging_face']
    data_format: str = "json"
    column_id: str = ""
    column_prompt: str = ""
    column_content: str = ""
    column_context: str = ""
    column_image: str = ""
    custom_config: Optional[str | dict] = None
    ########################### old args ###########################

    ######################### dropped args #########################
    # Huggingface specific setting
    huggingface_split: str = ""
    huggingface_config_name: Optional[str] = None
    ######################### dropped args #########################

    def __init__(self, **kwargs):
        # Initialize custom_config if it doesn't exist
        if 'custom_config' not in kwargs:
            kwargs['custom_config'] = {}

        if 'database' in kwargs:
            db = kwargs['database']
            if 'source' in db:
                kwargs['dataset'] = db['source']
            if 'format' in db:
                kwargs['data_format'] = db['format']
            if 'field' in db:
                field = db['field']
                if 'id' in field:
                    kwargs['column_id'] = field['id']
                if 'prompt' in field:
                    kwargs['column_prompt'] = field['prompt']
                if 'content' in field:
                    kwargs['column_content'] = field['content']
                if 'context' in field:
                    kwargs['column_context'] = field['context']
                if 'image' in field:
                    kwargs['column_image'] = field['image']

        if 'executor' in kwargs:
            ex = kwargs['executor']
            if 'eval_group' in ex:
                kwargs['eval_group'] = ex['eval_group']
            if 'start_index' in ex:
                kwargs['start_index'] = ex['start_index']
            if 'end_index' in ex:
                kwargs['end_index'] = ex['end_index']
            if 'max_workers' in ex:
                kwargs['max_workers'] = ex['max_workers']
            if 'batch_size' in ex:
                kwargs['batch_size'] = ex['batch_size']
            if 'result_save' in ex:
                result_save = ex['result_save']
                if 'bad' in result_save:
                    kwargs['save_data'] = result_save['bad']
                if 'all' in result_save:
                    kwargs['save_correct'] = result_save['all']
                if 'raw' in result_save:
                    kwargs['save_raw'] = result_save['raw']

            if 'rule_list' in ex:
                kwargs['custom_config']['rule_list'] = ex['rule_list']
            if 'prompt_list' in ex:
                kwargs['custom_config']['prompt_list'] = ex['prompt_list']

        if 'evaluator' in kwargs:
            ev = kwargs['evaluator']
            if 'rule_config' in ev:
                kwargs['custom_config']['rule_config'] = ev['rule_config']
            if 'llm_config' in ev:
                kwargs['custom_config']['llm_config'] = ev['llm_config']

        super().__init__(**kwargs)

    def check_args(self):
        # check eval group
        if not self.eval_group:
            if not self.custom_config:
                raise ValueError("eval_group cannot be empty.")
            else:
                tmp_config = {}
                if isinstance(self.custom_config, str):
                    with open(self.custom_config, "r", encoding="utf-8") as f:
                        tmp_config = json.load(f)
                else:
                    tmp_config = self.custom_config
                if "rule_list" in tmp_config or "prompt_list" in tmp_config:
                    self.eval_group = (
                        "custom_group"
                        + "_"
                        + time.strftime("%H%M%S", time.localtime())
                        + "_"
                        + str(uuid.uuid1())[:8]
                    )
                else:
                    raise ValueError("eval_group cannot be empty.")

        # check input path
        if self.dataset != "hugging_face" and not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Input path '{self.input_path}' does not exist.")

        # check save_data/save_correct
        if not self.save_data and self.save_correct:
            raise ValueError(
                "save_correct is True but save_data is False. Please set save_data to True."
            )

        # check start index
        if self.start_index < 0:
            raise ValueError("start_index must be non negative.")

        if self.end_index >= 0 and self.end_index < self.start_index:
            raise ValueError(
                "if end_index is non negative, end_index must be greater than start_index"
            )

        # check max workers
        if self.max_workers <= 0:
            raise ValueError("max_workers must be a positive integer.")

        # check batch size
        if self.batch_size <= 0:
            raise ValueError("batch_size must be a positive integer.")

        # check dataset
        if self.dataset not in ["local", "hugging_face"]:
            raise ValueError("dataset must in ['local', 'hugging_face']")

        # check llm config
        if (
            self.custom_config
            and isinstance(self.custom_config, dict)
            and self.custom_config.get("prompt_list")
        ):
            if not self.custom_config.get("llm_config"):
                raise ValueError(
                    "llm_config in custom_config cannot be empty when using llm evaluation."
                )

        # check log_level
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError("log_level must in ['DEBUG', 'INFO', 'WARNING', 'ERROR']")

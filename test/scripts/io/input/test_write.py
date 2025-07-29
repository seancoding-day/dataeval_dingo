import os
import shutil

import pytest

from dingo.config import InputArgs
from dingo.exec import Executor


class TestWrite:
    def test_write_local_jsonl(self):
        input_args = InputArgs(**{
            "input_path": "test/data/test_local_jsonl.jsonl",
            "dataset": {
                "source": "local",
                "format": "jsonl",
                "field": {
                    "id": "id",
                    "content": "content"
                }
            },
            "executor": {
                "eval_group": "qa_standard_v1",
                "result_save": {
                    "bad": True,
                    "good": True
                }
            }
        })
        executor = Executor.exec_map["local"](input_args)
        result = executor.execute().to_dict()
        # print(result)
        output_path = result['output_path']
        assert os.path.exists(output_path)
        shutil.rmtree('outputs')

import argparse
import json
import os

import prettytable as pt

from dingo.config import InputArgs
from dingo.exec import Executor
from dingo.model import Model
from dingo.utils import log


def parse_args():
    parser = argparse.ArgumentParser("dingo run with local script. (CLI)")
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default=None,
        help="Please input config file path",
    )

    return parser.parse_args()


def get_config(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


if __name__ == "__main__":
    args = parse_args()
    input_data = get_config(args.input)
    # print(args.input)
    # print(input_data)
    input_args = InputArgs(**input_data)
    executor = Executor.exec_map["local"](input_args)
    result = executor.execute()
    print(result)

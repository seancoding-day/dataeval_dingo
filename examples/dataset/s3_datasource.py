"""
S3 数据源使用示例

此示例展示如何使用 S3 作为数据源进行评估。

使用前准备：
1. 确保已安装 boto3: pip install boto3
2. 设置 S3 配置环境变量：
   export S3_ACCESS_KEY="your_access_key"
   export S3_SECRET_KEY="your_secret_key"
   export S3_ENDPOINT_URL="https://s3.amazonaws.com"  # 或其他 S3 兼容服务的端点
   export S3_BUCKET="your_bucket_name"
3. 设置 LLM API Key：
   export OPENAI_KEY="your_openai_api_key"
4. 在 S3 存储桶中准备数据文件（支持 jsonl 或 plaintext 格式）

数据格式要求：
- jsonl 格式：每行一个 JSON 对象，包含 content 字段
  例如: {"content": "这是一段文本"}
- plaintext 格式：每行一段纯文本

支持的路径格式：
- 单个文件：path/to/file.jsonl
- 目录（读取所有文件）：path/to/directory/
"""

import os
import sys

from dingo.config import InputArgs
from dingo.exec import Executor

if __name__ == '__main__':
    # S3 配置信息
    # 方式 1: 从环境变量中获取（推荐）
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")
    S3_BUCKET = os.getenv("S3_BUCKET", "")

    # 检查 S3 配置是否完整
    if not all([S3_ACCESS_KEY, S3_SECRET_KEY, S3_ENDPOINT_URL, S3_BUCKET]):
        print("错误：S3 配置不完整！")
        print("请设置以下环境变量：")
        print("  - S3_ACCESS_KEY: S3 Access Key")
        print("  - S3_SECRET_KEY: S3 Secret Key")
        print("  - S3_ENDPOINT_URL: S3 服务端点 URL (如: https://s3.amazonaws.com)")
        print("  - S3_BUCKET: S3 存储桶名称")
        print("\n示例：")
        print("  export S3_ACCESS_KEY='your_access_key'")
        print("  export S3_SECRET_KEY='your_secret_key'")
        print("  export S3_ENDPOINT_URL='https://s3.amazonaws.com'")
        print("  export S3_BUCKET='your_bucket_name'")
        print("\n或者直接在代码中修改配置（不推荐，注意安全）")
        sys.exit(1)

    # LLM 配置信息
    OPENAI_MODEL = 'deepseek-chat'
    OPENAI_URL = 'https://api.deepseek.com/v1'
    OPENAI_KEY = os.getenv("OPENAI_KEY")

    if not OPENAI_KEY:
        print("警告：未设置 OPENAI_KEY 环境变量，LLM 评估可能失败")
        print("请设置: export OPENAI_KEY='your_api_key'")

    input_data = {
        # 数据文件路径
        # 单个文件示例："data/test.jsonl"
        # 目录示例："data/test/" （以 / 结尾会读取目录下所有文件）
        "input_path": "path/to/your/data.jsonl",

        # 数据集配置
        "dataset": {
            "source": "s3",  # 使用 S3 数据源
            "format": "jsonl",  # 支持 "jsonl" 或 "plaintext"
            "field": {
                "content": "content"  # 从 JSON 中提取的字段名
            },
            # S3 连接配置
            "s3_config": {
                "s3_ak": S3_ACCESS_KEY,
                "s3_sk": S3_SECRET_KEY,
                "s3_endpoint_url": S3_ENDPOINT_URL,
                "s3_bucket": S3_BUCKET,
                "s3_addressing_style": "path",  # 可选值: "path" 或 "virtual"
            }
        },

        # 执行器配置
        "executor": {
            "prompt_list": ["PromptRepeat"],  # 使用的 Prompt 列表
            "result_save": {
                "bad": True,
                "good": True
            }
        },

        # 评估器配置
        "evaluator": {
            "llm_config": {
                "LLMTextQualityPromptBase": {
                    "model": OPENAI_MODEL,
                    "key": OPENAI_KEY,
                    "api_url": OPENAI_URL,
                }
            }
        }
    }

    # 创建 InputArgs 实例
    input_args = InputArgs(**input_data)

    # 创建执行器
    executor = Executor.exec_map["local"](input_args)

    # 执行评估
    result = executor.execute()

    # 打印结果
    print(result)

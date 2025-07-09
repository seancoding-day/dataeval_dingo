# 开始你的第一步

## 安装

### 基础安装
1. 使用conda准备 dingo 运行环境:
```shell
conda create --name dingo python=3.10 -y

conda activate dingo
```

2. 安装 dingo:
- pip安装:
```shell
pip install dingo_python
```

- 如果希望使用 dingo 的最新功能，也可以从源代码构建它：
```shell
git clone git@github.com:MigoXLab/dingo.git dingo
cd dingo
pip install -e .
```

### 进阶安装
如果想要体验全部的 dingo 功能，那么需要安装所有的可选依赖:
```shell
pip install -r requirements/contribute.txt
pip install -r requirements/docs.txt
pip install -r requirements/optional.txt
pip install -r requirements/web.txt
```

## 快速开始

### 概览
在 dingo 中启动一个评估任务可以通过以下2种方式：命令行、代码。

**命令行启动**
```shell
python -m dingo.run.cli
   --input_path data.txt
   --dataset local 
   --data_format plaintext
   -e sft
   --save_data True
```

**代码启动**
```python
from dingo.exec import Executor
from dingo.io import InputArgs

input_data = {
    "input_path": "data.txt",
    "dataset": "local",
    "data_format": "plaintext",
    "eval_group": "sft",
    "save_data": True
}
input_args = InputArgs(**input_data)
executor = Executor.exec_map["local"](input_args)
result = executor.execute()
print(result)
```

### 评估结果
评估完成后，评估结果将打印如下字段:
+ task_id
+ task_name
+ input_path
+ output_path
+ create_time
+ finish_time
+ score
+ num_good
+ num_bad
+ type_ratio
+ name_ratio

所有运行输出将定向到 outputs 目录，结构如下：
```
outputs/
├── 20250609_101837_50b5c0be
├── 20250609_111057_5d250cf6            # 每个任务一个文件夹
│   ├── QUALITY_BAD_COMPLETENESS        # 评估阶段的一级类型
│   │   ├── RuleSentenceNumber.jsonl    # 评估阶段的二级类型
│   │   └── RuleWordNumber.jsonl
│   ├── QUALITY_BAD_EFFECTIVENESS       
│   │   ├── RuleColonEnd.jsonl          
│   │   └── RuleEnterAndSpace.jsonl
│   └── summary.json                    # 单个任务的汇总结果
├── ...
```

# 教程

# 规则

# 提示词

# 进阶教程
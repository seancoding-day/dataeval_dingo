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
   --save_data
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

## 整体概括
本项目的架构可以分为以下3个模块：Data、Evaluator、Executor
+ Data: 负责数据的加载与格式转化
+ Evaluator: 负责评估的执行
+ Executor: 负责任务的分配与调度

![Architecture of dingo](./docs/assets/architeture.png)

## 基础配置
dingo 启动方式具有2种，因此配置方式也分为以下2种情况:
1. [命令行配置列表](docs/config.md#cli-config)
2. [代码配置列表](docs/config.md#sdk-config)

**命令行启动**  
在命令行环境中，所有配置均以 参数键值对 的形式指定，遵从标准 CLI 语法规则，通过 --参数名 参数值 的方式传递每个配置项。

```shell
python -m dingo.run.cli
   --input_path data.txt
   --dataset local 
   --data_format plaintext
   -e sft
   --save_data
```

**代码启动**  
在代码环境中，配置都是 Python 格式的，遵从基本的 Python 语法，通过定义变量的形式指定每个配置项。

```python
from dingo.io import InputArgs

input_data = {
    "input_path": "data.txt",
    "dataset": "local",
    "data_format": "plaintext",
    "eval_group": "sft",
    "save_data": True
}
input_args = InputArgs(**input_data)
```

## 加载数据
如果想要 dingo 顺利读入数据，那么需要在配置时设置以下参数:
- input_path
- dataset
- data_format

数据读入后，进入格式转化阶段，此时执行字段的映射，因此需要在配置时设置以下参数:
- column_id
- column_prompt
- column_content

最终数据以 [Data](dingo/io/input/Data.py) 类对象的形式在项目中流转。  
如果用户在配置时将参数 save_raw 设置为True，那么 Data 类对象的 raw_data 有值否则为空字典。

## 设置并发
dingo 默认状态下没有开启并发，如果有大规模评估任务需要开启并发，那么应该在配置时设置以下参数:
+ max_workers
+ batch_size

以上2个参数应当搭配使用，如果max_workers设置为10但是batch_size设置为1，那么评估的效率不会得到较大提升。
建议batch_size大于等于max_workers。

## 结果保存
评估任务完成后会在当前目录下创建 outputs 文件夹并且不保存原始数据格式，除非用户在配置时设置了以下参数:
+ save_data
+ save_raw
+ save_correct
+ output_path

上文中评估阶段的二级类型jsonl文件中的每条结果数据收到配置参数 save_raw 的影响。  
如果 save_raw 设置为True，那么将执行 [ResultInfo](dingo/io/output/ResultInfo.py) 类的 to_dict_raw 函数，否则将执行 to_dict 函数。

## 启动前端页面
dingo 评估任务结束后，如果保存了评估结果，那么就可以通过一下方式启动前端页面展示结果:
```shell
python -m dingo.run.vsl --input outputs/20250609_101837_50b5c0be
```

# 规则

# 提示词

# 进阶教程
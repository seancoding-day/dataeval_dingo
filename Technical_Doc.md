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

# 教程

# 规则

# 提示词

# 进阶教程
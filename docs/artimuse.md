# Artimuse 图像质量评估规则

## 概述

RuleImageArtimuse 基于 ArtiMuse 在线服务对输入图片进行美学质量评估。规则会创建评估任务并轮询状态，取得总体分数及服务端返回的细粒度信息；随后与阈值比较，给出 Good/Bad 判定，并在结果中回传完整的可解释信息。

测试数据使用 JSONL 格式构造，每行一个 JSON 对象，至少包含 id 与 content 字段，其中 content 为可公网访问的图片 URL。项目中提供了 test/data/test_imgae_artimuse.jsonl 作为模板，亦可自行仿照编写，例如：{"id": "1", "content": "https://example.com/a.jpg"}，{"id": "2", "content": "https://example.com/b.jpg"}。

在仓库根目录直接运行 python examples/artimuse/artimuse.py 即可调用在线 ArtiMuse 接口完成评估，或在自定义的 InputArgs 中设置 output_path 指向你的本地目录以指定输出位置。执行后，LocalExecutor 会在该目录下创建以时间戳与 8 位短 ID 命名的子目录，并写入 summary.json 与逐条样本的明细 JSONL，可通过命令 python -m dingo.run.vsl --input <输出目录> 打开静态页面查看结果。

评测结果的判定逻辑与代码一致：从服务端返回的 data 中读取 score_overall 与设定阈值比较，低于阈值判定为 BadImage，否则为 GoodImage；返回的 reason 字段保存了服务端 data 的字符串化 JSON，至少包含 phase 与 score_overall 等关键字段，便于后续分析与追溯。


样例 20250903_203109_deb630bc 即是通过 Dingo 的本地执行引擎运行 RuleImageArtimuse 自动生成的输出。执行器会在指定的 output_path 下新建以时间戳和 8 位短 ID 组成的目录（形如 YYYYmmdd_HHMMSS_shortid），并写入 summary.json 以及逐条样本的明细 JSONL。该样例目录包含 Artimuse_Succeeded/BadImage.jsonl、Artimuse_Succeeded/GoodImage.jsonl 和 summary.json。

在仓库根目录直接运行 examples/artimuse/artimuse.py 即可调用在线 ArtiMuse 接口完成评估；若在 InputArgs 中将 output_path 指向你的本地目录，则会生成与上文相同结构的目录。评估完成后，可用命令 python -m dingo.run.vsl --input <上述输出目录> 打开静态页面进行可视化。

## 规则配置

- **规则名称**: `QUALITY_BAD_IMG_ARTIMUSE`
- **阈值配置**: 范围 0 - 10，默认阈值为 6 分（可配置）
- **API 端点**: `https://artimuse.intern-ai.org.cn/`

## 核心方法

### `eval(cls, input_data: Data) -> ModelRes`

这是规则的主要评估方法，接收包含图像 URL 的 `Data` 对象，返回评估结果。

#### 参数
- `input_data`: 包含图像 URL 的 Data 对象
  - `data_id`: 数据标识符
  - `content`: 图像的网络 URL（本规则仅读取该字段）

#### 处理流程

1. **创建评估任务**
   - 向 ArtiMuse 接口 POST `{refer_path}/api/v1/task/create_task`
   - 请求体包含图片地址，内部固定 `style=1`

2. **获取任务状态**
   - 先等待 5 秒
   - 之后每 5 秒 POST `{refer_path}/api/v1/task/status` 查询一次，直到 `phase == "Succeeded"`
   - 代码未设置请求超时，也未限制最大轮询次数

3. **返回评估结果**
   - 读取 `score_overall` 与阈值比较，低于阈值判定为 `BadImage`，否则为 `GoodImage`
   - 将服务端返回的 `data` 以字符串化 JSON 放入 `reason`

#### 返回值

返回 `ModelRes` 对象，包含以下属性：

- `error_status`: 布尔值，表示图像质量是否不合格（低于阈值）
- `type`: 评估结果类型（"Artimuse_Succeeded" 或 "Artimuse_Fail"）
- `name`: 评估结果名称（"BadImage" 或 "GoodImage" 或 "Exception"）
- `reason`: 包含详细评估信息或异常信息的数组（字符串化 JSON）

## 异常处理

当评估过程中发生异常时，返回的 `ModelRes` 对象将包含：

- `error_status`: `False`
- `type`: `"Artimuse_Fail"`
- `name`: `"Exception"`
- `reason`: 包含异常信息的数组

## 使用示例

```python
# 创建测试数据
data = Data(
    data_id='1',
    content="https://example.com/image.jpg"
)

# 执行评估
res = RuleImageArtimuse.eval(data)

# 输出结果
print(res)
```

## 依赖项

- `requests`: 用于发送 HTTP 请求
- `time`: 用于控制请求间隔
- `json`: 用于处理返回的 JSON 数据

## 注意事项

1. 确保提供的图像 URL 可公开访问（避免鉴权、重定向或短链失效）
2. 首次查询前等待 5 秒，之后每 5 秒轮询一次；总耗时取决于服务端完成时间
3. 阈值与接口端点可通过 `dynamic_config` 调整：`threshold` 与 `refer_path`

## 错误排查

如果评估失败，可能的原因包括：

1. 网络连接问题
2. ArtiMuse 服务不可用
3. 图像 URL 不可访问
4. 服务端长时间无响应或不可达

建议在使用前确保网络环境稳定，并验证图像 URL 的有效性。

# Artimuse 图像质量评估规则

## 概述

`RuleImageArtimuse` 是一个基于 Artimuse API 的图像质量评估规则类，用于判断输入图像的质量是否达到合格标准。该规则通过调用 Artimuse 服务的图像评估接口，获取图像的总体评分和各个方面的详细评估结果。

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
  - `content`: 图像的网络 URL

#### 处理流程

1. **创建评估任务**
   - 向 Artimuse API 发送 POST 请求创建图像评估任务
   - 指定评估风格为 `1`（可根据需要调整：1-专业, 2-毒舌）
   - 设置 30 秒超时时间

2. **获取任务状态**
   - 等待 2 秒后开始查询任务状态
   - 最多尝试 5 次查询，每次间隔 2 秒
   - 当任务状态变为 `Succeeded` 时停止查询

3. **返回评估结果**
   - 根据总体评分判断图像质量是否合格
   - 返回包含详细评估信息的 `ModelRes` 对象

#### 返回值

返回 `ModelRes` 对象，包含以下属性：

- `error_status`: 布尔值，表示图像质量是否不合格（低于阈值）
- `type`: 评估结果类型（"Artimuse_Succeeded" 或 "Artimuse_Fail"）
- `name`: 评估结果名称（"BadImage" 或 "GoodImage"）
- `reason`: 包含详细评估信息的数组

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

1. 确保提供的图像 URL 可公开访问
2. 评估过程可能需要较长时间（最多约 12 秒）
3. 当前使用固定风格参数进行评估，可根据需要调整
4. 阈值可根据实际需求通过 `dynamic_config` 进行调整

## 错误排查

如果评估失败，可能的原因包括：

1. 网络连接问题
2. Artimuse 服务不可用
3. 图像 URL 不可访问
4. 请求超时

建议在使用前确保网络环境稳定，并验证图像 URL 的有效性。

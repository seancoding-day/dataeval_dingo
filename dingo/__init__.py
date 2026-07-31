import os

# 为无法访问 huggingface.co 的环境提供默认镜像。
# 必须在任何 huggingface_hub / transformers 被导入之前设置，
# 因为 HF_ENDPOINT 在 huggingface_hub 导入时即被固定读取。
# 使用 setdefault 保证用户可通过外部环境变量覆盖为其他镜像或官方地址。
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

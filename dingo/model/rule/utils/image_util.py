from huggingface_hub import snapshot_download


def download_similar_tool() -> str:
    file_path = snapshot_download(repo_id="OFA-Sys/chinese-clip-vit-base-patch16")
    return file_path

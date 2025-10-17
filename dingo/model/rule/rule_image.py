import json
import os
import time

import numpy as np
import requests
from PIL import Image

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io import Data
from dingo.model.model import Model
from dingo.model.modelres import ModelRes
from dingo.model.rule.base import BaseRule


@Model.rule_register("QUALITY_BAD_IMG_EFFECTIVENESS", ["img"])
class RuleImageValid(BaseRule):
    """check whether image is not all white or black"""

    # Metadata for documentation generation
    _metric_info = {
        "category": "Rule-Based IMG Quality Metrics",
        "quality_dimension": "IMG_EFFECTIVENESS",
        "metric_name": "RuleImageValid",
        "description": "Checks whether image is not all white or black, ensuring visual content validity",
        "paper_title": "",
        "paper_url": "",
        "paper_authors": "",
        "evaluation_results": ""
    }

    dynamic_config = EvaluatorRuleArgs()

    @classmethod
    def eval(cls, input_data: Data) -> ModelRes:
        res = ModelRes()
        if isinstance(input_data.image[0], str):
            img = Image.open(input_data.image[0])
        else:
            img = input_data.image[0]
        img_new = img.convert("RGB")
        img_np = np.asarray(img_new)
        if np.all(img_np == (255, 255, 255)) or np.all(img_np == (0, 0, 0)):
            res.error_status = True
            res.type = cls.metric_type
            res.name = cls.__name__
            res.reason = ["Image is not valid: all white or black"]
        return res


@Model.rule_register("QUALITY_BAD_IMG_EFFECTIVENESS", ["img"])
class RuleImageSizeValid(BaseRule):
    """check whether image ratio of width to height is valid"""

    # Metadata for documentation generation
    _metric_info = {
        "category": "Rule-Based IMG Quality Metrics",
        "quality_dimension": "IMG_EFFECTIVENESS",
        "metric_name": "RuleImageSizeValid",
        "description": "Checks whether image ratio of width to height is within valid range",
        "paper_title": "",
        "paper_url": "",
        "paper_authors": "",
        "evaluation_results": ""
    }

    dynamic_config = EvaluatorRuleArgs()

    @classmethod
    def eval(cls, input_data: Data) -> ModelRes:
        res = ModelRes()
        if isinstance(input_data.image[0], str):
            img = Image.open(input_data.image[0])
        else:
            img = input_data.image[0]
        width, height = img.size
        aspect_ratio = width / height
        if aspect_ratio > 4 or aspect_ratio < 0.25:
            res.error_status = True
            res.type = cls.metric_type
            res.name = cls.__name__
            res.reason = [
                "Image size is not valid, the ratio of width to height: "
                + str(aspect_ratio)
            ]
        return res


@Model.rule_register("QUALITY_BAD_IMG_EFFECTIVENESS", ["img"])
class RuleImageQuality(BaseRule):
    """check whether image quality is good."""

    # Metadata for documentation generation
    _metric_info = {
        "category": "Rule-Based IMG Quality Metrics",
        "quality_dimension": "IMG_EFFECTIVENESS",
        "metric_name": "RuleImageQuality",
        "description": "Evaluates image quality using NIMA (Neural Image Assessment) metrics",
        "paper_title": "NIMA: Neural Image Assessment",
        "paper_url": "https://arxiv.org/abs/1709.05424",
        "paper_authors": "Talebi & Milanfar, 2018",
        "evaluation_results": ""
    }

    dynamic_config = EvaluatorRuleArgs(threshold=5.5)

    @classmethod
    def eval(cls, input_data: Data) -> ModelRes:
        import pyiqa
        import torch

        res = ModelRes()
        if isinstance(input_data.image[0], str):
            img = Image.open(input_data.image[0])
        else:
            img = input_data.image[0]
        device = (
            torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        )
        iqa_metric = pyiqa.create_metric("nima", device=device)
        score_fr = iqa_metric(img)
        score = score_fr.item()
        if score < cls.dynamic_config.threshold:
            res.error_status = True
            res.type = cls.metric_type
            res.name = cls.__name__
            res.reason = ["Image quality is not satisfied, ratio: " + str(score)]
        return res


@Model.rule_register("QUALITY_BAD_IMG_SIMILARITY", [])
class RuleImageRepeat(BaseRule):
    """Check for duplicate images using PHash and CNN methods."""

    # Metadata for documentation generation
    _metric_info = {
        "category": "Rule-Based IMG Quality Metrics",
        "quality_dimension": "IMG_SIMILARITY",
        "metric_name": "RuleImageRepeat",
        "description": "Detects duplicate images using PHash and CNN methods to ensure data diversity",
        "paper_title": "ImageNet Classification with Deep Convolutional Neural Networks",
        "paper_url": "https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks.pdf",
        "paper_authors": "Krizhevsky et al., 2012",
        "evaluation_results": ""
    }

    dynamic_config = EvaluatorRuleArgs()

    @classmethod
    def eval(cls, input_data: Data) -> ModelRes:
        from imagededup.methods import CNN, PHash

        res = ModelRes()
        image_dir = input_data.content
        if len(os.listdir(image_dir)) == 0:
            raise ZeroDivisionError(
                "The directory is empty, cannot calculate the ratio."
            )
        phasher = PHash()
        cnn_encoder = CNN()
        phash_encodings = phasher.encode_images(image_dir=image_dir)
        duplicates_phash = phasher.find_duplicates(encoding_map=phash_encodings)
        duplicate_images_phash = set()
        for key, values in duplicates_phash.items():
            if values:
                duplicate_images_phash.add(key)
                duplicate_images_phash.update(values)
        duplicates_cnn = cnn_encoder.find_duplicates(
            image_dir=image_dir, min_similarity_threshold=0.97
        )
        common_duplicates = duplicate_images_phash.intersection(
            set(duplicates_cnn.keys())
        )
        if common_duplicates:
            res.error_status = True
            res.type = cls.metric_type
            res.name = cls.__name__
            res.reason = [
                f"{image} -> {duplicates_cnn[image]}" for image in common_duplicates
            ]
            res.reason.append(
                {"duplicate_ratio": len(common_duplicates) / len(os.listdir(image_dir))}
            )
        return res


@Model.rule_register("QUALITY_BAD_IMG_RELEVANCE", [])
class RuleImageTextSimilarity(BaseRule):
    """Check similarity between image and text content"""

    # Metadata for documentation generation
    _metric_info = {
        "category": "Rule-Based IMG Quality Metrics",
        "quality_dimension": "IMG_RELEVANCE",
        "metric_name": "RuleImageTextSimilarity",
        "description": "Evaluates semantic similarity between image and text content using CLIP model",
        "paper_title": "Learning Transferable Visual Representations with Natural Language Supervision",
        "paper_url": "https://arxiv.org/abs/2103.00020",
        "paper_authors": "Radford et al., 2021",
        "evaluation_results": ""
    }

    dynamic_config = EvaluatorRuleArgs(threshold=0.17)

    @classmethod
    def eval(cls, input_data: Data) -> ModelRes:
        import nltk

        nltk.download("punkt_tab")
        from nltk.tokenize import word_tokenize
        from similarities import ClipSimilarity

        from dingo.model.rule.utils.image_util import download_similar_tool

        res = ModelRes()
        if not input_data.image or not input_data.content:
            return res
        if isinstance(input_data.image[0], str):
            img = Image.open(input_data.image[0])
        else:
            img = input_data.image[0]
        tokenized_texts = word_tokenize(input_data.content)
        if cls.dynamic_config.refer_path is None:
            similar_tool_path = download_similar_tool()
        else:
            similar_tool_path = cls.dynamic_config.refer_path[0]
        m = ClipSimilarity(model_name_or_path=similar_tool_path)
        scores = []
        for text in tokenized_texts:
            sim_score = m.similarity([img], [text])
            scores.append(sim_score[0][0])
        average_score = sum(scores) / len(scores)
        if average_score < cls.dynamic_config.threshold:
            res.error_status = True
            res.type = cls.metric_type
            res.name = cls.__name__
            res.reason = [
                "Image quality is not satisfied, ratio: " + str(average_score)
            ]
        return res


@Model.rule_register("QUALITY_BAD_IMG_ARTIMUSE", [])
class RuleImageArtimuse(BaseRule):
    # Metadata for documentation generation
    _metric_info = {
        "category": "Rule-Based IMG Quality Metrics",
        "quality_dimension": "IMG_ARTIMUSE",
        "metric_name": "RuleImageArtimuse",
        "description": "Evaluates image quality in the field of aesthetics using artimuse",
        "paper_title": "",
        "paper_url": "",
        "paper_authors": "",
        "evaluation_results": ""
    }

    dynamic_config = EvaluatorRuleArgs(threshold=6, refer_path=['https://artimuse.intern-ai.org.cn/'])

    @classmethod
    def eval(cls, input_data: Data) -> ModelRes:
        try:
            response_create_task = requests.post(
                cls.dynamic_config.refer_path[0] + 'api/v1/task/create_task',
                json={
                    "img_url": input_data.content,
                    "style": 1
                },
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "dingo",
                },
                # timeout=30  # 设置超时时间
            )
            response_create_task_json = response_create_task.json()
            # print(response_create_task_json)
            task_id = response_create_task_json.get('data').get('id')

            time.sleep(5)
            request_time = 0
            while (True):
                request_time += 1
                response_get_status = requests.post(
                    cls.dynamic_config.refer_path[0] + 'api/v1/task/status',
                    json={
                        "id": task_id
                    },
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "dingo",
                    },
                    # timeout=30  # 设置超时时间
                )
                response_get_status_json = response_get_status.json()
                # print(response_get_status_json)
                status_data = response_get_status_json.get('data')
                if status_data['phase'] == 'Succeeded':
                    break
                time.sleep(5)

            return ModelRes(
                error_status=True if status_data['score_overall'] < cls.dynamic_config.threshold else False,
                type="Artimuse_Succeeded",
                name="BadImage" if status_data['score_overall'] < cls.dynamic_config.threshold else "GoodImage",
                reason=[json.dumps(status_data, ensure_ascii=False)],
            )
        except Exception as e:
            return ModelRes(
                error_status=False,
                type="Artimuse_Fail",
                name="Exception",
                reason=[str(e)],
            )


@Model.rule_register("QUALITY_BAD_IMG_LABEL_OVERLAP", [])
class RuleImageLabelOverlap(BaseRule):
    _metric_info = {
        "category": "Rule-Based IMG Quality Metrics",
        "quality_dimension": "IMG_LABEL_OVERLAP",
        "metric_name": "RuleImageLabelOverlap",
        "description": "Detects overlapping bounding boxes in image annotations, marks full/partial overlap and generates visualization images",
        "paper_title": "",
        "paper_url": "",
        "paper_authors": "",
        "evaluation_results": ""
    }

    dynamic_config = EvaluatorRuleArgs(
        refer_path=['../../test/data/overlap_visual_image'],  # 用户保存图片路径
    )

    @classmethod
    def eval(cls, input_data: Data) -> ModelRes:
        import copy
        import json
        from pathlib import Path
        from PIL import Image, ImageDraw, ImageFont
        import logging

        res = ModelRes()

        try:
            # 1. 阈值参数
            iou_partial_threshold = 0.1
            iou_full_threshold = 0.9

            # 2. 解析输入数据
            content = input_data.content
            image_path = input_data.image[0] if (input_data.image and len(input_data.image) > 0) else None
            data_id = input_data.data_id

            # 3. 解析标注内容
            if isinstance(content, str):
                try:
                    annotations = json.loads(content)
                except json.JSONDecodeError as e:
                    res.error_status = True
                    res.reason = [f"content解析失败：{str(e)}，前50字符：{content[:50]}..."]
                    return res
            elif isinstance(content, dict):
                annotations = content
            else:
                res.error_status = True
                res.reason = [f"content类型错误：需dict/str，实际是{type(content).__name__}"]
                return res

            # 4. 验证数据有效性
            if not annotations:
                res.error_status = True
                res.reason = [f"id:{data_id} - annotations为空"]
                return res
            if not image_path or not os.path.exists(image_path):
                res.error_status = True
                res.reason = [f"id:{data_id} - 图片路径无效：{image_path}"]
                return res

            # 5. 提取边界框并计算重叠
            bboxes = [
                obj for obj in annotations.get('step_1', {}).get('result', [])
                if obj.get('valid', True) and all(k in obj for k in ['x', 'y', 'width', 'height'])
            ]

            has_overlap = False  # 是否符合阈值重叠（部分或完全）
            full_overlap_pairs = []
            partial_overlap_pairs = []

            if bboxes:
                n = len(bboxes)
                for i in range(n):
                    for j in range(i + 1, n):
                        # 计算IOU
                        box1 = bboxes[i]
                        box2 = bboxes[j]
                        x1 = max(box1["x"], box2["x"])
                        y1 = max(box1["y"], box2["y"])
                        x2 = min(box1["x"] + box1["width"], box2["x"] + box2["width"])
                        y2 = min(box1["y"] + box1["height"], box2["y"] + box2["height"])
                        intersection = max(0, x2 - x1) * max(0, y2 - y1)
                        area1 = box1["width"] * box1["height"]
                        area2 = box2["width"] * box2["height"]
                        union = area1 + area2 - intersection
                        iou = intersection / union if union != 0 else 0

                        # 判断是否符合阈值重叠
                        if iou >= iou_full_threshold:
                            full_overlap_pairs.append((i, j))
                            has_overlap = True
                        elif iou >= iou_partial_threshold:
                            partial_overlap_pairs.append((i, j))
                            has_overlap = True

                # 标记重叠边界框
                full_overlap_ids = set(idx for pair in full_overlap_pairs for idx in pair)
                partial_overlap_ids = set(idx for pair in partial_overlap_pairs for idx in pair) - full_overlap_ids
                new_annotations = copy.deepcopy(annotations)
                for idx, box in enumerate(new_annotations["step_1"]["result"]):
                    if idx in full_overlap_ids:
                        box["attribute"] = "full_overlap"
                    elif idx in partial_overlap_ids:
                        box["attribute"] = "partial_overlap"
            else:
                new_annotations = annotations

            # 6. 动态设置 res.name 和 res.type
            if has_overlap:
                # 符合阈值重叠：使用原名称和类型
                res.name = cls.__name__  # "RuleImageLabelOverlap"
                res.type = cls._metric_info["quality_dimension"]  # "IMG_LABEL_OVERLAP"
            else:
                # 不符合阈值重叠
                res.name = "GOOD_IMG_LABEL"  # 自定义非重叠名称
                res.type = "NO_LABEL_OVERLAP"  # 自定义非重叠类型

            # 7. 生成可视化标注狂框重叠图片
            output_dir = Path(cls.dynamic_config.refer_path[0])
            output_dir.mkdir(parents=True, exist_ok=True)
            vis_path = str(output_dir / f"overlap_{data_id}.png")

            try:
                img = Image.open(image_path).convert("RGB")
                draw = ImageDraw.Draw(img)
                for idx, box in enumerate(bboxes):
                    x, y, w, h = box["x"], box["y"], box["width"], box["height"]
                    if idx in full_overlap_ids:
                        color = (255, 0, 0)
                    elif idx in partial_overlap_ids:
                        color = (255, 255, 0)
                    else:
                        color = (0, 255, 0)
                    draw.rectangle([(x, y), (x + w, y + h)], outline=color, width=3)
                    draw.text((x, max(0, y - 15)), f"Box {idx}", fill=color, font=ImageFont.load_default())
                img.save(vis_path)
            except Exception as e:
                logging.warning(f"可视化生成失败：{str(e)}")
                vis_path = None

            # 8. 整理结果
            final_result = {
                "id": data_id,
                "has_overlap": has_overlap,
                "overlap_stats": {
                    "full_overlap_pairs": len(full_overlap_pairs),
                    "partial_overlap_pairs": len(partial_overlap_pairs),
                    "total_boxes": len(bboxes)
                },
                "visualization_path": vis_path
            }

            res.error_status = has_overlap  # 重叠图像标记为错误状态（可选）
            res.reason = [json.dumps(final_result, ensure_ascii=False)]

        except Exception as global_e:
            res.error_status = False
            res.reason = [f"全局处理错误：{str(global_e)}，id:{input_data.data_id}"]
            # 异常情况仍使用原类型，便于排查
            res.name = cls.__name__
            res.type = cls._metric_info["quality_dimension"]

        return res


@Model.rule_register("QUALITY_BAD_IMG_LABEL_VISUALIZATION", [])
class RuleImageLabelVisualization(BaseRule):
    _metric_info = {
        "category": "Rule-Based IMG Quality Metrics",
        "quality_dimension": "IMG_LABEL_VISUALIZATION",
        "metric_name": "RuleImageLabelVisualization",
        "description": "",  # TODO: lindong input
        "paper_title": "",
        "paper_url": "",
        "paper_authors": "",
        "evaluation_results": ""
    }

    dynamic_config = EvaluatorRuleArgs()

    @classmethod
    def eval(cls, input_data: Data) -> ModelRes:
        pass


if __name__ == "__main__":
    data = Data(
        data_id='1',
        content="https://openxlab.oss-cn-shanghai.aliyuncs.com/artimuse/upload/ef39eef6-2b40-4ea3-8285-934684734298-stsupload-1753254621827-dog.jpg"
    )
    res = RuleImageArtimuse.eval(data)
    print(res)

import re
from typing import List

import diff_match_patch as dmp_module

from dingo.io import Data
from dingo.model import Model
from dingo.model.llm.base_openai import BaseOpenAI
from dingo.model.modelres import ModelRes
from dingo.model.prompt.prompt_html_extract_compare_v2 import PromptHtmlExtractCompareV2
from dingo.model.response.response_class import ResponseJudgementReason
from dingo.utils import log


@Model.llm_register("LLMHtmlExtractCompareV2")
class LLMHtmlExtractCompareV2(BaseOpenAI):
    """
    HTML提取工具对比评估 V2 版本

    主要改进：
    1. 使用 diff-match-patch 算法预先提取文本差异
    2. 只向 LLM 提供独有内容和共同内容，大幅减少 token 消耗
    3. 支持中英文双语提示词
    4. 使用 A/B/C 判断格式，更清晰地表达哪个工具更好

    输入数据要求：
    - input_data.prompt: 工具A提取的文本
    - input_data.content: 工具B提取的文本
    - input_data.raw_data.get("language", "en"): 语言类型 ("zh" 或 "en")
    """

    prompt = PromptHtmlExtractCompareV2

    @classmethod
    def extract_text_diff(cls, text_a: str, text_b: str, max_diff_length: int = 10000) -> dict:
        """
        使用 diff-match-patch 算法提取两段文本的差异

        Args:
            text_a: 工具A提取的文本
            text_b: 工具B提取的文本
            max_diff_length: 差异文本的最大长度限制

        Returns:
            dict: 包含 unique_a, unique_b, common 三个字段
        """
        dmp = dmp_module.diff_match_patch()

        # 计算差异
        diff = dmp.diff_main(text_a, text_b)
        dmp.diff_cleanupEfficiency(diff)

        unique_a_list = []
        unique_b_list = []
        common_list = []

        for single_diff in diff:
            if single_diff[0] == -1:  # 仅在 text_a 中
                unique_a_list.append(single_diff[1])
            elif single_diff[0] == 1:  # 仅在 text_b 中
                unique_b_list.append(single_diff[1])
            elif single_diff[0] == 0:  # 共同内容
                common_list.append(single_diff[1])

        return {
            "unique_a": "".join(unique_a_list)[:max_diff_length],
            "unique_b": "".join(unique_b_list)[:max_diff_length],
            "common": "".join(common_list)[:max_diff_length],
        }

    @classmethod
    def build_messages(cls, input_data: Data) -> List:
        """
        构建 LLM 输入消息

        主要流程：
        1. 提取工具A和工具B的文本
        2. 使用 diff-match-patch 计算差异
        3. 根据语言选择合适的提示词
        4. 填充差异内容到提示词中
        """
        # 获取输入文本
        text_tool_a = input_data.prompt
        text_tool_b = input_data.content

        # 获取配置参数
        language = input_data.raw_data.get("language", "en")

        # 计算文本差异
        diff_result = cls.extract_text_diff(text_tool_a, text_tool_b)

        # 根据语言选择提示词
        if language == "zh":
            prompt_template = cls.prompt.content_cn
        else:
            prompt_template = cls.prompt.content_en

        # 填充提示词
        prompt_content = prompt_template.format(
            text_unique_tool_a=diff_result["unique_a"],
            text_unique_tool_b=diff_result["unique_b"],
            text_common=diff_result["common"]
        )

        messages = [
            {
                "role": "user",
                "content": prompt_content
            }
        ]

        return messages

    @classmethod
    def process_response(cls, response: str) -> ModelRes:
        """
        处理 LLM 返回结果

        解析格式：
        1. 提取 <Judgement>A/B/C</Judgement> 标签中的判断结果
        2. 其余内容作为推理过程

        返回映射：
        - A -> TOOL_ONE_BETTER (工具A更好)
        - B -> TOOL_EQUAL (两者相同)
        - C -> TOOL_TWO_BETTER (工具B更好)
        """
        log.info(response)

        # 提取判断结果
        judgement_match = re.search(r"<Judgement>([ABC])</Judgement>", response)

        if not judgement_match:
            # 如果没有找到标准格式，尝试其他可能的格式
            judgement_match = re.search(r"判断[：:]\s*([ABC])", response)
            if not judgement_match:
                judgement_match = re.search(r"答案[：:]\s*([ABC])", response)

        if not judgement_match:
            raise ValueError(f"无法从响应中提取判断结果: {response}")

        judgement = judgement_match.group(1)

        # 提取推理过程（去除判断标签）
        reason = re.sub(r"<Judgement>[ABC]</Judgement>", "", response).strip()

        # 创建结果对象
        result = ModelRes()

        # 映射判断结果到类型
        if judgement == "A":
            result.type = "TOOL_ONE_BETTER"
            result.error_status = False  # 工具A更好，认为正常
        elif judgement == "B":
            result.type = "TOOL_EQUAL"
            result.error_status = False  # 两者相同，认为正常
        elif judgement == "C":
            result.type = "TOOL_TWO_BETTER"
            result.error_status = True  # 工具B更好，标记为错误（因为期望A更好）

        # 设置名称（使用判断结果）
        result.name = f"Judgement_{judgement}"

        # 设置推理过程
        result.reason = [reason]

        return result

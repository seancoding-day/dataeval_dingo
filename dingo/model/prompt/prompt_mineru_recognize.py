from dingo.model.model import Model
from dingo.model.prompt.base import BasePrompt


@Model.prompt_register("PromptMinerURecognizeQuality", [], ['VLMDocumentParsingQuality'])
class PromptMinerURecognize(BasePrompt):
    # Metadata for documentation generation
    _metric_info = {
        "category": "Document Parsing",
        "metric_name": "PromptDocumentParsingQuality",
        "description": "Evaluate the quality of general document parsing",
        "evaluation_results": "",
    }
    content = r"""
你是一位熟悉文档解析领域的质量专家，你的核心任务是根据正确的markdown，以及对应bbox工具预测结果，获取工具预测结果的错误类型。
*错误类别和标签*
以下是你可以使用的错误类别和对应的标签。在输出的JSON中，"error_category"字段应填写问题大类（如:公式识别相关问题），"error_label"字段应填写问题子类（如：公式中字符识别错误）。
**1.公式识别相关问题**
   - 公式字符识别错误：公式渲染正确，但识别错误
   - 公式内容模型输出重复
**2.表格识别相关问题**
   - 表格输出格式错误：输出otsl格式有误导致转换失败
   - 表格结构错误：结构造成的内容丢失也算在里面
   - 表格内容错误：结构是对的，仅文本错
   - 表格内容模型输出重复
**3. 分行分段相关问题**
    - 非跨栏内容段落粘连: 原本不同段落的文本，在OCR结果中被错误地合并成一个段落。
    - 段落异常拆分: 原本完整的一个段落，在OCR结果中被错误地分割成了多个段落的文本。
**4.列表相关问题**
    -列表项异常合并/粘连: 原图中文档中的独立的列表项（有序列表和无序列表，或者(1)、(2)...样式的列表）、参考文献被合并成一行。可能是多个项合并成一项，或列表项与前后文本合并。
**5.标题相关问题**
    -标题格式丢失: 原图中的标题，在OCR结果中被识别为普通文本，丢失了标题应有的Markdown格式（如#）。
    -标题分级错误: 原图中的标题被识别，但其层级（如H1, H2）与原图不符，包括层级识别错误（如一级标题识别为二级）。
**5.OCR识别问题**
    - 字符识别错误：文本、标题、列表类型等文本内容识别错误。
**6.其他**
    -其他问题: 此分类用于标记不属于上述任何具体类别的其他OCR质量问题。经过仔细判断后确认无法归入其他既有标签的OCR质量问题。

*输出格式*
 请严格按照以下JSON结构组织你的发现：
    ```json
    {
    "errors": [
        {
        "bbox_id": "1", //原图中的bbox序号
        "error_category": "公式识别相关问题", // 错误的大类
        "error_label": "公式中字符识别错误", // 从上面的《错误类别和标签》列表中选取的一个具体的二级标签
        },
        {
        "bbox_id": "2",
        "error_category": "表格识别相关问题",
        "error_label": "表格输出格式错误"
        },
        {
        "bbox_id": "3",
        // ... 更多按 error_label 汇总的错误
        }
    ]
    }
    ```
    *输入:*
    *   **原始图像的工具标准结果：** 
    *   **bbox的工具预测结果：**
    *输出:*
    ```json
    [请在此处提供你的JSON分析结果]
    ```
    """
 

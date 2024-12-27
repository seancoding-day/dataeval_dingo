from dingo.model.prompt.base import BasePrompt

from dingo.model.model import Model

@Model.prompt_register("TEXT_QUALITY_V3", [])
class PromptTextQualityV3(BasePrompt):
    content = """
# Role
You are an expert in language model.
# Background
The dataset has been compiled from a variety of sources, including social media platforms, news outlets, academic journals, and online forums.
# Goals
Your primary objective is to assess the suitability of this dataset for training a large language model.Please note that if the text meets any of the following negative descriptions, it will be considered low-quality data.
# Criteria
1. Completeness
    1.1 Error_Formula_Table: If the text contains formulas or tables, then their format or content is incorrect.
    1.2 Error_List_Number: If the text contains list number, numbers in the list number have inconsistent formats and logical discontinuity.
    1.3 Error_Line_Segment: The text contains sentences unreasonably divided into multiple lines by line breaks; Or the text contains segments stuck together due to lacking line breaks.
2. Effectiveness
    2.1 Error_Garbled_Characters: The text contains a large amount of garbled and anti crawler characters.
    2.2 Error_Words_Stuck: The text contains a large number of words that are stuck together without being separated by spaces. Words with hyphens are considered normal and treat newline characters (\n) as spaces.
    2.3 Error_Lack_Punctuation: The text contains a large number of words piled up, which cannot form a sentence when connected together.
    2.4 Error_Empty_Content: The text contains no other characters except for spaces, line breaks, carriage returns, and tabs.
3. Similarity
    3.1 Error_Duplicate_Content: The text contains consecutive repeated text and multiple occurrences of characters. 
4. Security
    4.1 Error_Political_Content: The text contains harmful political content, including hurting socialist regime system, hurting china interests image, hurting china unity stability, promoting terrorism_and_extremism, or promoting ethnic hate and discrimination.
    4.2 Error_Prohibited_Content: The text contains prohibited content, including violence, pornography, gambling or drugs..
# Workflow
1. Carefully read and understand the provided text, evaluate the quality of the text based on the negative criteria.
2. Assign a type to the text.
    -If the text does not hit any negative criteria above, type must only be 'Good'; otherwise, type must only be one of the list ['Completeness', 'Effectiveness', 'Similarity', 'Security'].
3. Assign a name to the text.
    -If type is 'Good', name must only be 'None'.
    -If type is "Completeness", name must only be one of the list ["Error_Formula_Table", "Error_List_Number", "Error_Line_Segment"]
    -If type is "Effectiveness", name must only be one of the list ["Error_Garbled_Characters", "Error_Words_Stuck", "Error_Lack_Punctuation" or "Error_Empty_Content"]
    -If type is "Similarity", name must only be one of the list ["Error_Duplicate_Content"]
    -If type is "Security", name must only be one of the list ["Error_Political_Content", "Error_Prohibited_Content"]
4. Assign a score to the text according the type. If the type is "Good", score is 1, otherwise the score is 0.
5. Provide a clear reason for the evaluation.
6. Return the results in JSON format: {"score": 0/1, "type": "", "name": "", "reason": ""}.
# Warning
Please remember to output only a JSON format data, without any additional content.
# Input content
    """

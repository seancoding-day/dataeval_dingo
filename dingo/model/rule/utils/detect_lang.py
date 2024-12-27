import fasttext

from typing import Tuple, Dict, Any
from huggingface_hub import hf_hub_download

from dingo.utils import log

_global_lang_detect = []
_fasttext_path = ''

def set_fasttext(path: str):
    global _fasttext_path
    _fasttext_path = path

def download_fasttext() -> str:
    if _fasttext_path:
        return _fasttext_path
    file_path = hf_hub_download(repo_id='chupei/fasttext.lib.176.bin', filename='lid.176.bin')
    return file_path


class LanguageIdentification:
    """
    A class used to identify the language of a given text using a pre-trained fastText model.

    Methods:
        predict(text: str) -> Tuple[Tuple[str], Tuple[float]]:
            Predicts the language of the given text and returns the top 5 matching languages
            along with their probabilities.
    """
    def __init__(self) -> None:
        """
        Initializes the LanguageIdentification class with the pre-trained fastText model.
        """
        log.info("========= downloading fasttext =========")
        pretrained_lang_model = download_fasttext()
        self.model = fasttext.load_model(pretrained_lang_model)

    def predict(self, text: str) -> Tuple[Tuple[str], Tuple[float]]:
        """
        Predicts the language of the given text and returns the top 5 matching languages along with their probabilities.

        Args:
            text (str): The text for which the language needs to be identified.

        Returns:
            Tuple[Tuple[str], Tuple[float]]: A tuple containing the top 5 matching languages and their probabilities.
        """
        text = text.replace("\n", " ")
        predictions, probabilities = self.model.predict(text, k=5)

        return predictions, probabilities


def get_lang_detect() -> LanguageIdentification:
    """
    Returns the language detection instance.

    Returns:
        LanguageIdentification: The language detection instance.
    """
    if len(_global_lang_detect) == 0:
        _global_lang_detect.append(LanguageIdentification())
    return _global_lang_detect[0]


def release_lang_detect():
    """
    Releases the language detection instance.
    """
    while len(_global_lang_detect) > 0:
        del _global_lang_detect[0]


def decide_language_by_prob(predictions: Tuple[str], probabilities: Tuple[float]) -> str:
    """
    Decides the final language based on the probabilities of the predicted languages.

    Args:
        predictions (Tuple[str]): The predicted languages.
        probabilities (Tuple[float]): The probabilities of the predicted languages.

    Returns:
        str: The final language decided based on the probabilities.
    """
    lang_prob_dict = {}
    for lang_key, lang_prob in zip(predictions, probabilities):
        lang = lang_key.replace("__label__", "")
        lang_prob_dict[lang] = lang_prob

    zh_prob = lang_prob_dict.get("zh", 0)
    en_prob = lang_prob_dict.get("en", 0)
    zh_en_prob = zh_prob + en_prob
    if zh_en_prob > 0.5:
        if zh_prob > 0.4 * zh_en_prob:
            final_lang = "zh"
        else:
            final_lang = "en"
    else:
        if max(lang_prob_dict.values()) > 0.6:
            final_lang = max(lang_prob_dict, key=lang_prob_dict.get)
            if final_lang == "hr":
                final_lang = "sr"
        elif max(lang_prob_dict.values()) > 0 and max(lang_prob_dict, key=lang_prob_dict.get) in ["sr", "hr"]:
            final_lang = "sr"
        else:
            final_lang = "mix"
    return final_lang


def decide_language_func(content_str: str, lang_detect: LanguageIdentification) -> str:
    """
    Decides the language of the given content string using the language detection instance.

    Args:
        content_str (str): The content string for which the language needs to be decided.
        lang_detect (LanguageIdentification): The language detection instance.

    Returns:
        str: The final language decided for the given content string.
    """
    str_len = len(content_str)
    if str_len > 10000:
        start_idx = (str_len - 10000) // 2
        content_str = content_str[start_idx: start_idx + 10000]

    if len(content_str) == 0:
        return "empty"
    predictions, probabilities = lang_detect.predict(content_str)
    return decide_language_by_prob(predictions, probabilities)


def decide_language_by_str(content_str: str) -> str:
    """
    Decides the language of the given content string using the language detection instance.

    Args:
        content_str (str): The content string for which the language needs to be decided.

    Returns:
        str: The final language decided for the given content string.
    """
    return decide_language_func(content_str, get_lang_detect())


def update_language_by_str(content_str: str) -> Dict[str, Any]:
    """
    Updates the language of the given content string.

    Args:
        content_str (str): The content string for which the language needs to be updated.

    Returns:
        Dict[str, Any]: A dictionary containing the updated language.
    """
    return {"language": decide_language_by_str(content_str)}


if __name__ == '__main__':
    content = "你好，我很高兴见到你！"
    language = decide_language_by_str(content)
    print(language)
    content = "Hello, nice to meet you."
    language = decide_language_by_str(content)
    print(language)

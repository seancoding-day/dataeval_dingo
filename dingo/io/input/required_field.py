from enum import Enum


class RequiredField(Enum):
    CONTENT = "content"
    PROMPT = "prompt"
    CONTEXT = "context"
    IMAGE = "image"
    METADATA = "metadata"
    TYPE = "type"
    DT = "dt"
    SOURCE = "source"
    ANNOTATION = "annotation"

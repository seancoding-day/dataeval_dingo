"""Run LLMPerspective against the Google Perspective API.

Before running this example:

    pip install google-api-python-client
    export PERSPECTIVE_API_KEY="your-google-api-key"
    python examples/security/sdk_perspective.py
"""

import os

from dingo.config.input_args import EvaluatorLLMArgs
from dingo.io.input import Data
from dingo.model.llm.llm_perspective import LLMPerspective


def main() -> None:
    api_key = os.getenv("PERSPECTIVE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit(
            "Please set PERSPECTIVE_API_KEY (or GOOGLE_API_KEY) before running this example."
        )

    LLMPerspective.dynamic_config = EvaluatorLLMArgs(
        key=api_key,
        api_url=os.getenv(
            "PERSPECTIVE_API_URL",
            "https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
        ),
    )
    LLMPerspective.client = None

    samples = [
        Data(data_id="perspective-good", content="Thank you for your thoughtful answer."),
        Data(data_id="perspective-toxic", content="You are stupid and I hate you."),
    ]

    for sample in samples:
        result = LLMPerspective.eval(sample)
        print(f"data_id: {sample.data_id}")
        print(f"content: {sample.content}")
        print(f"status: {result.status}  # True means a quality issue was detected")
        print(f"label: {result.label}")
        print(f"reason: {result.reason}")
        print()


if __name__ == "__main__":
    main()

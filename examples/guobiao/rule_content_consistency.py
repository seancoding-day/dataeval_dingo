"""Evaluate string fields using the national-standard content-consistency rule.

Optional dependencies:
    conda run -n dingo pip install "dingo-python[hhem]"

The first run downloads the configured Hugging Face model unless it is already
available locally.
"""

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io import Data
from dingo.model.rule.guobiao.rule_tc609_quality import Rule_TC609_0206_ContentConsistency


def main():
    data = Data(
        data_id="guobiao-content-consistency-example",
        title="高血压患者的日常健康管理",
        content="高血压患者应遵医嘱规律用药，并定期监测血压。",
        summary="高血压患者需要规律服药和监测血压。",
    )

    Rule_TC609_0206_ContentConsistency.dynamic_config = EvaluatorRuleArgs(
        key_list=["title", "content", "summary"],
        threshold=0.5,
        model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        device=-1,
    )
    result = Rule_TC609_0206_ContentConsistency.eval(data)
    print(result)


if __name__ == "__main__":
    main()

"""Evaluate one Chinese text using the national-standard type-consistency rule.

Optional dependencies:
    conda run -n dingo pip install "dingo-python[hhem]"

The first run downloads the configured Hugging Face model unless it is already
available locally.
"""

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io import Data
from dingo.model.rule.rule_guobiao import RuleDataTypeConsistency


def main():
    data = Data(
        data_id="guobiao-type-example",
        type="医疗",
        content="高血压患者应在医生指导下规律用药，并定期监测血压变化。",
    )

    RuleDataTypeConsistency.dynamic_config = EvaluatorRuleArgs(
        threshold=0.5,
        model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        device=-1,
    )
    result = RuleDataTypeConsistency.eval(data)
    print(result)


if __name__ == "__main__":
    main()

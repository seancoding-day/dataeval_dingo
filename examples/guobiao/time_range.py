"""Evaluate one sample using the guobiao data-time-range rule."""

from dingo.config.input_args import EvaluatorRuleArgs
from dingo.io import Data
from dingo.model.rule.rule_guobiao import RuleDataTimeRange


def main():
    data = Data(
        data_id="guobiao-time-range-example",
        dt="2025-03-01 10:30:00",
        content="示例数据",
    )

    RuleDataTimeRange.dynamic_config = EvaluatorRuleArgs(
        dt_start="2025-01-01",
        dt_end="2025-12-31 23:59:59",
    )
    result = RuleDataTimeRange.eval(data)
    print(result)


if __name__ == "__main__":
    main()

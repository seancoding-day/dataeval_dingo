from dingo.io.input import Data
from dingo.io.output.eval_detail import QualityLabel
from dingo.model.llm.agent_eval.llm_agent_task_completion import LLMAgentTaskCompletion


def _always_raise(cls, messages):
    raise ConnectionError("boom")


def test_retry_exhaustion_is_not_faked_as_issue(monkeypatch):
    monkeypatch.setattr(LLMAgentTaskCompletion, "send_messages", classmethod(_always_raise))
    monkeypatch.setattr(LLMAgentTaskCompletion, "create_client", classmethod(lambda cls: None))
    monkeypatch.setattr(LLMAgentTaskCompletion, "client", object())

    res = LLMAgentTaskCompletion.eval(Data(data_id="t", prompt="p", content="c"))

    # 基础设施错误绝不能伪装成阻塞性 finding（spec §9.3）
    assert res.status is False
    assert res.label is not None
    assert res.label[0].startswith(QualityLabel.REVIEW_EXECUTION_ERROR_PREFIX)
    assert "boom" in res.reason[0]
    assert res.score is None

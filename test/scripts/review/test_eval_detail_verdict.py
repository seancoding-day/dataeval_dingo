from dingo.io.output.eval_detail import EvalDetail


def test_new_fields_default_backward_compatible():
    d = EvalDetail(metric="X")  # 旧评估器只填 metric/status
    assert d.verdict is None
    assert d.applicable is True
    assert d.rule_id is None
    assert d.rubric_version is None


def test_effective_verdict_derives_from_status_when_unset():
    passed = EvalDetail(metric="X", status=False)
    failed = EvalDetail(metric="X", status=True)
    assert passed.effective_verdict == "pass"
    assert failed.effective_verdict == "issue"


def test_effective_verdict_prefers_native_verdict():
    d = EvalDetail(metric="X", status=False, verdict="warning")
    assert d.effective_verdict == "warning"


def test_effective_verdict_na_when_not_applicable():
    d = EvalDetail(metric="X", status=False, applicable=False)
    assert d.effective_verdict == "n/a"

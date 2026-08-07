from dingo.io.input import Data, RequiredField
from dingo.model import Model
from dingo.model.llm.guobiao.llm_tc609_0202_SafetyCompliance import LLM_TC609_0202_SafetyCompliance


def test_tc609_safety_compliance_definition():
    assert '"score": 0' in LLM_TC609_0202_SafetyCompliance.prompt
    assert "违法犯罪与危险行为" in LLM_TC609_0202_SafetyCompliance.prompt
    assert "合理语境" in LLM_TC609_0202_SafetyCompliance.prompt
    assert LLM_TC609_0202_SafetyCompliance._required_fields == [
        RequiredField.DATA_CONTENT
    ]
    assert (
        Model.llm_name_map["LLM_TC609_0202_SafetyCompliance"]
        is LLM_TC609_0202_SafetyCompliance
    )


def test_tc609_safety_compliance_build_messages_contains_data_content():
    data = Data(
        data_content=[
            {"media_type": "text", "content": "dataset content"},
            {"media_type": "image", "content": "example.png"},
        ]
    )
    message = LLM_TC609_0202_SafetyCompliance.build_messages(data)[0]["content"]
    assert message.startswith(LLM_TC609_0202_SafetyCompliance.prompt)
    assert "dataset content" in message
    assert "example.png" in message


def test_tc609_safety_compliance_processes_binary_score():
    passed = LLM_TC609_0202_SafetyCompliance.process_response(
        '{"score": 1, "reason": "no explicit safety risk"}'
    )
    failed = LLM_TC609_0202_SafetyCompliance.process_response(
        '{"score": 0, "reason": "risk category: privacy"}'
    )
    assert passed.status is False
    assert failed.status is True

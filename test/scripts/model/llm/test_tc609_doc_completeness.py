from dingo.io.input import Data
from dingo.model.llm.guobiao.llm_tc609_0101_doc_basic_info_completeness import LLM_TC609_0101_DocBasicInfoCompleteness
from dingo.model.llm.guobiao.llm_tc609_0102_doc_content_feature_completeness import LLM_TC609_0102_DocContentFeatureCompleteness
from dingo.model.llm.guobiao.llm_tc609_0103_doc_construction_process_completeness import LLM_TC609_0103_DocConstructionProcessCompleteness
from dingo.model.llm.guobiao.llm_tc609_0104_doc_application_completeness import LLM_TC609_0104_DocApplicationCompleteness

TC609_LLM_CLASSES = [
    LLM_TC609_0101_DocBasicInfoCompleteness,
    LLM_TC609_0102_DocContentFeatureCompleteness,
    LLM_TC609_0103_DocConstructionProcessCompleteness,
    LLM_TC609_0104_DocApplicationCompleteness,
]


def test_tc609_doc_llm_prompts_define_binary_json_output():
    for evaluator in TC609_LLM_CLASSES:
        assert '"score": 0' in evaluator.prompt
        assert "至少4项" in evaluator.prompt
        assert "同义词、近义表达" in evaluator.prompt
        assert evaluator._required_fields


def test_tc609_doc_llm_build_messages_contains_document():
    document = "这是一份数据集说明文档。"
    for evaluator in TC609_LLM_CLASSES:
        messages = evaluator.build_messages(Data(content=document))
        assert messages == [
            {"role": "user", "content": evaluator.prompt + document}
        ]


def test_tc609_doc_llm_process_response_pass_and_fail():
    evaluator = LLM_TC609_0101_DocBasicInfoCompleteness

    passed = evaluator.process_response(
        '{"score": 1, "reason": "covered: 5项; missing: 无"}'
    )
    assert passed.status is False
    assert passed.reason == ["covered: 5项; missing: 无"]

    failed = evaluator.process_response(
        '{"score": 0, "reason": "covered: 3项; missing: 访问渠道、技术支持"}'
    )
    assert failed.status is True
    assert failed.reason == [
        "covered: 3项; missing: 访问渠道、技术支持"
    ]

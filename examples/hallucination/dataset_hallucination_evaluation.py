"""
Dataset Hallucination Evaluation Example

This example demonstrates how to use Dingo's hallucination detection capability
for batch evaluation of datasets, particularly useful for:
- RAG system evaluation
- LLM response validation
- SFT data quality assessment
"""

from dingo.config import InputArgs
from dingo.exec import Executor
# Force import hallucination detection modules
from dingo.model.llm.llm_hallucination import LLMHallucination
from dingo.model.prompt.prompt_hallucination import PromptHallucination
from dingo.model.rule.rule_hallucination_hhem import RuleHallucinationHHEM


def evaluate_hallucination_jsonl_dataset():
    """
    Example 1: Evaluate a JSONL dataset for hallucinations
    Expected JSONL format:
    {"data_id": "1", "prompt": "question", "content": "response", "context": ["context1", "context2"]}
    """
    print("=== Example 1: JSONL Dataset Evaluation ===")

    input_data = {
        "input_path": "test/data/hallucination_test.jsonl",  # Your JSONL file path
        "output_path": "output/hallucination_evaluation/",
        "dataset": {
            "source": "local",
            "format": "jsonl",
            "field": {
                "prompt": "prompt",
                "content": "content",
                "context": "context",
            }
        },
        "executor": {
            "prompt_list": ["PromptHallucination"],
            "result_save": {
                "bad": True
            }
        },
        "evaluator": {
            "llm_config": {
                "LLMHallucination": {
                    "model": "deepseek-chat",
                    "key": "YOUR_API_KEY",
                    "api_url": "https://api.deepseek.com"
                }
            }
        }
    }

    input_args = InputArgs(**input_data)
    executor = Executor.exec_map["local"](input_args)
    result = executor.execute()

    print(result)
    print(f"Evaluation completed successfully!")
    print(f"Total processed: {result.total}")
    print(f"Hallucinations detected: {result.num_bad}")
    print(f"Clean responses: {result.num_good}")
    print(f"Overall score: {result.score}%")
    print(f"Type distribution: {result.type_ratio}")
    print(f"Name distribution: {result.name_ratio}")
    print()


# def evaluate_rag_responses():
#     """
#     Example 2: Evaluate RAG system responses
#     """
#     print("=== Example 2: RAG System Evaluation ===")

#     input_data = {
#         "input_path": "test_data/rag_responses.jsonl",
#         "data_format": "jsonl",
#         "dataset": "local",
#         "column_content": "generated_response",  # The LLM generated response
#         "column_prompt": "user_question",       # The user's question
#         "column_context": "retrieved_contexts", # The retrieved contexts
#         "custom_config": {
#             "prompt_list": ["PromptHallucination"],  # Use hallucination detection prompt
#             "llm_config": {
#                 "LLMHallucination": {
#                     "model": "gpt-4o-mini",  # Use cheaper model for batch processing
#                     "key": "YOUR_API_KEY",
#                     "api_url": "https://api.openai.com/v1/chat/completions",
#                     "threshold": 0.3  # Lower threshold for more sensitive detection
#                 }
#             }
#         },
#         "max_workers": 5,  # Process 5 items in parallel
#         "batch_size": 50,
#         "save_data": True,
#         "output_path": "output/rag_hallucination_check/"
#     }

#     input_args = InputArgs(**input_data)
#     executor = Executor.exec_map["local"](input_args)
#     result = executor.execute()

#     print(f"RAG evaluation completed!")
#     print(f"Hallucination rate: {result.bad_count / result.total_count:.2%}")
#     print()


# def evaluate_sft_dataset_with_references():
#     """
#     Example 3: Evaluate SFT dataset with reference contexts
#     """
#     print("=== Example 3: SFT Dataset with References ===")

#     input_data = {
#         "input_path": "your_sft_dataset.jsonl",
#         "data_format": "jsonl",
#         "dataset": "local",
#         "column_content": "response",
#         "column_prompt": "instruction",
#         "column_context": "reference_docs",  # Reference documents for fact-checking
#         "eval_group": "sft",  # Use comprehensive SFT evaluation group
#         "custom_config": {
#             # Include multiple evaluations
#             "prompt_list": [
#                 "QUALITY_BAD_HALLUCINATION",
#                 "QUALITY_HELPFUL",
#                 "QUALITY_HARMLESS"
#             ],
#             "llm_config": {
#                 "LLMHallucination": {
#                     "model": "gpt-4o",
#                     "key": "YOUR_API_KEY",
#                     "api_url": "https://api.openai.com/v1/chat/completions"
#                 },
#                 "LLMText3HHelpful": {
#                     "model": "gpt-4o",
#                     "key": "YOUR_API_KEY",
#                     "api_url": "https://api.openai.com/v1/chat/completions"
#                 }
#             }
#         },
#         "save_data": True,
#         "save_correct": True,  # Also save data that passes all checks
#         "output_path": "output/sft_comprehensive_evaluation/"
#     }

#     input_args = InputArgs(**input_data)
#     executor = Executor.exec_map["local"](input_args)
#     result = executor.execute()

#     print(f"SFT dataset evaluation completed!")
#     print(f"Quality metrics summary: {result.summary}")
#     print()


def create_sample_test_data():
    """
    Helper function to create sample test data for demonstration
    """
    import json
    import os

    # Create test directory
    os.makedirs("test_data", exist_ok=True)

    # Sample hallucination test data
    hallucination_samples = [
        {
            "data_id": "1",
            "prompt": "When did Einstein win the Nobel Prize?",
            "content": "Einstein won the Nobel Prize in 1969 for his discovery of the photoelectric effect.",
            "context": ["Einstein won the Nobel Prize in 1921.", "The prize was for his work on the photoelectric effect."]
        },
        {
            "data_id": "2",
            "prompt": "What is the capital of Japan?",
            "content": "The capital of Japan is Tokyo, which is located on the eastern coast of Honshu island.",
            "context": ["Tokyo is the capital of Japan.", "Tokyo is located on Honshu island."]
        },
        {
            "data_id": "3",
            "prompt": "How many continents are there?",
            "content": "There are 8 continents in the world including Asia, Europe, North America, South America, Africa, Australia, Antarctica, and Atlantis.",
            "context": ["There are 7 continents.", "The continents are Asia, Europe, North America, South America, Africa, Australia, and Antarctica."]
        }
    ]

    # Write to JSONL file
    with open("test/data/hallucination_test.jsonl", "w", encoding="utf-8") as f:
        for sample in hallucination_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print("✅ Sample test data created in test_data/hallucination_test.jsonl")


if __name__ == "__main__":
    print("📊 Dingo Dataset Hallucination Evaluation Examples")
    print("=" * 60)
    print()

    # Create sample data first
    # create_sample_test_data()  # Commented out - using pre-built test data
    print()

    print("⚠️  Configuration Notes:")
    print("1. Set your OpenAI API key in the custom_config")
    print("2. Adjust file paths to your actual data")
    print("3. Modify column names to match your data format")
    print("4. Tune threshold values based on your requirements")
    print()

    # Run examples (comment out if you don't have actual data)
    evaluate_hallucination_jsonl_dataset()
    # evaluate_rag_responses()
    # evaluate_sft_dataset_with_references()

    print("💡 Usage Tips:")
    print("- Use lower thresholds (0.2-0.3) for sensitive hallucination detection")
    print("- Use higher thresholds (0.6-0.8) for more permissive evaluation")
    print("- Combine with other quality metrics for comprehensive assessment")
    print("- Use parallel processing (max_workers) for large datasets")
    print("- Check output files for detailed per-item analysis")

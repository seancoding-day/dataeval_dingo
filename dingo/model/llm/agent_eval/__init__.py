"""
Agent Trace Evaluation metrics (LLMAgent* series).

These evaluators assess agent trace quality using LLM-as-Judge methodology.
They are distinct from the agent/ directory which contains agent-framework-based
evaluators (AgentFactCheck, AgentHallucination) that USE agent frameworks to DO evaluation.

Evaluators in this package EVALUATE agent traces — task completion, plan quality,
tool correctness, error recovery, etc.
"""

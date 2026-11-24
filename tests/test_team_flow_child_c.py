"""
Test suite for team-flow-e2e Child C: Pipeline Processor.

This module contains comprehensive tests for the Pipeline, Step, and related
utility functions in team_flow_e2e.child_c.

Tests cover:
- Normal pipeline execution with multiple steps
- Edge cases: empty pipeline, None input handling, error propagation
- Optional vs required step behavior
- Context-aware execution
- Validation pipeline factory
- Transformation pipeline factory
"""

import pytest
from typing import Any, Optional

from team_flow_e2e.child_c import (
    Pipeline,
    Step,
    StepResult,
    PipelineResult,
    create_validation_pipeline,
    create_data_transformation_pipeline,
)


# ==================== Step Tests ====================

class TestStep:
    """Tests for the Step class."""

    def test_step_success(self):
        """Test successful step execution."""
        step = Step(name="double", func=lambda x: x * 2)
        result = step.execute(5)
        assert result.success is True
        assert result.data == 10
        assert result.step_name == "double"
        assert result.error is None

    def test_step_failure(self):
        """Test step failure handling."""
        step = Step(name="fail", func=lambda x: 1 / 0)
        result = step.execute(5)
        assert result.success is False
        assert result.data is None
        assert result.error is not None
        assert "ZeroDivisionError" in result.error
        assert result.step_name == "fail"

    def test_step_skip_on_none(self):
        """Test step skipping when input is None and skip_on_none=True."""
        step = Step(name="process", func=lambda x: x.upper(), skip_on_none=True)
        result = step.execute(None)
        assert result.success is True
        assert result.data is None
        assert result.metadata.get("skipped") is True

    def test_step_no_skip_on_none(self):
        """Test step execution when input is None and skip_on_none=False."""
        step = Step(name="process", func=lambda x: x.upper(), skip_on_none=False)
        result = step.execute(None)
        assert result.success is False
        assert "AttributeError" in result.error or "TypeError" in result.error

    def test_step_required_flag(self):
        """Test that required flag doesn't affect step execution directly."""
        step = Step(name="test", func=lambda x: x + 1, required=True)
        result = step.execute(1)
        assert result.success is True
        assert result.data == 2


# ==================== Pipeline Tests ====================

class TestPipeline:
    """Tests for the Pipeline class."""

    def test_empty_pipeline(self):
        """Test execution of an empty pipeline."""
        pipeline = Pipeline[str](name="empty")
        result = pipeline.execute("input")
        assert result.success is True
        assert result.data == "input"
        assert result.executed_steps == 0
        assert result.skipped_steps == 0
        assert len(result.step_results) == 0

    def test_single_step_pipeline(self):
        """Test pipeline with a single transformation step."""
        pipeline = Pipeline[int](name="single")
        pipeline.add_function("increment", lambda x: x + 1)
        result = pipeline.execute(5)
        assert result.success is True
        assert result.data == 6
        assert result.executed_steps == 1

    def test_multi_step_pipeline_normal(self):
        """Test normal multi-step pipeline execution."""
        pipeline = Pipeline[str](name="normal")
        pipeline.add_function("trim", lambda s: s.strip())
        pipeline.add_function("uppercase", lambda s: s.upper())
        pipeline.add_function("add_prefix", lambda s: f"RESULT: {s}")
        result = pipeline.execute("  hello world  ")
        assert result.success is True
        assert result.data == "RESULT: HELLO WORLD"
        assert result.executed_steps == 3

    def test_pipeline_with_type_transformation(self):
        """Test pipeline that transforms data types between steps."""
        pipeline = Pipeline[Any](name="type_transform")
        pipeline.add_function("to_str", lambda x: str(x))
        pipeline.add_function("to_len", lambda s: len(s))
        pipeline.add_function("double", lambda n: n * 2)
        result = pipeline.execute(12345)
        assert result.success is True
        assert result.data == 10  # len("12345") * 2 = 5 * 2 = 10

    def test_pipeline_error_stops_execution(self):
        """Test that error in required step stops pipeline."""
        pipeline = Pipeline[int](name="error_stop")
        pipeline.add_function("step1", lambda x: x + 1)
        pipeline.add_function("fail", lambda x: 1 / 0)  # Will raise ZeroDivisionError
        pipeline.add_function("step3", lambda x: x * 2)  # Should not execute
        result = pipeline.execute(5)
        assert result.success is False
        assert result.error is not None
        assert "ZeroDivisionError" in result.error
        assert result.executed_steps == 2  # step1 and fail
        assert result.data is None

    def test_pipeline_optional_step_failure_continues(self):
        """Test that optional step failure doesn't stop pipeline."""
        pipeline = Pipeline[int](name="optional_fail")
        pipeline.add_function("step1", lambda x: x + 1)
        pipeline.add_function("optional_fail", lambda x: 1 / 0, required=False)
        pipeline.add_function("step3", lambda x: x * 2 if x is not None else 0)
        result = pipeline.execute(5)
        assert result.success is True
        assert result.data == 0  # step3 receives None, returns 0
        assert result.executed_steps == 3

    def test_pipeline_skip_on_none(self):
        """Test pipeline with skip_on_none steps."""
        pipeline = Pipeline[Optional[str]](name="skip_none")
        pipeline.add_function("maybe_none", lambda x: None if x < 0 else str(x))
        pipeline.add_function("process", lambda s: s.upper(), skip_on_none=True)
        pipeline.add_function("final", lambda s: f"[{s}]" if s else "EMPTY")
        # Test with positive input (not None)
        result = pipeline.execute(5)
        assert result.success is True
        assert result.data == "[5]"
        # Test with negative input (produces None)
        result = pipeline.execute(-1)
        assert result.success is True
        assert result.data == "EMPTY"
        assert result.skipped_steps == 1

    def test_pipeline_duplicate_step_name_raises(self):
        """Test that adding duplicate step names raises ValueError."""
        pipeline = Pipeline[int](name="dup")
        pipeline.add_function("step1", lambda x: x + 1)
        with pytest.raises(ValueError, match="already exists"):
            pipeline.add_function("step1", lambda x: x * 2)

    def test_pipeline_len_and_repr(self):
        """Test pipeline length and string representation."""
        pipeline = Pipeline[str](name="test_pipe")
        pipeline.add_function("a", lambda x: x)
        pipeline.add_function("b", lambda x: x)
        assert len(pipeline) == 2
        assert pipeline.get_step_names() == ["a", "b"]
        repr_str = repr(pipeline)
        assert "test_pipe" in repr_str
        assert "a -> b" in repr_str


# ==================== PipelineResult Tests ====================

class TestPipelineResult:
    """Tests for the PipelineResult dataclass."""

    def test_successful_result_properties(self):
        """Test properties of a successful pipeline result."""
        step_results = [
            StepResult.ok("data1", "step1"),
            StepResult.ok("data2", "step2"),
        ]
        result = PipelineResult(
            success=True,
            data="final",
            step_results=step_results,
            executed_steps=2,
            skipped_steps=0,
        )
        assert result.success is True
        assert result.data == "final"
        assert len(result.all_results) == 2
        assert result.error is None

    def test_failed_result_properties(self):
        """Test properties of a failed pipeline result."""
        step_results = [
            StepResult.ok("data1", "step1"),
            StepResult.fail("error msg", "step2"),
        ]
        result = PipelineResult(
            success=False,
            data=None,
            step_results=step_results,
            error="error msg",
            executed_steps=2,
            skipped_steps=0,
        )
        assert result.success is False
        assert result.data is None
        assert result.error == "error msg"


# ==================== StepResult Tests ====================

class TestStepResult:
    """Tests for the StepResult dataclass."""

    def test_ok_factory(self):
        """Test StepResult.ok factory method."""
        result = StepResult.ok("test_data", "my_step", extra="meta")
        assert result.success is True
        assert result.data == "test_data"
        assert result.step_name == "my_step"
        assert result.metadata["extra"] == "meta"

    def test_fail_factory(self):
        """Test StepResult.fail factory method."""
        result = StepResult.fail("something went wrong", "bad_step", code=500)
        assert result.success is False
        assert result.error == "something went wrong"
        assert result.step_name == "bad_step"
        assert result.metadata["code"] == 500


# ==================== Context Execution Tests ====================

class TestPipelineWithContext:
    """Tests for context-aware pipeline execution."""

    def test_execute_with_context_passed_to_steps(self):
        """Test that context is passed to steps that accept it."""
        pipeline = Pipeline[str](name="context_test")
        captured_context = {}

        def step_with_context(data: str, context: dict) -> str:
            captured_context.update(context)
            return data + context.get("suffix", "")

        pipeline.add_step(Step(name="with_context", func=step_with_context))
        result = pipeline.execute_with_context("hello", {"suffix": "_world"})
        assert result.success is True
        assert result.data == "hello_world"
        assert captured_context.get("suffix") == "_world"

    def test_execute_with_context_ignored_for_single_arg(self):
        """Test that context is not passed to single-argument functions."""
        pipeline = Pipeline[str](name="no_context")
        pipeline.add_function("no_context", lambda s: s.upper())
        result = pipeline.execute_with_context("hello", {"ignored": True})
        assert result.success is True
        assert result.data == "HELLO"

    def test_mixed_context_and_simple_steps(self):
        """Test pipeline with mix of context-aware and simple steps."""
        pipeline = Pipeline[str](name="mixed")
        pipeline.add_function("simple", lambda s: s.strip())
        pipeline.add_step(Step(
            name="with_context",
            func=lambda s, ctx: s + ctx.get("tag", "")
        ))
        pipeline.add_function("final", lambda s: f"[{s}]")
        result = pipeline.execute_with_context("  test  ", {"tag": "_tagged"})
        assert result.success is True
        assert result.data == "[test_tagged]"


# ==================== Factory Function Tests ====================

class TestValidationPipelineFactory:
    """Tests for create_validation_pipeline factory."""

    def test_validation_pipeline_success(self):
        """Test validation pipeline with valid input."""
        pipeline = create_validation_pipeline(
            required_fields=["name", "age"],
            field_types={"age": int, "name": str},
        )
        result = pipeline.execute({"name": "Alice", "age": 30})
        assert result.success is True
        assert result.data == {"name": "Alice", "age": 30}

    def test_validation_pipeline_missing_field(self):
        """Test validation pipeline with missing required field."""
        pipeline = create_validation_pipeline(
            required_fields=["name", "age"],
            field_types={"age": int},
        )
        result = pipeline.execute({"name": "Alice"})
        assert result.success is False
        assert "Missing required fields" in result.error
        assert "age" in result.error

    def test_validation_pipeline_wrong_type(self):
        """Test validation pipeline with incorrect field type."""
        pipeline = create_validation_pipeline(
            required_fields=["age"],
            field_types={"age": int},
        )
        result = pipeline.execute({"age": "thirty"})
        assert result.success is False
        assert "must be int" in result.error

    def test_validation_pipeline_no_type_checking(self):
        """Test validation pipeline without type checking."""
        pipeline = create_validation_pipeline(required_fields=["name"])
        result = pipeline.execute({"name": "Alice", "extra": 123})
        assert result.success is True
        assert result.data["extra"] == 123


class TestTransformationPipelineFactory:
    """Tests for create_data_transformation_pipeline factory."""

    def test_transformation_pipeline(self):
        """Test transformation pipeline factory."""
        pipeline = create_data_transformation_pipeline([
            ("add_one", lambda x: x + 1),
            ("double", lambda x: x * 2),
            ("to_str", lambda x: f"result_{x}"),
        ])
        result = pipeline.execute(5)
        assert result.success is True
        assert result.data == "result_12"  # (5+1)*2 = 12

    def test_empty_transformation_pipeline(self):
        """Test transformation pipeline with no transformations."""
        pipeline = create_data_transformation_pipeline([])
        result = pipeline.execute("input")
        assert result.success is True
        assert result.data == "input"


# ==================== Edge Case Tests ====================

class TestEdgeCases:
    """Edge case tests for the pipeline processor."""

    def test_pipeline_with_none_initial_data(self):
        """Test pipeline execution with None as initial data."""
        pipeline = Pipeline[Optional[str]](name="none_input")
        pipeline.add_function("handle_none", lambda x: "was_none" if x is None else x)
        pipeline.add_function("uppercase", lambda s: s.upper())
        result = pipeline.execute(None)
        assert result.success is True
        assert result.data == "WAS_NONE"

    def test_pipeline_with_complex_data_structure(self):
        """Test pipeline processing complex nested data structures."""
        pipeline = Pipeline[dict](name="complex_data")
        pipeline.add_function("add_timestamp", lambda d: {**d, "ts": 12345})
        pipeline.add_function("extract_keys", lambda d: list(d.keys()))
        pipeline.add_function("count_keys", lambda keys: len(keys))
        result = pipeline.execute({"a": 1, "b": 2})
        assert result.success is True
        assert result.data == 3  # a, b, ts

    def test_pipeline_step_modifies_shared_object(self):
        """Test that steps modifying mutable objects affect subsequent steps."""
        pipeline = Pipeline[list](name="mutable")
        pipeline.add_function("append", lambda lst: lst + [1])
        pipeline.add_function("append2", lambda lst: lst + [2])
        pipeline.add_function("sum", lambda lst: sum(lst))
        # Each step gets a new list due to + operator
        result = pipeline.execute([10])
        assert result.success is True
        assert result.data == 13  # 10 + 1 + 2

    def test_pipeline_with_exception_in_optional_step_then_required(self):
        """Test optional step fails, then required step receives None."""
        pipeline = Pipeline[str](name="opt_then_req")
        pipeline.add_function("opt_fail", lambda x: 1/0, required=False)
        pipeline.add_function("req_after_none", lambda x: x.upper() if x else "DEFAULT", required=True)
        result = pipeline.execute("hello")
        assert result.success is True
        assert result.data == "DEFAULT"

    def test_pipeline_step_result_metadata_preserved(self):
        """Test that step metadata is preserved in results."""
        def step_with_meta(x):
            return x * 2
        step = Step(name="meta_step", func=step_with_meta)
        result = step.execute(5)
        assert result.metadata == {}
        # Pipeline should preserve step results
        pipeline = Pipeline[int](name="meta_pipe")
        pipeline.add_step(step)
        pipe_result = pipeline.execute(5)
        assert pipe_result.step_results[0].step_name == "meta_step"

    def test_deeply_nested_pipeline_execution(self):
        """Test pipeline with many steps."""
        pipeline = Pipeline[int](name="deep")
        for i in range(10):
            pipeline.add_function(f"step_{i}", lambda x, i=i: x + i)
        result = pipeline.execute(0)
        assert result.success is True
        assert result.data == sum(range(10))  # 0+1+2+...+9 = 45
        assert result.executed_steps == 10


# ==================== Integration-style Tests ====================

class TestIntegrationScenarios:
    """Integration-style tests simulating realistic workflow scenarios."""

    def test_data_cleaning_pipeline(self):
        """Test a realistic data cleaning workflow."""
        pipeline = Pipeline[str](name="clean_data")
        pipeline.add_function("strip", lambda s: s.strip())
        pipeline.add_function("lower", lambda s: s.lower())
        pipeline.add_function("remove_special", lambda s: "".join(c for c in s if c.isalnum() or c.isspace()))
        pipeline.add_function("collapse_spaces", lambda s: " ".join(s.split()))
        result = pipeline.execute("  HeLLo!!!   WoRLD@@@  ")
        assert result.success is True
        assert result.data == "hello world"

    def test_json_processing_pipeline(self):
        """Test a JSON-like data processing workflow."""
        import json
        pipeline = Pipeline[str](name="json_process")
        pipeline.add_function("parse", lambda s: json.loads(s))
        pipeline.add_function("extract_names", lambda d: [item["name"] for item in d["items"]])
        pipeline.add_function("sort", lambda lst: sorted(lst))
        pipeline.add_function("join", lambda lst: ", ".join(lst))
        input_json = '{"items": [{"name": "Charlie"}, {"name": "Alice"}, {"name": "Bob"}]}'
        result = pipeline.execute(input_json)
        assert result.success is True
        assert result.data == "Alice, Bob, Charlie"

    def test_conditional_processing_pipeline(self):
        """Test pipeline with conditional logic based on data content."""
        pipeline = Pipeline[dict](name="conditional")
        pipeline.add_function("check_type", lambda d: d.get("type"))
        # Steps pass through existing result if already set, otherwise process
        pipeline.add_function(
            "process_a",
            lambda t: {"result": "processed_a"} if t == "A" else t,
            required=False,
        )
        pipeline.add_function(
            "process_b",
            lambda t: {"result": "processed_b"} if t == "B" else t,
            required=False,
        )
        pipeline.add_function(
            "default",
            lambda x: {"result": "default"} if isinstance(x, str) else x,
        )
        # Test type A
        result = pipeline.execute({"type": "A"})
        assert result.success is True
        assert result.data == {"result": "processed_a"}
        # Test type B
        result = pipeline.execute({"type": "B"})
        assert result.success is True
        assert result.data == {"result": "processed_b"}
        # Test unknown type
        result = pipeline.execute({"type": "C"})
        assert result.success is True
        assert result.data == {"result": "default"}

    def test_pipeline_with_accumulator_pattern(self):
        """Test pipeline using accumulator pattern via context."""
        pipeline = Pipeline[int](name="accumulator")
        def step1(x, ctx): ctx["acc"] = x; return x
        def step2(x, ctx): ctx["acc"] += x * 2; return x * 2
        def step3(x, ctx): ctx["acc"] += x * 3; return x * 3
        def final(x, ctx): return ctx["acc"]
        pipeline.add_step(Step("s1", step1))
        pipeline.add_step(Step("s2", step2))
        pipeline.add_step(Step("s3", step3))
        pipeline.add_step(Step("final", final))
        result = pipeline.execute_with_context(10, {})
        assert result.success is True
        # acc = 10 (step1) + 20 (step2: 10*2) + 60 (step3: 20*3) = 90
        assert result.data == 90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
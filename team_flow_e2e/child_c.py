"""
Child C: Workflow Pipeline Processor

This module provides a flexible pipeline processor for executing sequential
data transformation steps. It supports conditional execution, error handling,
and result aggregation for team-based workflow scenarios.

The processor is designed for "team-flow-e2e" integration tests where multiple
processing stages need to be coordinated with type safety and clear contracts.

Example:
    >>> from team_flow_e2e.child_c import Pipeline, Step
    >>> pipeline = Pipeline()
    >>> pipeline.add_step(Step("normalize", lambda x: x.strip().lower()))
    >>> pipeline.add_step(Step("validate", lambda x: x if len(x) > 0 else None))
    >>> result = pipeline.execute("  Hello World  ")
    >>> print(result.success, result.data)
    True hello world
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class StepResult(Generic[T]):
    """
    Represents the result of a single pipeline step execution.

    Attributes:
        success: Whether the step completed successfully.
        data: The output data from the step (if successful).
        error: Error message if the step failed.
        step_name: Name of the step that produced this result.
        metadata: Additional metadata about the step execution.
    """
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    step_name: str = ""
    metadata: dict = field(default_factory=dict)

    @classmethod
    def ok(cls, data: T, step_name: str = "", **metadata) -> "StepResult[T]":
        """Create a successful step result."""
        return cls(success=True, data=data, step_name=step_name, metadata=metadata)

    @classmethod
    def fail(cls, error: str, step_name: str = "", **metadata) -> "StepResult[T]":
        """Create a failed step result."""
        return cls(success=False, error=error, step_name=step_name, metadata=metadata)


@dataclass
class Step(Generic[T, U]):
    """
    A single processing step in a pipeline.

    Each step has a name, a transformation function, and optional configuration
    for error handling and conditional execution.

    Attributes:
        name: Unique identifier for the step.
        func: Transformation function that takes input of type T and returns U.
        required: If True, step failure stops the pipeline. If False, failure
            is logged and pipeline continues with None data.
        skip_on_none: If True and input data is None, step is skipped and
            None is passed to next step.
        timeout: Optional timeout in seconds (not enforced, for documentation).
    """
    name: str
    func: Callable[[T], U]
    required: bool = True
    skip_on_none: bool = False
    timeout: Optional[float] = None

    def execute(self, input_data: T) -> StepResult[U]:
        """
        Execute the step with the given input data.

        Args:
            input_data: Input data to process.

        Returns:
            StepResult containing the output data or error information.
        """
        if self.skip_on_none and input_data is None:
            logger.debug("Step %s skipped due to None input", self.name)
            return StepResult.ok(None, step_name=self.name, skipped=True)

        try:
            logger.debug("Executing step: %s", self.name)
            output = self.func(input_data)
            return StepResult.ok(output, step_name=self.name)
        except Exception as e:
            error_msg = f"Step '{self.name}' failed: {type(e).__name__}: {e}"
            logger.error(error_msg)
            return StepResult.fail(error_msg, step_name=self.name)


@dataclass
class PipelineResult(Generic[T]):
    """
    Aggregated result of a pipeline execution.

    Attributes:
        success: Whether all required steps completed successfully.
        data: Final output data from the last successful step.
        step_results: List of results from each executed step.
        error: Error message if pipeline failed (from first failing required step).
        executed_steps: Number of steps that were executed.
        skipped_steps: Number of steps that were skipped.
    """
    success: bool
    data: Optional[T] = None
    step_results: list = field(default_factory=list)
    error: Optional[str] = None
    executed_steps: int = 0
    skipped_steps: int = 0

    @property
    def all_results(self) -> list[StepResult]:
        """Return all step results including skipped ones."""
        return self.step_results


class Pipeline(Generic[T]):
    """
    A sequential data processing pipeline.

    The pipeline executes steps in order, passing the output of each step
    as input to the next. It supports conditional execution, error handling,
    and result aggregation.

    Type Parameters:
        T: The type of data flowing through the pipeline (input and output).

    Example:
        >>> pipeline = Pipeline[str]()
        >>> pipeline.add_step(Step("trim", lambda s: s.strip()))
        >>> pipeline.add_step(Step("uppercase", lambda s: s.upper()))
        >>> result = pipeline.execute("  hello  ")
        >>> result.data
        'HELLO'
    """

    def __init__(self, name: str = "pipeline"):
        """
        Initialize an empty pipeline.

        Args:
            name: Optional name for the pipeline (used in logging).
        """
        self.name = name
        self._steps: list[Step[Any, Any]] = []

    def add_step(self, step: Step[Any, Any]) -> "Pipeline[T]":
        """
        Add a processing step to the pipeline.

        Args:
            step: Step instance to add.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If a step with the same name already exists.
        """
        if any(s.name == step.name for s in self._steps):
            raise ValueError(f"Step with name '{step.name}' already exists in pipeline")
        self._steps.append(step)
        logger.debug("Added step '%s' to pipeline '%s'", step.name, self.name)
        return self

    def add_function(
        self,
        name: str,
        func: Callable[[T], T],
        required: bool = True,
        skip_on_none: bool = False,
        timeout: Optional[float] = None,
    ) -> "Pipeline[T]":
        """
        Convenience method to add a step from a simple function.

        Args:
            name: Name for the step.
            func: Transformation function.
            required: Whether step failure stops the pipeline.
            skip_on_none: Whether to skip step on None input.
            timeout: Optional timeout documentation.

        Returns:
            Self for method chaining.
        """
        step = Step(
            name=name,
            func=func,
            required=required,
            skip_on_none=skip_on_none,
            timeout=timeout,
        )
        return self.add_step(step)

    def execute(self, initial_data: T) -> PipelineResult[T]:
        """
        Execute the pipeline with the given initial data.

        Args:
            initial_data: Starting data for the pipeline.

        Returns:
            PipelineResult containing the final data and execution details.
        """
        logger.info("Starting pipeline '%s' with %d steps", self.name, len(self._steps))

        current_data: Any = initial_data
        step_results: list[StepResult] = []
        executed = 0
        skipped = 0

        for step in self._steps:
            result = step.execute(current_data)
            step_results.append(result)

            if result.metadata.get("skipped"):
                skipped += 1
                continue

            executed += 1

            if not result.success:
                if step.required:
                    logger.error("Pipeline '%s' stopped at required step '%s'",
                                 self.name, step.name)
                    return PipelineResult(
                        success=False,
                        data=None,
                        step_results=step_results,
                        error=result.error,
                        executed_steps=executed,
                        skipped_steps=skipped,
                    )
                else:
                    logger.warning("Optional step '%s' failed, continuing",
                                   step.name)
                    current_data = None
            else:
                current_data = result.data

        logger.info("Pipeline '%s' completed successfully", self.name)
        return PipelineResult(
            success=True,
            data=current_data,
            step_results=step_results,
            executed_steps=executed,
            skipped_steps=skipped,
        )

    def execute_with_context(
        self,
        initial_data: T,
        context: dict[str, Any],
    ) -> PipelineResult[T]:
        """
        Execute the pipeline with an additional context dictionary.

        The context is passed to each step function as a second argument
        if the function accepts it. Functions that only accept one argument
        will receive just the data.

        Args:
            initial_data: Starting data for the pipeline.
            context: Additional context data available to steps.

        Returns:
            PipelineResult containing the final data and execution details.
        """
        logger.info("Starting pipeline '%s' with context", self.name)

        current_data: Any = initial_data
        step_results: list[StepResult] = []
        executed = 0
        skipped = 0

        for step in self._steps:
            if step.skip_on_none and current_data is None:
                skipped += 1
                step_results.append(StepResult.ok(
                    None, step_name=step.name, skipped=True))
                continue

            executed += 1
            try:
                logger.debug("Executing step: %s (with context)", step.name)
                # Check if function accepts context parameter
                import inspect
                sig = inspect.signature(step.func)
                if len(sig.parameters) >= 2:
                    output = step.func(current_data, context)
                else:
                    output = step.func(current_data)
                result = StepResult.ok(output, step_name=step.name)
            except Exception as e:
                error_msg = f"Step '{step.name}' failed: {type(e).__name__}: {e}"
                logger.error(error_msg)
                result = StepResult.fail(error_msg, step_name=step.name)

            step_results.append(result)

            if not result.success:
                if step.required:
                    return PipelineResult(
                        success=False,
                        data=None,
                        step_results=step_results,
                        error=result.error,
                        executed_steps=executed,
                        skipped_steps=skipped,
                    )
                else:
                    current_data = None
            else:
                current_data = result.data

        return PipelineResult(
            success=True,
            data=current_data,
            step_results=step_results,
            executed_steps=executed,
            skipped_steps=skipped,
        )

    def get_step_names(self) -> list[str]:
        """Return list of step names in execution order."""
        return [step.name for step in self._steps]

    def __len__(self) -> int:
        """Return the number of steps in the pipeline."""
        return len(self._steps)

    def __repr__(self) -> str:
        step_names = " -> ".join(self.get_step_names())
        return f"Pipeline(name='{self.name}', steps=[{step_names}])"


def create_validation_pipeline(
    required_fields: list[str],
    field_types: Optional[dict[str, type]] = None,
) -> Pipeline[dict[str, Any]]:
    """
    Create a pipeline for validating dictionary input.

    Args:
        required_fields: List of field names that must be present.
        field_types: Optional mapping of field names to expected types.

    Returns:
        Configured pipeline that validates input dictionaries.
    """
    def validate_presence(data: dict[str, Any]) -> dict[str, Any]:
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        return data

    def validate_types(data: dict[str, Any]) -> dict[str, Any]:
        if not field_types:
            return data
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                raise TypeError(
                    f"Field '{field}' must be {expected_type.__name__}, "
                    f"got {type(data[field]).__name__}"
                )
        return data

    pipeline = Pipeline[dict[str, Any]](name="validation")
    pipeline.add_function("check_presence", validate_presence)
    if field_types:
        pipeline.add_function("check_types", validate_types)
    return pipeline


def create_data_transformation_pipeline(
    transformations: list[tuple[str, Callable[[Any], Any]]],
) -> Pipeline[Any]:
    """
    Create a pipeline from a list of named transformations.

    Args:
        transformations: List of (name, function) tuples.

    Returns:
        Configured pipeline with the given transformations.
    """
    pipeline = Pipeline[Any](name="transformation")
    for name, func in transformations:
        pipeline.add_function(name, func)
    return pipeline
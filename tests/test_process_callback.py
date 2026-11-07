"""
Focused tests for the DataProcessor.process callback evaluation contract.

These tests guard against the regression where the callback was evaluated
more than once per input item (once in the filter condition and once for the
retained value), which caused side effects to happen twice and produced
inconsistent results for stateful callbacks.
"""

import copy

from mylib.core import DataProcessor


class TestProcessCallbackEvaluatedOnce:
    """The callback must be called exactly once per input item."""

    def test_callback_called_once_per_item_including_filtered(self):
        """Every input item, even those filtered out, triggers exactly one call."""
        items = [
            {"id": 1, "keep": True},
            {"id": 2, "keep": False},
            {"id": 3, "keep": True},
            {"id": 4, "keep": False},
            {"id": 5, "keep": True},
        ]
        call_counts = {item["id"]: 0 for item in items}

        def counter(item):
            call_counts[item["id"]] += 1
            return item if item["keep"] else None

        processor = DataProcessor(copy.deepcopy(items))
        processor.process(counter)

        for item_id, count in call_counts.items():
            assert count == 1, f"item {item_id} was called {count} times, expected 1"

    def test_stateful_callback_is_consistent(self):
        """A stateful callback must not double-apply its side effects."""
        items = [{"id": i} for i in range(4)]
        seen = []

        def recorder(item):
            seen.append(item["id"])
            # Only keep even ids; the "filter" is applied once.
            return item if item["id"] % 2 == 0 else None

        processor = DataProcessor(copy.deepcopy(items))
        result = processor.process(recorder)

        assert seen == [0, 1, 2, 3]
        assert [item["id"] for item in result.data] == [0, 2]


class TestProcessPreservesOrderAndResults:
    """Retained items must keep their original relative order."""

    def test_kept_items_preserve_order(self):
        items = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
            {"id": 4, "name": "Diana"},
            {"id": 5, "name": "Eve"},
        ]
        processor = DataProcessor(copy.deepcopy(items))
        processor.process(lambda x: x if x["id"] % 2 == 1 else None)

        assert [item["id"] for item in processor.data] == [1, 3, 5]

    def test_no_items_retained(self):
        """When every callback returns None, the result is an empty list."""
        processor = DataProcessor([{"id": 1}, {"id": 2}])
        processor.process(lambda x: None)
        assert processor.data == []

    def test_all_items_retained(self):
        processor = DataProcessor([{"id": 1}, {"id": 2}])
        processor.process(lambda x: x)
        assert [item["id"] for item in processor.data] == [1, 2]


class TestProcessFluentApiAndHistory:
    """process must return the same instance and record correct history counts."""

    def test_returns_same_processor_instance(self):
        processor = DataProcessor([{"id": 1}, {"id": 2}])
        result = processor.process(lambda x: x)
        assert result is processor

    def test_history_records_input_and_output_counts(self):
        items = [
            {"id": 1, "keep": True},
            {"id": 2, "keep": False},
            {"id": 3, "keep": True},
            {"id": 4, "keep": False},
            {"id": 5, "keep": True},
        ]
        processor = DataProcessor(copy.deepcopy(items))
        processor.process(lambda x: x if x["keep"] else None)

        assert len(processor.history) == 1
        entry = processor.history[0]
        assert entry["action"] == "process"
        assert entry["input_count"] == 5
        assert entry["output_count"] == 3

    def test_history_accumulates_across_calls(self):
        processor = DataProcessor([{"id": 1}, {"id": 2}, {"id": 3}])
        processor.process(lambda x: x if x["id"] != 2 else None)
        processor.process(lambda x: x)

        assert len(processor.history) == 2
        assert processor.history[0]["input_count"] == 3
        assert processor.history[0]["output_count"] == 2
        assert processor.history[1]["input_count"] == 2
        assert processor.history[1]["output_count"] == 2
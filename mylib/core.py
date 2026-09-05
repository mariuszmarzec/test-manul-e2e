"""
Core classes for WebFrame.

This module provides the main processing, filtering, and transformation
classes used throughout the framework.
"""

import re
from typing import Any, Dict, List, Optional, Callable, Union


class DataProcessor:
    """
    General-purpose data processor that can transform and manage datasets.
    
    Supports filtering, mapping, and aggregation operations on lists of
    dictionaries or other iterable data sources.
    """
    
    def __init__(self, data: Optional[List[Dict[str, Any]]] = None):
        """Initialize with optional data."""
        self._data = data if data is not None else []
        self._history: List[Dict[str, Any]] = []
    
    @property
    def data(self) -> List[Dict[str, Any]]:
        """Return a copy of the current data."""
        return list(self._data)
    
    @data.setter
    def data(self, value: List[Dict[str, Any]]) -> None:
        """Set new data."""
        self._data = list(value)
    
    def process(self, func: Callable[[Dict[str, Any]], Dict[str, Any]]) -> "DataProcessor":
        """Apply a function to each item in the dataset."""
        original_count = len(self._data)
        self._data = [func(item) for item in self._data if func(item) is not None]
        self._history.append({
            "action": "process",
            "input_count": original_count,
            "output_count": len(self._data),
        })
        return self
    
    def map(self, key: str, func: Callable[[Any], Any]) -> "DataProcessor":
        """Apply a function to a specific key in each item."""
        for item in self._data:
            if key in item:
                item[key] = func(item[key])
        self._history.append({
            "action": "map",
            "key": key,
            "count": len(self._data),
        })
        return self
    
    def aggregate(self, key: str, operation: str = "sum") -> Union[int, float]:
        """
        Aggregate values from a specific key.
        
        Supported operations: sum, avg, min, max, count
        """
        if not self._data:
            return 0
        
        values = [item[key] for item in self._data if key in item]
        
        if operation == "sum":
            result = sum(values)
        elif operation == "avg":
            result = sum(values) / len(values) if values else 0
        elif operation == "min":
            result = min(values) if values else 0
        elif operation == "max":
            result = max(values) if values else 0
        elif operation == "count":
            result = len(values)
        else:
            raise ValueError(f"Unknown aggregation operation: {operation}")
        
        self._history.append({
            "action": "aggregate",
            "key": key,
            "operation": operation,
            "result": result,
        })
        return result
    
    def first(self) -> Optional[Dict[str, Any]]:
        """Return the first item in the dataset."""
        return self._data[0] if self._data else None
    
    def last(self) -> Optional[Dict[str, Any]]:
        """Return the last item in the dataset."""
        return self._data[-1] if self._data else None
    
    def limit(self, n: int) -> "DataProcessor":
        """Return a new processor with only the first n items."""
        new_processor = DataProcessor(self._data[:n])
        return new_processor
    
    @property
    def history(self) -> List[Dict[str, Any]]:
        """Return a copy of the operation history."""
        return list(self._history)

    def paginate(self, page: int, per_page: int) -> Dict[str, Any]:
        """Return paginated results with metadata."""
        total = len(self._data)
        start = (page - 1) * per_page
        end = start + per_page
        items = self._data[start:end]
        
        return {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Return processor state as a dictionary."""
        return {
            "count": len(self._data),
            "history_length": len(self._history),
            "first": self.first(),
            "last": self.last(),
        }


class Filter:
    """
    Flexible filtering class for datasets.
    
    Supports equality, inequality, range, and contains checks.
    """
    
    def __init__(self, data: List[Dict[str, Any]]):
        """Initialize with data to filter."""
        self._data = data
        self._conditions: List[Dict[str, Any]] = []
    
    def where(self, key: str, value: Any) -> "Filter":
        """Add equality condition."""
        self._conditions.append({
            "type": "eq",
            "key": key,
            "value": value,
        })
        return self
    
    def where_not(self, key: str, value: Any) -> "Filter":
        """Add inequality condition."""
        self._conditions.append({
            "type": "neq",
            "key": key,
            "value": value,
        })
        return self
    
    def where_gt(self, key: str, value: Any) -> "Filter":
        """Add greater-than condition."""
        self._conditions.append({
            "type": "gt",
            "key": key,
            "value": value,
        })
        return self
    
    def where_lt(self, key: str, value: Any) -> "Filter":
        """Add less-than condition."""
        self._conditions.append({
            "type": "lt",
            "key": key,
            "value": value,
        })
        return self
    
    def where_gte(self, key: str, value: Any) -> "Filter":
        """Add greater-than-or-equal condition."""
        self._conditions.append({
            "type": "gte",
            "key": key,
            "value": value,
        })
        return self
    
    def where_lte(self, key: str, value: Any) -> "Filter":
        """Add less-than-or-equal condition."""
        self._conditions.append({
            "type": "lte",
            "key": key,
            "value": value,
        })
        return self
    
    def where_contains(self, key: str, value: str) -> "Filter":
        """Add contains condition (for strings and lists)."""
        self._conditions.append({
            "type": "contains",
            "key": key,
            "value": value,
        })
        return self
    
    def where_in(self, key: str, values: List[Any]) -> "Filter":
        """Add 'in' condition."""
        self._conditions.append({
            "type": "in",
            "key": key,
            "value": values,
        })
        return self
    
    def apply(self) -> List[Dict[str, Any]]:
        """Apply all conditions and return filtered results."""
        result = self._data
        
        for condition in self._conditions:
            filtered = []
            for item in result:
                if condition["key"] not in item:
                    continue
                
                item_value = item[condition["key"]]
                
                if condition["type"] == "eq" and item_value == condition["value"]:
                    filtered.append(item)
                elif condition["type"] == "neq" and item_value != condition["value"]:
                    filtered.append(item)
                elif condition["type"] == "gt" and item_value > condition["value"]:
                    filtered.append(item)
                elif condition["type"] == "lt" and item_value < condition["value"]:
                    filtered.append(item)
                elif condition["type"] == "gte" and item_value >= condition["value"]:
                    filtered.append(item)
                elif condition["type"] == "lte" and item_value <= condition["value"]:
                    filtered.append(item)
                elif condition["type"] == "contains":
                    if isinstance(item_value, list):
                        if condition["value"] in item_value:
                            filtered.append(item)
                    elif condition["value"] in str(item_value):
                        filtered.append(item)
                elif condition["type"] == "in" and item_value in condition["value"]:
                    filtered.append(item)
            
            result = filtered
        
        return result


class Transformer:
    """
    Transform data structures with pluggable transformation rules.
    
    Supports renaming keys, adding computed fields, and nested transformations.
    """
    
    def __init__(self, template: Optional[Dict[str, Any]] = None):
        """Initialize with an optional transformation template."""
        self._template = template or {}
        self._transformations: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = []
    
    def rename(self, old_name: str, new_name: str) -> "Transformer":
        """Add a key rename transformation."""
        def transform(item: Dict[str, Any]) -> Dict[str, Any]:
            if old_name in item:
                item[new_name] = item.pop(old_name)
            return item
        self._transformations.append(transform)
        return self
    
    def add_field(self, name: str, value: Any) -> "Transformer":
        """Add a constant field to all items."""
        def transform(item: Dict[str, Any]) -> Dict[str, Any]:
            item[name] = value
            return item
        self._transformations.append(transform)
        return self
    
    def compute_field(self, name: str, func: Callable[[Dict[str, Any]], Any]) -> "Transformer":
        """Add a computed field based on a function."""
        def transform(item: Dict[str, Any]) -> Dict[str, Any]:
            item[name] = func(item)
            return item
        self._transformations.append(transform)
        return self
    
    def remove_field(self, name: str) -> "Transformer":
        """Remove a field from all items."""
        def transform(item: Dict[str, Any]) -> Dict[str, Any]:
            item.pop(name, None)
            return item
        self._transformations.append(transform)
        return self
    
    def apply(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply all transformations to a list of items."""
        result = []
        for item in data:
            new_item = dict(item)
            for transform in self._transformations:
                new_item = transform(new_item)
            result.append(new_item)
        return result
    
    def apply_single(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformations to a single item."""
        result = dict(item)
        for transform in self._transformations:
            result = transform(result)
        return result

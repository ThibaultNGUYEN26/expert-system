import logging

from collections.abc import Callable

class AndCondition:
    """Evaluate a collection of conditions using boolean AND semantics."""

    def __init__(self, *conditions):
        self.conditions = list(conditions)

    def _condition_label(self, condition):
        for attr in ("rule_format", "expression", "name"):
            label = getattr(condition, attr, None)
            if label:
                return label
        return str(condition)


    def _evaluate_single(self, condition, context):
        if hasattr(condition, "evaluate"):
            return condition.evaluate(context)

        if isinstance(condition, Callable):
            try:
                return condition(context)
            except TypeError:
                return condition()

        return bool(condition)


    def evaluate(self, context=None):
        results = []
        for condition in self.conditions:
            evaluated = self._evaluate_single(condition, context)
            outcome = bool(evaluated)
            logging.debug(f"{self._condition_label(condition)} : {outcome}")
            results.append(outcome)
        return all(results)

"""Custom deterministic evaluator for the golden dataset."""

from strands_evals.evaluators.evaluator import Evaluator
from strands_evals.types import EvaluationOutput


class ExpectedContains(Evaluator):
    """Passes when the case's `expected_output` shows up in the answer.

    `expected_output` holds one or more keywords separated by `|`; ANY of them is enough
    (case-insensitive). That keeps the dataset readable and tolerant to phrasing, while still
    being a plain string check: no judge model, no tokens.
    """

    def __init__(self, name: str = "ExpectedContains"):
        super().__init__(name=name)

    def evaluate(self, evaluation_case) -> list[EvaluationOutput]:
        expected = str(evaluation_case.expected_output or "")
        options = [o.strip().lower() for o in expected.split("|") if o.strip()]
        if not options:
            raise ValueError("ExpectedContains needs a non-empty expected_output on every case")
        actual = str(evaluation_case.actual_output).lower()
        found = [o for o in options if o in actual]
        return [EvaluationOutput(
            score=1.0 if found else 0.0,
            test_pass=bool(found),
            reason=(f"la respuesta contiene '{found[0]}'" if found
                    else f"la respuesta no contiene ninguna de: {options}"),
        )]

    async def evaluate_async(self, evaluation_case) -> list[EvaluationOutput]:
        return self.evaluate(evaluation_case)

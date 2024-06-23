"""CLI application use cases."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from sghi.config import ImproperlyConfiguredError
from sghi.etl.core import WorkflowDefinition
from sghi.etl.runtime.exceptions import SGHIETLRuntimeError
from sghi.utils import ensure_callable, ensure_predicate, type_fqn

if TYPE_CHECKING:
    from collections.abc import Sequence


# =============================================================================
# TYPES
# =============================================================================


_WorkflowFactory = Callable[[], WorkflowDefinition[Any, Any]]


# =============================================================================
# HELPERS
# =============================================================================


def _workflow_factory_to_instance(
    workflow_factory: _WorkflowFactory,
) -> WorkflowDefinition:
    ensure_callable(
        value=workflow_factory,
        message="'workflow_factory' MUST be a callable object.",
    )

    workflow = workflow_factory()
    ensure_predicate(
        test=isinstance(workflow, WorkflowDefinition),
        message=(
            f"The factory '{type_fqn(workflow_factory)}' did not return an "
            f"'{type_fqn(WorkflowDefinition)}' instance."
        ),
        exc_factory=ImproperlyConfiguredError,
    )

    return workflow


# =============================================================================
# EXCEPTIONS
# =============================================================================


class NoSuchWorkflowsError(SGHIETLRuntimeError):
    """Indicates that selected workflow(s) are not known."""

    def __init__(
        self,
        missing_workflows: Sequence[str],
        message: str | None = None,
        *args: Any,  # noqa: ANN401
    ) -> None:
        """Create a new ``NoSuchWorkflowsError`` of the given properties.

        :param missing_workflows: A ``Sequence`` of the workflow identifiers
            that are missing/unknown. This MUST be a ``Sequence``.
        :param message: An optional error message describing the error that
            occurred. A default error message will be used if no value is
            provided.
        :param args: Optional args to forward to the base exceptions.
        """
        _message: str = message or (
            "The following workflow(s) do not exists: "
            f"'{','.join(missing_workflows)}'."
        )
        super().__init__(_message, *args)
        self._missing_workflows: Sequence[str] = tuple(missing_workflows)

    @property
    def missing_workflows(self) -> Sequence[str]:
        """A ``Sequence`` of the workflows identifiers that are unknown."""
        return self._missing_workflows


# =============================================================================
# USE CASES
# =============================================================================


def list_workflows() -> Mapping[str, WorkflowDefinition]:
    """List all loaded and registered workflows.

    :return: A ``Mapping`` of all the loaded and registered workflows.
    """
    return {}


def run_workflows(select: Sequence[str] | None = None) -> None:
    """Load and run the selected ETL workflows. Run all when ``None``.

    :param select: An optional ``Sequence`` of the workflow identifiers to run.
        When ``None``, all available workflows will be run.
        This MUST be a ``Sequence`` when NOT ``None``.

    :raise NoSuchWorkflowsError: If any of the selected workflows, identifiers
        do NOT exist.
    """
    _err_msg = "Oops"
    raise RuntimeError(_err_msg)

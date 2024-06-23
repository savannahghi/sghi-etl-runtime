"""Common exceptions raised within this library."""

from typing import Any

from sghi.etl.core import WorkflowDefinition
from sghi.exceptions import SGHIError


class SGHIETLRuntimeError(SGHIError):
    """Base exception for most non-builtin exceptions raised by this library."""  # noqa: E501


class RunWorkflowsError(BaseExceptionGroup, SGHIETLRuntimeError):
    """Error(s) occurred while executing SGHI ETL Workflows.

    This error is typically raised by the
    :func:`sghi.etl.runtime.lib.run_workflows` function.
    """


class WorkflowExecutionError(SGHIETLRuntimeError):
    """An error occurred while executing an SGHI ETL Workflow."""

    def __init__(
        self,
        workflow_def: WorkflowDefinition,
        message: str | None = None,
        *args: Any,  # noqa: ANN401
    ) -> None:
        """Create a ``WorkflowExecutionError`` of the given properties.

        :param workflow_def: The ``WorkflowDefinition`` of the workflow whose
            execution failed. This MUST NOT be ``None``.
        :param message: An optional error message describing the error that
            occurred. A default error message will be used if no value is
            provided.
        :param args: Optional args to forward to the base exceptions.
        """
        _message: str = message or (
            "An error occurred while executing the workflow whose id="
            f"'{workflow_def.id}' and name='{workflow_def.name}'."
        )
        super().__init__(_message, *args)
        self._workflow_def: WorkflowDefinition = workflow_def

    @property
    def workflow_def(self) -> WorkflowDefinition:
        """The class:`~sghi.etl.core.WorkflowDefinition` of the workflow whose
        execution failed.
        """  # noqa: D205
        return self._workflow_def

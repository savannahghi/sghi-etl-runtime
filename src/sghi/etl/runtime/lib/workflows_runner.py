"""A utility for executing multiple SGHI ETL Workflows concurrently."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from logging import Logger
from typing import Any, Final

from typing_extensions import override

from sghi.config import ImproperlyConfiguredError
from sghi.etl.commons import run_workflow
from sghi.etl.core import WorkflowDefinition
from sghi.task import Task, execute_concurrently
from sghi.utils import (
    ensure_callable,
    ensure_instance_of,
    ensure_predicate,
    type_fqn,
)

from ..exceptions import RunWorkflowsError, WorkflowExecutionError

# =============================================================================
# TYPES
# =============================================================================


_WorkflowFactory = Callable[[], WorkflowDefinition[Any, Any]]


# =============================================================================
# CONSTANTS
# =============================================================================


_WORKFLOW_EXC_LOGGER_PREFIX: Final[str] = f"{__name__}.workflow_executor"


# =============================================================================
# HELPERS
# =============================================================================


class _WorkflowExecutor(Task[None, None]):
    __slots__ = ("_workflow_factory",)

    def __init__(self, workflow_factory: _WorkflowFactory) -> None:
        super().__init__()
        ensure_callable(
            value=workflow_factory,
            message="'workflow_factory' MUST be a callable object.",
        )
        self._workflow_factory: _WorkflowFactory = workflow_factory

    @override
    def execute(self, an_input: None = None) -> None:
        workflow: WorkflowDefinition[Any, Any]
        workflow = self._workflow_factory_to_instance(self._workflow_factory)
        ensure_predicate(
            test=isinstance(workflow, WorkflowDefinition),
            message=(
                f"The factory '{type_fqn(self._workflow_factory)}', did not "
                f"return an '{type_fqn(WorkflowDefinition)}' instance."
            ),
            exc_factory=TypeError,
        )

        logger: Logger = logging.getLogger(
            f"{_WORKFLOW_EXC_LOGGER_PREFIX}[{workflow.id}:{workflow.name}]"
        )
        try:
            logger.info("Starting workflow execution ...")
            run_workflow(workflow)
            logger.info("Workflow execution complete.")
        except Exception as exp:
            logger.exception("Error executing workflow.")
            raise WorkflowExecutionError(workflow) from exp

    @staticmethod
    def _workflow_factory_to_instance(
        workflow_factory: _WorkflowFactory,
    ) -> WorkflowDefinition[Any, Any]:
        workflow = workflow_factory()
        ensure_predicate(
            test=isinstance(workflow, WorkflowDefinition),
            message=(
                f"The factory '{type_fqn(workflow_factory)}' did not return "
                f"an '{type_fqn(WorkflowDefinition)}' instance."
            ),
            exc_factory=ImproperlyConfiguredError,
        )

        return workflow


# =============================================================================
# USE CASES
# =============================================================================


def run_workflows(workflow_factories: Sequence[_WorkflowFactory]) -> None:
    r"""Create and run ``WorkflowDefinition``\ s from the provided factories.

    :param workflow_factories: A ``Sequence`` of factory functions that
        return the ``WorkflowDefinition``\ s to run.

    :return: None.

    :raise RunWorkflowsError: If any of the provided ``WorkflowDefinition``\ s
        fails during execution.
    """
    ensure_instance_of(
        value=workflow_factories,
        klass=Sequence,
        message=(
            "'workflow_factories' MUST be a Sequence of factory functions "
            f"that supply '{type_fqn(WorkflowDefinition)}' instances."
        ),
    )
    if not workflow_factories:
        return

    workflow_executors: Sequence[_WorkflowExecutor] = tuple(
        _WorkflowExecutor(factory) for factory in workflow_factories
    )
    # -> from concurrent.futures import ProcessPoolExecutor as PPE

    # -> with execute_concurrently(*workflow_executors, executor=PPE()) as executor:  # noqa: E501
    with execute_concurrently(*workflow_executors) as executor:
        futures = executor.execute(None)

    exceptions: Sequence[BaseException]
    exceptions = tuple(f.exception() for f in futures if f.exception())  # pyright: ignore
    if exceptions:
        _err_msg: str = "Error(s) occurred while executing SGHI ETL Workflows."
        raise RunWorkflowsError(_err_msg, exceptions)


# =============================================================================
# MODULE EXPORTS
# =============================================================================


__alL__ = [
    "run_workflows",
]

"""Usecases."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from logging import Logger
from typing import Any, Final

from sghi.etl.core import WorkflowDefinition
from sghi.task import Task, execute_concurrently
from sghi.utils import (
    ensure_callable,
    ensure_instance_of,
    ensure_predicate,
    type_fqn,
)

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

    def execute(self, an_input: None = None) -> None:
        workflow: WorkflowDefinition = self._workflow_factory()
        ensure_predicate(
            test=isinstance(workflow, WorkflowDefinition),
            message=(
                f"The factory '{type_fqn(self._workflow_factory)}', did not "
                "return an 'sghi.etl.core.WorkflowDefinition' instance."
            ),
            exc_factory=TypeError,
        )

        logger: Logger = logging.getLogger(
            f"{_WORKFLOW_EXC_LOGGER_PREFIX}[{workflow.id} - {workflow.name}] "
        )
        try:
            logger.info("executing workflow...")
            self._do_run_workflow(workflow)
            logger.info("workflow executed successfully.")
        except Exception:
            logger.exception("error executing workflow.")
            raise

    @staticmethod
    def _do_run_workflow(workflow: WorkflowDefinition) -> None:
        with (
            workflow.source_factory() as source,
            workflow.processor_factory() as processor,
            workflow.sink_factory() as sink,
        ):
            sink.drain(processor.apply(source.draw()))


# =============================================================================
# USE CASES
# =============================================================================


def run_workflows(workflow_factories: Sequence[_WorkflowFactory]) -> None:
    r"""Create and run ``WorkflowDefinition``\ s from the provided factories.

    :param workflow_factories: A ``Sequence`` of factory functions that
        return the ``WorkflowDefinition``\ s to run.

    :return:
    """
    ensure_instance_of(
        value=workflow_factories,
        klass=Sequence,
        message=(
            "'workflow_factories' MUST be a Sequence of workflow factories."
        ),
    )
    if not workflow_factories:
        return

    workflow_executors: Sequence[_WorkflowExecutor] = tuple(
        _WorkflowExecutor(factory) for factory in workflow_factories
    )
    with execute_concurrently(*workflow_executors) as executor:
        executor.execute(None)


# =============================================================================
# MODULE EXPORTS
# =============================================================================


__alL__ = [
    "run_workflows",
]

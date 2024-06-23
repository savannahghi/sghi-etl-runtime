"""Application Signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sghi.dispatch import Signal

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sghi.etl.core import WorkflowDefinition


@dataclass(frozen=True, slots=True)
class AppConfigurationFailed(Signal):
    """Indicates that the application configuration failed.

    Unless otherwise specified at the use site, this signal will result in the
    application halting.

    .. important::

        The :class:`AppReady` and :class:`AppStopping` signals are never
        dispatched once this signal is dispatched.
    """

    err_message: str = field()
    exception: BaseException | None = field(default=None)


@dataclass(frozen=True, slots=True)
class AppReady(Signal):
    """Indicates that the application setup is done.

    This signal indicates that the application setup has completed
    (successfully) and normal application operations are about to begin.
    """


@dataclass(frozen=True, slots=True)
class AppStopping(Signal):
    """Indicates that the application is about to stop.

    Listeners can use this signal to perform cleanup actions and dispose of
    resources, etc.
    """


@dataclass(frozen=True, slots=True)
class ShowWorkflowsRequest(Signal):
    """A request to display all available workflows.

    This indicates that the user has made a request to the ``UI`` to display
    all available workflows.
    """

    available_workflows: Mapping[str, WorkflowDefinition] = field()


@dataclass(frozen=True, slots=True)
class UnhandledRuntimeErrorOccurred(Signal):
    """Indicates that unhandled error occurred at runtime.

    Unless otherwise specified at the use site, this signal will result in the
    application halting.
    """

    err_message: str = field()
    exception: BaseException | None = field(default=None)

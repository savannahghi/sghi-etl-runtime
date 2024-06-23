"""A Simple :class:`sghi.etl.runtime.cli.ui.UI` implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from typing_extensions import override

import sghi.app
from sghi.etl.runtime.cli.ui import UI

from ... import signals as app_s
from ..printers import print_debug, print_error, print_info, print_success

if TYPE_CHECKING:
    from sghi.dispatch import Dispatcher


@dataclass(frozen=True, slots=True)
class SimpleUI(UI):
    """Simple UI that displays app status information on the console."""

    @override
    def start(self) -> None:
        print_info("Starting ...")

        dispatcher: Dispatcher = sghi.app.dispatcher
        dispatcher.connect(app_s.AppConfigurationFailed, self._on_config_error)
        dispatcher.connect(app_s.AppReady, self._on_app_ready)
        dispatcher.connect(app_s.AppStopping, self._on_app_stopping)
        dispatcher.connect(app_s.ShowWorkflowsRequest, self._on_show_workflows)
        dispatcher.connect(
            signal_type=app_s.UnhandledRuntimeErrorOccurred,
            receiver=self._on_runtime_error,
        )

    @override
    def stop(self) -> None:
        print_success("Done 😁")

    @staticmethod
    def _on_app_ready(_: app_s.AppReady) -> None:
        print_debug("Started")

    @staticmethod
    def _on_app_stopping(_: app_s.AppStopping) -> None:
        print_debug("Stopping ...")

    @staticmethod
    def _on_config_error(signal: app_s.AppConfigurationFailed) -> None:
        print_error(signal.err_message, signal.exception)

    @staticmethod
    def _on_runtime_error(signal: app_s.UnhandledRuntimeErrorOccurred) -> None:
        print_error(signal.err_message, signal.exception)

    @staticmethod
    def _on_show_workflows(signal: app_s.ShowWorkflowsRequest) -> None:
        width: int = 75
        print_info("")
        print_info("=" * width)
        print_info(f'|{"AVAILABLE WORKFLOWS":^{width - 2}}|')
        print_info("=" * width)
        print_info("")

        for wf_id, workflow in signal.available_workflows.items():
            print_debug(f"\t- {wf_id}:{workflow.name}")
        else:
            print_info(
                f'{"So empty!!! No workflows appear to be loaded, yet.":^{width}}'  # noqa: E501
            )

        print_info("")
        print_info("-" * width)
        print_info("")

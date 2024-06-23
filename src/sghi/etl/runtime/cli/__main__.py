"""Application main module."""

from __future__ import annotations

import logging
import sys
from logging import Logger
from typing import TYPE_CHECKING, Any, Final, Literal

import click

import sghi.app
from sghi.config import (
    Config,
    ConfigProxy,
    ConfigurationError,
    SettingInitializer,
)

from . import signals, ui
from .constants import (
    APP_LOG_LEVEL_REG_KEY,
    APP_VERBOSITY_REG_KEY,
    DEFAULT_CONFIG,
)
from .lib import ConfigFormat, LoadConfigError, load_config_file

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

# =============================================================================
# TYPES
# =============================================================================


ConfigFormats = Literal["auto", "toml", "yaml"]

Supported_UIs = Literal["none", "simple"]


# =============================================================================
# CONSTANTS
# =============================================================================


_LOGGER: Final[Logger] = logging.getLogger("sghi.etl.runtime.cli")


# =============================================================================
# HELPERS
# =============================================================================


def _config_format_from_str(str_config_format: ConfigFormats) -> ConfigFormat:
    match str_config_format:
        case "auto":
            return ConfigFormat.AUTO
        case "toml":
            return ConfigFormat.TOML
        case "yaml":
            return ConfigFormat.YAML
        case _:
            _err_msg: str = (
                f"Unsupported config format: {str_config_format}, given."
            )
            raise ConfigurationError(message=_err_msg)


def _configure_runtime(
    config_file: str | None,
    config_format: ConfigFormat,
    log_level: str,
    verbosity: int,
) -> None:
    try:
        sghi.app.registry[APP_VERBOSITY_REG_KEY] = verbosity

        config_contents: Mapping[str, Any] | None = (
            load_config_file(config_file, config_format)
            if config_file is not None
            else None
        )
        sghi.app.setup = setup
        sghi.app.setup(settings=config_contents, log_level=log_level)
    except LoadConfigError as exp:
        _err_msg: str = exp.message or "Error loading configuration."
        sghi.app.dispatcher.send(signals.AppConfigurationFailed(_err_msg, exp))
        sys.exit(2)
    except ConfigurationError as exp:
        _err_msg: str = (
            "Error configuring the runtime. The cause of the error was: "
            f"{exp.message}"
        )
        # This might not be logged as logging may still be un-configured when
        # this error occurs.
        _LOGGER.exception(_err_msg)
        sghi.app.dispatcher.send(signals.AppConfigurationFailed(_err_msg, exp))
        sys.exit(3)


def _handle_runtime_error(exp: Exception, app_ui: ui.UI) -> None:
    _err_msg: str = (
        "An unhandled error occurred at runtime. The cause of the error "
        f"was: {exp!s}."
    )
    _LOGGER.exception(_err_msg)
    sghi.app.dispatcher.send(
        signals.UnhandledRuntimeErrorOccurred(_err_msg, exp),
    )
    app_ui.stop()
    sys.exit(5)


def _set_ui(preferred_ui: Supported_UIs) -> ui.UI:
    match preferred_ui:
        case "none":
            return ui.UI.of_no_ui()
        case "simple":
            from sghi.etl.runtime.cli.lib import SimpleUI

            return SimpleUI()
        case _:
            _err_msg: str = f"Unsupported UI option: '{preferred_ui}', given."
            raise ConfigurationError(message=_err_msg)


# =============================================================================
# SETUP
# =============================================================================


def setup(
    settings: Mapping[str, Any] | None = None,
    settings_initializers: Sequence[SettingInitializer] | None = None,
    log_level: int | str = "NOTSET",
    disable_default_initializers: bool = False,
) -> None:
    """Prepare the runtime and ready the application for use.

    :param settings: An optional mapping of settings and their values.
        When not provided, the runtime defaults as well as defaults set by the
        given setting initializers will be used instead.
    :param settings_initializers: An optional sequence of setting initializers
        to execute during runtime setup.
        Default initializers (set by the runtime) are always executed unless
        the ``disable_default_initializers`` param is set to ``True``.
    :param log_level: The log level to set for the root application logger.
        When not set, defaults to the value "NOTSET".
    :param disable_default_initializers: Exclude default setting initializers
        from being executed as part of the runtime setup.
        The default setting initializers set up logging and load SGHI ETL
        workflows into the application registry.
    """
    settings_dict: dict[str, Any] = dict(DEFAULT_CONFIG)
    settings_dict.update(settings or {})

    initializers: list[SettingInitializer] = list(settings_initializers or [])
    if not disable_default_initializers:
        from sghi.etl.runtime.cli.lib.config.settings_initializers import (
            setup_app_logging,
        )

        initializers.insert(0, setup_app_logging())

    sghi.app.registry[APP_LOG_LEVEL_REG_KEY] = log_level
    config: Config = Config.of(
        settings=settings_dict,
        setting_initializers=initializers,
    )
    match sghi.app.conf:
        case ConfigProxy():
            sghi.app.conf.set_source(config)
        case _:
            setattr(sghi.app, "conf", config)  # noqa: B010


# =============================================================================
# MAIN
# =============================================================================


@click.group(epilog="Lets do this! ;)", invoke_without_command=True)
@click.option(
    "-c",
    "--config",
    "config_file",
    default=None,
    envvar="SGHI_ETL_RUNTIME_CONFIG",
    help=(
        "Set the location of the configuration file to use. Both 'toml' and "
        "'yaml' file formats are supported."
    ),
    type=click.Path(exists=True, readable=True, resolve_path=True),
)
@click.option(
    "--config-format",
    default="auto",
    envvar="SGHI_ETL_RUNTIME_CONFIG_FORMAT",
    help=(
        "The format of the configuration file in use. Both 'toml' and 'yaml' "
        "file formats are supported. 'auto' determines the format of the "
        "configuration file in use based on the extension of the file. When "
        "that fails, defaults to assuming the configuration file is a 'toml' "
        "file."
    ),
    show_default=True,
    type=click.Choice(choices=("auto", "toml", "yaml")),
)
@click.option(
    "-l",
    "--log-level",
    default="WARNING",
    envvar="SGHI_ETL_RUNTIME_LOG_LEVEL",
    help='Set the log level of the "primary" application logger.',
    show_default=True,
    type=click.Choice(
        choices=(
            "CRITICAL",
            "ERROR",
            "WARNING",
            "INFO",
            "DEBUG",
            "NOTSET",
        ),
    ),
)
@click.option(
    "--ui",
    "preferred_ui",
    default="simple",
    envvar="SGHI_ETL_RUNTIME_UI",
    help="Select a user interface to use.",
    show_default=True,
    type=click.Choice(choices=("none", "simple")),
)
@click.option(
    "-v",
    "--verbose",
    "verbosity",
    count=True,
    default=0,
    envvar="SGHI_ETL_RUNTIME_VERBOSITY",
    help=(
        "Set the level of output to expect from the program on stdout. This "
        "is different from log level."
    ),
)
@click.version_option(package_name="sghi-etl-runtime", message="%(version)s")
@click.pass_context
def main(
    ctx: click.Context,
    config_file: str | None,
    config_format: ConfigFormats,
    log_level: str,
    preferred_ui: Supported_UIs,
    verbosity: int,
) -> None:
    """A tool for executing SGHI ETL workflows.

    \f

    :param ctx: An object holding the CLI's context.
    :param config_file: An optional path to a configuration file.
    :param config_format: The format of the config contents.
        Can be 'auto' which allows the configuration format to be determined
        from the extension of the file name.
    :param log_level: The log level of the "root application" logger.
    :param preferred_ui: The preferred user interface to use.
    :param verbosity: The level of output to expect from the application on
        stdout. This is different from log level.
    """  # noqa: D301, D401
    app_ui: ui.UI = _set_ui(preferred_ui)
    app_ui.start()

    _configure_runtime(
        config_file=config_file,
        config_format=_config_format_from_str(config_format),
        log_level=log_level,
        verbosity=verbosity,
    )

    ctx.obj = app_ui
    if ctx.invoked_subcommand is None:
        ctx.invoke(run_workflows)


@main.command(name="list")
@click.pass_obj
def list_workflows(app_ui: ui.UI) -> None:
    """List all available workflows."""
    try:
        sghi.app.dispatcher.send(signals.AppReady())

        # Delay this import as late as possible to avoid cyclic imports,
        # especially before application setup has completed.
        from .use_cases import list_workflows as _list_workflows

        workflows = _list_workflows()
        sghi.app.dispatcher.send(signals.ShowWorkflowsRequest(workflows))

        sghi.app.dispatcher.send(signals.AppStopping())
        app_ui.stop()
    except Exception as exp:  # noqa: BLE001
        _handle_runtime_error(exp, app_ui)


@main.command(name="run")
@click.option(
    "-s",
    "--select",
    "selected",
    default=(),
    help=(
        "The id of a specific workflow to run. Can be provided more than "
        "once. If no selection is made, then all available workflows are "
        "executed."
    ),
    multiple=True,
    type=str,
)
@click.pass_obj
def run_workflows(app_ui: ui.UI, selected: tuple[str, ...]) -> None:
    """Run the selected workflows. Run all when no selection is made."""
    try:
        sghi.app.dispatcher.send(signals.AppReady())

        # Delay this import as late as possible to avoid cyclic imports,
        # especially before application setup has completed.
        from .use_cases import run_workflows as _run_workflows

        _run_workflows(select=selected if selected else None)

        sghi.app.dispatcher.send(signals.AppStopping())
        app_ui.stop()
    except Exception as exp:  # noqa: BLE001
        _handle_runtime_error(exp, app_ui)


if __name__ == "__main__":
    main(auto_envvar_prefix="SGHI_ETL_RUNTIME")

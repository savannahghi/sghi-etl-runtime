"""Application settings initializers."""

from __future__ import annotations

import logging
from logging.config import dictConfig
from typing import TYPE_CHECKING, Any

import sghi.app
from sghi.config import (
    ImproperlyConfiguredError,
    setting_initializer,
)
from sghi.registry import RegistryItemSet

from ...constants import (
    APP_LOG_LEVEL_REG_KEY,
    DEFAULT_CONFIG,
    LOGGING_CONFIG_KEY,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

# =============================================================================
# HELPERS
# =============================================================================


def on_logging_level_changed(signal: RegistryItemSet) -> None:
    """Listen for log level changes and update the app logging configuration.

    This signal receiver listens for changes on the application logging level
    setting on the main application registry, and then updates the main
    application logger accordingly.

    :param signal: A ``RegistryItemSet`` signal.
    """
    if signal.item_key == APP_LOG_LEVEL_REG_KEY:
        logging.getLogger("sghi").setLevel(signal.item_value)


# =============================================================================
# INITIALIZERS
# =============================================================================


@setting_initializer(setting=LOGGING_CONFIG_KEY)
def setup_app_logging(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Configure logging for the application.

    :param config: Optional logging configuration.
        When not ``None``, the given value MUST be a ``dictConfig``
        ``Mapping``.

    :return: A ``Mapping`` of the given logging configuration or the
        default logging config if ``None`` was given.
    """
    logging_config: dict[str, Any] = dict(
        config or DEFAULT_CONFIG[LOGGING_CONFIG_KEY],
    )

    try:
        dictConfig(logging_config)
    except Exception as exp:
        _err_msg: str = (
            "The logging configuration provided doesn't appear to be valid. "
            f"The following error was raised: {exp!s}"
        )
        raise ImproperlyConfiguredError(message=_err_msg) from exp

    logging.getLogger("sghi").setLevel(
        sghi.app.registry.get(APP_LOG_LEVEL_REG_KEY, logging.CRITICAL),
    )
    sghi.app.registry.dispatcher.connect(
        signal_type=RegistryItemSet,
        receiver=on_logging_level_changed,
        weak=False,  # Last for the lifetime of the application
    )
    return logging_config

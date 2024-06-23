"""Utilities for loading application configuration on files."""

from __future__ import annotations

import os
from enum import Enum, unique
from typing import TYPE_CHECKING, Any, Final

from jinja2 import Environment, StrictUndefined, Template, select_autoescape
from jinja2.exceptions import UndefinedError
from jinja2.sandbox import ImmutableSandboxedEnvironment

from sghi.etl.runtime.exceptions import SGHIETLRuntimeError
from sghi.utils import ensure_instance_of, ensure_not_none_nor_empty

if TYPE_CHECKING:
    from collections.abc import Mapping

# =============================================================================
# CONSTANTS
# =============================================================================


_CONFIG_JINJA_ENV: Final[Environment] = ImmutableSandboxedEnvironment(
    autoescape=select_autoescape(default=True, default_for_string=True),
    undefined=StrictUndefined,
)


@unique
class ConfigFormat(Enum):
    """Listing of the supported config file formats."""

    AUTO = "auto"
    TOML = "toml"
    YAML = "yaml"


# =============================================================================
# EXCEPTIONS
# =============================================================================


class LoadConfigError(SGHIETLRuntimeError):
    """An error occurred while loading app configurations from a file."""


# =============================================================================
# HELPERS
# =============================================================================


def _pick_config_file_format(
    config_format: ConfigFormat,
    config_file_path: str,
) -> ConfigFormat:
    match config_format:
        case ConfigFormat.TOML | ConfigFormat.YAML:
            return config_format

    # Config.AUTO
    _, file_ext = os.path.splitext(config_file_path)
    match file_ext:
        case ".yaml" | ".yml":
            return ConfigFormat.YAML
        case _:
            return ConfigFormat.TOML


def _read_config(config_file_path: str) -> str:
    with open(config_file_path) as config_file:
        config_content: str = config_file.read()

    return config_content


def _substitute_env_variables(config_content: str) -> str:
    config_template: Template = _CONFIG_JINJA_ENV.from_string(config_content)
    try:
        return config_template.render(os.environ)
    except UndefinedError as exp:
        _err_msg: str = f"Undefined environment variable encountered: {exp!s}"
        raise LoadConfigError(message=_err_msg) from exp


# =============================================================================
# LOADERS
# =============================================================================


def load_config_file(
    config_file_path: str,
    config_format: ConfigFormat = ConfigFormat.AUTO,
) -> Mapping[str, Any]:
    """Load configuration from the given file and format.

    The configuration file has to be either in the "yaml" or "toml" format.
    When the ``config_format`` is set to ``ConfigFormat.AUTO``, the file format
    is deduced from the file extensions as follows:

        - *If the file extension is ".yaml" or ".yml", the file is assumed to
          be a "yaml" file.*
        - *Else, the file is treated as a "toml" file.*

    Sections of the file wrapped with double braces, i.e. ``{{`` and ``}}``
    will be substituted with environment variables with the same name.
    For example, in the following configuration snippet:
    ``DATABASE_PASSWORD: {{DB_PASSWORD}}``, the text ``{{DB_PASSWORD}}`` will
    be substituted with the value of an environment variable of the same name.
    If no such environment variable exists, then a :exc:`LoadConfigError` is
    raised.

    A ``LoadConfigError`` will also be raised in case the file can't be opened
    or read.

    :param config_file_path: A string representing a path on the file system
        that points to the configuration file to be loaded.
        This MUST be a NON-EMPTY string.
        This file MUST also exist and be readable.
    :param config_format: The format of the given file.
        When set to ``ConfigFormat.AUTO``, the default, the file extension of
        the file will be used to deduce the file format.

    :return: The contents of the loaded config file as a ``Mapping``.

    :raise LoadConfigError: If an error occurred while opening or reading the
        specified configuration file.
    """
    ensure_not_none_nor_empty(
        value=ensure_instance_of(
            value=config_file_path,
            klass=str,
            message="'config_file_path' MUST be a string.",
        ),
        message="'config_file_path' MUST NOT be an empty string.",
    )
    ensure_instance_of(
        value=config_format,
        klass=ConfigFormat,
        message="'config_format' MUST be a ConfigFormat instance.",
    )

    use_format: ConfigFormat = _pick_config_file_format(
        config_format=config_format,
        config_file_path=config_file_path,
    )
    try:
        config_src: str = _substitute_env_variables(
            config_content=_read_config(config_file_path),
        )
        match use_format:
            case ConfigFormat.YAML:
                import yaml

                return yaml.safe_load(config_src)
            case _:
                import tomllib

                return tomllib.loads(config_src)
    except LoadConfigError:
        # Raise a `LoadConfigError` as is without re-wrapping it in another
        # `LoadConfigError` error.
        raise
    except Exception as exp:
        _err_msg: str = (
            "Error opening/reading the given configuration file. Please "
            "ensure that the configuration file contents consist of valid "
            f'{use_format.value}, and that "{config_file_path}" points to '
            f'an existing readable file. The cause of the error was: "{exp!s}"'
        )
        raise LoadConfigError(message=_err_msg) from exp

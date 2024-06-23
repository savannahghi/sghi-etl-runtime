from __future__ import annotations

import os
from enum import Enum, unique
from typing import TYPE_CHECKING, Any, Final

from jinja2 import Environment, StrictUndefined, Template, select_autoescape
from jinja2.exceptions import UndefinedError
from jinja2.sandbox import ImmutableSandboxedEnvironment

from sghi.config import ConfigurationError
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


class LoadConfigError(ConfigurationError):
    """An error occurred while loading app configurations from a file."""


# =============================================================================
# HELPERS
# =============================================================================


def _pick_config_file_format(
    config_format: ConfigFormat,
    config_file_path: str,
) -> ConfigFormat:
    match config_format:
        case ConfigFormat.TOML, ConfigFormat.YAML:
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

    :param config_file_path:
    :param config_format:

    :return:
    """
    ensure_instance_of(
        value=config_file_path,
        klass=str,
        message="'config_file_path' MUST be a string.",
    )
    ensure_not_none_nor_empty(
        value=config_file_path,
        message="'config_file_path' MUST NOT be an empty string.",
    )
    ensure_instance_of(
        value=config_format,
        klass=ConfigFormat,
        message="'config_format' MUST be a ConfigFormat instance.",
    )

    try:
        use_format: ConfigFormat = _pick_config_file_format(
            config_format=config_format,
            config_file_path=config_file_path,
        )
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
        raise
    except Exception as exp:  # noqa: BLE001
        _err_msg: str = (
            "Error opening/reading the given configuration file. Please "
            "ensure that the configuration file contents consist of valid "
            f'{config_format.value}, and that "{config_file_path}" points to '
            f'an existing readable file. The cause of the error was: "{exp}"'
        )
        raise LoadConfigError(message=_err_msg) from exp

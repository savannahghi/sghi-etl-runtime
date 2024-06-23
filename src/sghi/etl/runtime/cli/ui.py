"""SGHI Runtime User Interface."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod

from typing_extensions import override

# =============================================================================
# UI INTERFACE
# =============================================================================


class UI(metaclass=ABCMeta):
    """Application user interface."""

    __slots__ = ()

    @abstractmethod
    def start(self) -> None:
        """Start the UI.

        Called at the beginning of the application.

        .. note::

            - Only called once.
            - Should not block the caller. Specifically, should not block the
              calling thread.

        :return: None.
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop the UI.

        Called at the end of the application.

        :return: None.
        """
        ...

    @staticmethod
    def of_no_ui() -> UI:
        """Return a :class:`UI` implementation that provides no UI.

        This is useful as a placeholder or as a means to disable UI on the
        application.

        :return: A ``UI`` implementation that provides no UI.
        """
        return _NoUI()


# =============================================================================
# UI IMPLEMENTATIONS
# =============================================================================


class _NoUI(UI):
    """:class:`UI` implementation that provides no UI."""

    @override
    def start(self) -> None: ...

    @override
    def stop(self) -> None: ...

# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2019 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

"""Singleton to start one vimiv process for tests."""

from PyQt5.QtCore import QThreadPool, QCoreApplication
from PyQt5.QtWidgets import QWidget

# Must mock decorator before import
from unittest import mock
mock.patch("vimiv.utils.cached_method", lambda x: x).start()

from vimiv import api, vimiv  # noqa
from vimiv.utils import working_directory  # noqa
from vimiv.imutils import imstorage  # noqa


_processes = []


def init(qtbot, argv):
    """Create the VimivProc object."""
    assert not _processes, "Not creating another vimiv process"
    _processes.append(VimivProc(qtbot, argv))


def instance():
    """Get the VimivProc object."""
    assert _processes, "No vimiv process created"
    return _processes[0]


def exit():
    """Close the vimiv process."""
    instance().exit()
    del _processes[0]


class VimivProc():
    """Process class to start and exit one vimiv process."""

    def __init__(self, qtbot, argv=[]):
        argv.extend(["--temp-basedir"])
        vimiv.startup(argv)
        for name, widget in api.objreg._registry.items():
            if isinstance(widget, QWidget):
                qtbot.addWidget(widget)
        # No crazy stuff should happen here, waiting is not really necessary
        working_directory.handler.WAIT_TIME = 0.001

    def exit(self):
        # Do not start any new threads
        QThreadPool.globalInstance().clear()
        # Wait for any running threads to exit safely
        QThreadPool.globalInstance().waitForDone(5000)  # Kill after 5s
        imstorage._paths = []
        imstorage._index = 0
        # Needed for cleanup
        QCoreApplication.instance().aboutToQuit.emit()
        api.settings.reset()

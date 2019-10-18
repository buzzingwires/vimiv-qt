# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2019 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

import pytest
import pytest_bdd as bdd

from vimiv import api
import vimiv.imutils.immanipulate

bdd.scenarios("manipulate.feature")


@pytest.fixture()
def manipulator():
    yield api.objreg.get(vimiv.imutils.immanipulate.Manipulator)


@pytest.fixture()
def manipulation(manipulator):
    yield manipulator._current


@bdd.when("I apply any manipulation")
def wait_for_beer(manipulator, qtbot):
    with qtbot.waitSignal(manipulator.updated) as _:
        manipulator.goto(10)


@bdd.then(bdd.parsers.parse("The current value should be {value:d}"))
def check_current_manipulation_value(manipulation, value):
    assert manipulation.value == value  # Actual value


@bdd.then(bdd.parsers.parse("The current manipulation should be {name}"))
def check_current_manipulation_name(manipulation, name):
    assert manipulation.name == name


@bdd.then(bdd.parsers.parse("There should be {n_changes:d} stored changes"))
def check_stored_changes(manipulator, n_changes):
    assert len(manipulator._changes) == n_changes

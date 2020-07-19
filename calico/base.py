# Copyright (C) 2016-2019 H. Turgut Uyar <uyar@itu.edu.tr>
#
# Calico is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Calico is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Calico.  If not, see <http://www.gnu.org/licenses/>.

"""Base classes for Calico."""

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import os
import sys
from collections import OrderedDict
from enum import Enum

import pexpect

from . import GLOBAL_TIMEOUT, SUPPORTS_JAIL


PY2 = sys.version_info < (3,)  # sig: bool

MAX_LEN = 40

_logger = logging.getLogger("calico")


class ActionType(Enum):
    """Type of an action."""

    EXPECT = ("e", "expect")  # sig: Tuple[str, str]
    SEND = ("s", "send")  # sig: Tuple[str, str]


class Action:
    """An action in a test script."""

    def __init__(self, type_, data, timeout=-1):
        """Initialize this action.

        :sig: (ActionType, str, Optional[int]) -> None
        :param type_: Expect or send.
        :param data: Data to expect or send.
        :param timeout: Timeout duration, in seconds.
        """
        self.type_ = type_  # sig: ActionType
        """Type of this action, expect or send."""

        self.data = data if data != "_EOF_" else pexpect.EOF  # sig: str
        """Data description of this action, what to expect or send."""

        self.timeout = timeout  # sig: Optional[int]
        """Timeout duration of this action."""

    def __iter__(self):
        """Get components of this action as a sequence."""
        yield self.type_.value[1]
        yield self.data if self.data != pexpect.EOF else "_EOF_"
        yield self.timeout


def run_script(command, script, defs=None, g_timeout=None):
    """Run a command and check whether it follows a script.

    :sig: (str, List[Action], Optional[Mapping], Optional[int]) -> Tuple[int, int, List[str]]
    :param command: Command to run.
    :param script: Script to check against.
    :param defs: Variable substitutions.
    :param g_timeout: Global timeout value for the spawn class
    :return: Exit status, signal status, and errors.
    """
    defs = defs if defs is not None else {}
    g_timeout = g_timeout if g_timeout is not None else GLOBAL_TIMEOUT

    process = pexpect.spawn(command, timeout=g_timeout)
    process.setecho(False)
    errors = []

    last = script[-1] if len(script) > 0 else None
    if (last is None) or ((last.type_ != ActionType.EXPECT) and (last.data != "_EOF_")):
        script.append(Action(ActionType.EXPECT, "_EOF_"))

    for action in script:
        if action.data is not pexpect.EOF:
            action.data = action.data % defs
        if action.type_ == ActionType.EXPECT:
            try:
                expecting = (
                    "_EOF_" if action.data is pexpect.EOF else ('"%(a)s"' % {"a": action.data})
                )
                timeout = action.timeout if action.timeout != -1 else g_timeout
                _logger.debug("  expecting (%ds): %s", timeout, expecting)
                process.expect(action.data, timeout=action.timeout)
                output = process.after
                received = (
                    "_EOF_" if ".EOF" in repr(output) else ('"%(o)s"' % {"o": output.decode()})
                )
                _logger.debug("  received: %s", received)
            except pexpect.EOF:
                output = process.before
                received = (
                    "_EOF_" if ".EOF" in repr(output) else ('"%(o)s"' % {"o": output.decode()})
                )
                _logger.debug('  received: "%s"', received)
                process.close(force=True)
                _logger.debug("FAILED: Expected output not received.")
                errors.append("Expected output not received.")
                break
            except pexpect.TIMEOUT:
                output = process.before
                received = (
                    "_EOF_" if ".EOF" in repr(output) else ('"%(o)s"' % {"o": output.decode()})
                )
                _logger.debug('  received: "%s"', received)
                process.close(force=True)
                _logger.debug("FAILED: Timeout exceeded.")
                errors.append("Timeout exceeded.")
                break
        elif action.type_ == ActionType.SEND:
            _logger.debug('  sending: "%s"', action.data)
            process.sendline(action.data)
    else:
        process.close(force=True)
    return process.exitstatus, process.signalstatus, errors


class TestCase:
    """A case in a test suite."""

    def __init__(
        self, name, command, timeout=-1, exits=0, points=None, blocker=False, visible=True
    ):
        """Initialize this test case.

        :sig:
            (
                str,
                str,
                Optional[int],
                Optional[int],
                Optional[Union[int, float]],
                Optional[bool],
                Optional[bool]
            ) -> None
        :param name: Name of the case.
        :param command: Command to run.
        :param timeout: Timeout duration, in seconds.
        :param exits: Expected exit status.
        :param points: Contribution to overall points.
        :param blocker: Whether failure blocks subsequent cases.
        :param visible: Whether the test will be visible during the run.
        """
        self.name = name  # sig: str
        """Name of this test case."""

        self.command = command  # sig: str
        """Command to run in this test case."""

        self.script = []  # sig: List[Action]
        """Sequence of actions to run in this test case."""

        self.timeout = timeout  # sig: Optional[int]
        """Timeout duration of this test case, in seconds."""

        self.exits = exits  # sig: Optional[int]
        """Expected exit status of this test case."""

        self.points = points  # sig: Optional[Union[int, float]]
        """How much this test case contributes to the total points."""

        self.blocker = blocker  # sig: bool
        """Whether failure in this case will block subsequent cases or not."""

        self.visible = visible  # sig: bool
        """Whether this test will be visible during the run or not."""

    def add_action(self, action):
        """Append an action to the script of this test case.

        :sig: (Action) -> None
        :param action: Action to append to the script.
        """
        self.script.append(action)

    def run(self, defs=None, jailed=False, g_timeout=None):
        """Run this test and produce a report.

        :sig:
            (
                Optional[Mapping],
                Optional[bool],
                Optional[int]
            ) -> Mapping[str, Union[str, List[str]]]
        :param defs: Variable substitutions.
        :param jailed: Whether to jail the command to the current directory.
        :param g_timeout: Global timeout for all expects in the test
        :return: Result report of the test.
        """
        report = {"errors": []}

        jail_prefix = ("fakechroot chroot %(d)s " % {"d": os.getcwd()}) if jailed else ""
        command = "%(j)s%(c)s" % {"j": jail_prefix, "c": self.command}
        _logger.debug("running command: %s", command)

        exit_status, signal_status, errors = run_script(
            self.command, self.script, defs=defs, g_timeout=g_timeout
        )
        report["errors"].extend(errors)

        if exit_status is not None:
            _logger.debug("exit status: %d (expected %d)", exit_status, self.exits)
        if signal_status is not None:
            _logger.debug("program terminated with signal %d", signal_status)
        if exit_status != self.exits:
            report["errors"].append("Incorrect exit status.")

        return report


class Calico(OrderedDict):
    """A suite containing a collection of ordered test cases."""

    def __init__(self):
        """Initialize this test suite from a given specification.

        :sig: () -> None
        """
        if PY2:
            OrderedDict.__init__(self)
        else:
            super().__init__()

        self.points = 0  # sig: Union[int, float]
        """Total points in this test suite."""

    def add_case(self, case):
        """Add a test case to this suite.

        :sig: (TestCase) -> None
        :param case: Test case to add.
        """
        if PY2:
            OrderedDict.__setitem__(self, case.name, case)
        else:
            super().__setitem__(case.name, case)
        self.points += case.points if case.points is not None else 0

    def run(self, tests=None, quiet=False, g_timeout=None):
        """Run this test suite.

        :sig: (Optional[bool], Optional[List[str]], Optional[int]) -> Mapping[str, Any]
        :param tests: Tests to include in the run.
        :param quiet: Whether to suppress progress messages.
        :param g_timeout: Global timeout value for the all tests
        :return: A report containing the results.
        """
        report = OrderedDict()
        earned_points = 0

        os.environ["TERM"] = "dumb"  # disable color output in terminal

        test_names = tests if tests is not None else [n for n in self.keys() if n[0] != "_"]
        for test_name in test_names:
            test = self.get(test_name)

            _logger.debug("starting test %s", test_name)
            if (not quiet) and test.visible:
                dots = "." * (MAX_LEN - len(test_name) + 1)
                print("%(t)s %(d)s" % {"t": test_name, "d": dots}, end=" ")

            jailed = SUPPORTS_JAIL and test_name.startswith("case_")
            report[test_name] = test.run(
                defs=self.get("_define_vars"), jailed=jailed, g_timeout=g_timeout
            )
            passed = len(report[test_name]["errors"]) == 0

            if test.points is None:
                if (not quiet) and test.visible:
                    print("PASSED" if passed else "FAILED")
            else:
                report[test_name]["points"] = test.points if passed else 0
                earned_points += report[test_name]["points"]
                if (not quiet) and test.visible:
                    scored = report[test_name]["points"]
                    print("%(s)s / %(p)s" % {"s": scored, "p": test.points})

            if test.blocker and (not passed):
                break

        report["points"] = earned_points
        return report

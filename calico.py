# Copyright (C) 2016-2018 H. Turgut Uyar <uyar@itu.edu.tr>
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

"""Calico is a utility for checking command-line programs.

For documentation, please refer to: https://calico.readthedocs.io/
"""

import logging
import os
import shutil
import sys
from argparse import ArgumentParser
from collections import OrderedDict

import pexpect
from ruamel import yaml


MAX_LEN = 40
SUPPORTS_JAIL = shutil.which("fakechroot") is not None

_logger = logging.getLogger(__name__)


def _get_yaml_comment(node, name, field):
    try:
        comment = node.ca.items[name][2].value[1:].strip()  # remove the leading hash
    except KeyError:
        comment = None
    if comment is not None:
        delim = field + ":"
        if comment.startswith(delim):
            return comment[len(delim) :].strip()
    return None


def parse_spec(source):
    """Parse a test specification.

    :sig: (str) -> Tuple[Mapping[str, Any], Union[int, float]]
    :param source: Specification to parse.
    :return: Tests in the spec file and their total points.
    :raise AssertionError: When given spec source is invalid.
    """
    try:
        config = yaml.round_trip_load(source)
    except yaml.YAMLError as e:
        raise AssertionError(str(e))

    if config is None:
        raise AssertionError("No configuration")

    total_points = 0
    tests = [(k, v) for c in config for k, v in c.items()]
    for test_name, test_body in tests:
        run = test_body.get("run")
        assert run is not None, f"{test_name}: no run command"
        assert isinstance(run, str), f"{test_name}: run command must be string"

        script = test_body.get("script")
        if script is None:
            timeout = _get_yaml_comment(test_body, "run", "timeout")
            assert (
                timeout is None
            ) or timeout.isdigit(), f"{test_name}: timeout value must be integer"
            script_item = (
                "expect",
                "_EOF_",
                int(timeout) if timeout is not None else None,
            )
            test_body["script"] = [script_item]
        else:
            test_body["script"] = []
            for step in script:
                action, data = [(k, v) for k, v in step.items()][0]
                assert action in ("expect", "send"), f"{test_name}: invalid action type"
                assert isinstance(data, str), f"{test_name}: step data must be string"
                timeout = _get_yaml_comment(step, action, "timeout")
                assert (
                    timeout is None
                ) or timeout.isdigit(), f"{test_name}: timeout value must be integer"
                script_item = (
                    action,
                    data,
                    int(timeout) if timeout is not None else None,
                )
                test_body["script"].append(script_item)

        returns = test_body.get("return")
        if returns is not None:
            assert isinstance(
                returns, int
            ), f"{test_name}: return value must be integer"

        points = test_body.get("points")
        if points is not None:
            assert isinstance(
                points, (int, float)
            ), f"{test_name}: points value must be numeric"
            total_points += test_body["points"]

        blocker = test_body.get("blocker")
        if blocker is not None:
            assert isinstance(
                blocker, bool
            ), f"{test_name}: blocker must be true or false"

        visible = test_body.get("visible")
        if visible is not None:
            assert isinstance(
                visible, bool
            ), f"{test_name}: visible must be true or false"

    return OrderedDict(tests), total_points


def run_script(command, script):
    """Run a command and check whether it follows a script.

    :sig: (str, List[Tuple[str, str, Optional[int]]]) -> Tuple[int, List[str]]
    :param command: Command to run.
    :param script: Script to follow.
    :return: Exit status and errors.
    """
    process = pexpect.spawn(command)
    process.setecho(False)
    errors = []
    for action, data, timeout in script:
        if action == "expect":
            pattern = pexpect.EOF if data == "_EOF_" else data
            try:
                _logger.debug(
                    "  expecting%s: %s",
                    " (%ss)" % timeout if timeout is not None else "",
                    data,
                )
                process.expect(pattern, timeout=timeout)
                received = "_EOF_" if ".EOF" in repr(process.after) else process.after
                _logger.debug("  received: %s", received)
            except pexpect.EOF:
                received = "_EOF_" if ".EOF" in repr(process.before) else process.before
                _logger.debug("  received: %s", received)
                process.close(force=True)
                _logger.debug("FAILED: Expected output not received.")
                errors.append("Expected output not received.")
                break
            except pexpect.TIMEOUT:
                received = "_EOF_" if ".EOF" in repr(process.before) else process.before
                _logger.debug("  received: %s", received)
                process.close(force=True)
                _logger.debug("FAILED: Timeout exceeded.")
                errors.append("Timeout exceeded.")
                break
        elif action == "send":
            _logger.debug("  sending: %s", data)
            process.sendline(data)
    else:
        process.close(force=True)
    return process.exitstatus, errors


def run_test(test, *, jailed=False):
    """Run a test and produce a report.

    :sig: (Mapping[str, Any], Optional[bool]) -> Mapping[str, Union[str, List[str]]]
    :param test: Test to run.
    :param jailed: Whether to jail the command to the current directory.
    :return: Result report of the test.
    """
    report = {"errors": []}

    command = test["run"]
    if jailed:
        command = "fakechroot chroot %(root)s %(command)s" % {
            "root": os.getcwd(),
            "command": command,
        }
    _logger.debug("running command: %s", command)

    script = test.get("script")
    exit_status, errors = run_script(command, script)

    report["errors"].extend(errors)

    expected_status = test.get("return", 0)
    if exit_status != expected_status:
        report["errors"].append("Incorrect exit status.")

    return report


def run_spec(tests, *, quiet=False):
    """Run a test suite specification.

    :sig: (Mapping[str, Any], bool) -> Mapping[str, Any]
    :param tests: Test specifications to run.
    :param quiet: Whether to suppress progress messages.
    :return: A report containing the results.
    """
    report = OrderedDict()
    earned_points = 0

    os.environ["TERM"] = "dumb"  # disable color output in terminal

    for test_name, test in tests.items():
        _logger.debug("starting test %s", test_name)
        visible = test.get("visible", True)
        if (not quiet) and visible:
            dots = "." * (MAX_LEN - len(test_name) + 1)
            print(f"{test_name} {dots}", end=" ")

        jailed = SUPPORTS_JAIL and test_name.startswith("case_")
        report[test_name] = run_test(test, jailed=jailed)
        passed = len(report[test_name]["errors"]) == 0

        points = test.get("points")
        if points is None:
            if (not quiet) and visible:
                print("PASSED" if passed else "FAILED")
        else:
            report[test_name]["points"] = points if passed else 0
            earned_points += report[test_name]["points"]
            if (not quiet) and visible:
                scored = report[test_name]["points"]
                print(f"{scored} / {points}")

        blocker = test.get("blocker", False)
        if blocker and (not passed):
            break

    report["points"] = earned_points
    return report


def make_parser(prog):
    """Build a parser for command-line arguments.

    :param prog: Name of program.
    """
    parser = ArgumentParser(prog=prog)
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")

    parser.add_argument("spec", help="test specifications file")
    parser.add_argument(
        "-d", "--directory", help="change to directory before doing anything"
    )
    parser.add_argument(
        "--validate", action="store_true", help="don't run tests, just validate spec"
    )
    parser.add_argument("--quiet", action="store_true", help="disable most messages")
    parser.add_argument("--log", action="store_true", help="create a log file")
    parser.add_argument(
        "--debug", action="store_true", help="enable debugging messages"
    )
    return parser


def setup_logging(*, debug, log):
    """Set up logging levels and handlers.

    :sig: (bool, bool) -> None
    :param debug: Whether to activate debugging.
    :param log: Whether to activate logging.
    """
    _logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # stream handler for console messages
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    _logger.addHandler(stream_handler)

    if log:
        # force debug mode
        _logger.setLevel(logging.DEBUG)

        # file handler for logging messages
        file_handler = logging.FileHandler("log.txt")
        file_handler.setLevel(logging.DEBUG)
        _logger.addHandler(file_handler)


def main(argv=None):
    """Entry point of the utility.

    :sig: (Optional[List[str]]) -> None
    :param argv: Command line arguments.
    """
    argv = argv if argv is not None else sys.argv
    parser = make_parser(prog="calico")
    arguments = parser.parse_args(argv[1:])

    try:
        spec_filename = os.path.abspath(arguments.spec)
        with open(spec_filename) as f:
            content = f.read()

        if arguments.directory is not None:
            os.chdir(arguments.directory)

        setup_logging(debug=arguments.debug, log=arguments.log)

        tests, total_points = parse_spec(content)

        if not arguments.validate:
            report = run_spec(tests, quiet=arguments.quiet)
            scored = report["points"]
            print(f"Grade: {scored} / {total_points}")
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

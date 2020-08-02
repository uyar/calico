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

"""Command line interface."""

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import os
import sys
from argparse import ArgumentParser
from calico import __version__
from calico.parse import parse_spec
from calico.base import Clioc

_logger = logging.getLogger("calico")

LOG_FILENAME = "calico.log"


def make_parser(prog):
    """Build a parser for command line arguments.

    :sig: (str) -> ArgumentParser
    :param prog: Name of program.
    :return: Created argument parser.
    """
    parser = ArgumentParser(prog=prog)
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    parser.add_argument(
        "-g", "--generate-test-file", nargs="+",
        help="generate a test file from run(s)")
    parser.add_argument("spec", help="test specifications file")
    parser.add_argument("-d", "--directory", help="change to directory before doing anything")
    parser.add_argument(
        "--validate", action="store_true", help="don't run tests, just validate spec"
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="disable most messages")
    parser.add_argument("--log", action="store_true", help="log messages to file")
    parser.add_argument("--debug", action="store_true", help="enable debug messages")
    parser.add_argument("-t", "--tests", nargs="+", help="specify which tests cases will run")
    parser.add_argument(
        "--timeout", type=int, help="default timeout value for all test cases (seconds)"
    )
    return parser


def setup_logging(debug, log):
    """Set up logging levels and handlers.

    :sig: (bool, bool) -> None
    :param debug: Whether to activate debugging.
    :param log: Whether to log messages to a file.
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
        file_handler = logging.FileHandler(LOG_FILENAME)
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
        if arguments.generate_test_file:
            test_suite_generator = Clioc(arguments.generate_test_file)
            with open(spec_filename, "w") as f:
                f.write(test_suite_generator.generate_test_spec())
            print("A test file named '%s' has been generated." % arguments.spec)
        with open(spec_filename) as f:
            content = f.read()

        if arguments.directory is not None:
            os.chdir(arguments.directory)

        setup_logging(debug=arguments.debug, log=arguments.log)

        runner = parse_spec(content)

        if not arguments.validate:
            report = runner.run(
                tests=arguments.tests, quiet=arguments.quiet, g_timeout=arguments.timeout
            )
            score = report["points"]
            print("Grade: %(s)s / %(p)s" % {"s": score, "p": runner.points})
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

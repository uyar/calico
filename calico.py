# Copyright (C) 2016-2017 H. Turgut Uyar <uyar@itu.edu.tr>
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

from argparse import ArgumentParser
from collections import OrderedDict
from ruamel import yaml

import logging
import os
import pexpect
import shutil
import sys


MAX_LEN = 40
SUPPORTS_JAIL = shutil.which('fakechroot') is not None

_logger = logging.getLogger(__name__)


def _get_comment(node, name, field):
    try:
        comment = node.ca.items[name][2].value[1:].strip()  # remove the hash from the start
    except KeyError:
        comment = None
    if (comment is not None) and comment.startswith(field + ':'):
        return comment[len(field)+1:].strip()
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
        raise AssertionError('No configuration')

    total_points = 0
    tests = [(k, v) for c in config for k, v in c.items()]
    for test_name, test in tests:
        run = test.get('run')
        assert run is not None, test_name + ': no run command'
        assert isinstance(run, str), test_name + ': run command must be string'

        script = test.get('script')
        if script is None:
            timeout = _get_comment(test, 'run', 'timeout')
            assert (timeout is None) or timeout.isdigit(), \
                test_name + ': timeout value must be integer'
            script_item = ('expect', '_EOF_', int(timeout) if timeout is not None else None)
            test['script'] = [script_item]
        else:
            test['script'] = []
            for step in script:
                action, data = [(k, v) for k, v in step.items()][0]
                assert action in ('expect', 'send'), test_name + ': invalid action type'
                assert isinstance(data, str), test_name + ': step data must be string'
                timeout = _get_comment(step, action, 'timeout')
                assert (timeout is None) or timeout.isdigit(), \
                    test_name + ': timeout value must be integer'
                script_item = (action, data, int(timeout) if timeout is not None else None)
                test['script'].append(script_item)

        returns = test.get('return')
        if returns is not None:
            assert isinstance(returns, int), test_name + ': return value must be integer'

        points = test.get('points')
        if points is not None:
            assert isinstance(points, (int, float)), \
                test_name + ': points value must be numeric'
            total_points += test['points']

        blocker = test.get('blocker')
        if blocker is not None:
            assert isinstance(blocker, bool), test_name + ': blocker must be true or false'

        visible = test.get('visible')
        if visible is not None:
            assert isinstance(visible, bool), test_name + ': visible must be true or false'

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
        if action == 'expect':
            pattern = pexpect.EOF if data == '_EOF_' else data
            try:
                _logger.debug('  expecting%s: %s',
                              ' (%ss)' % timeout if timeout is not None else '', data)
                process.expect(pattern, timeout=timeout)
                received = '_EOF_' if '.EOF' in repr(process.after) else process.after
                _logger.debug('  received: %s', received)
            except pexpect.EOF:
                received = '_EOF_' if '.EOF' in repr(process.before) else process.before
                _logger.debug('  received: %s', received)
                process.close(force=True)
                _logger.debug('FAILED: Expected output not received.')
                errors.append('Expected output not received.')
                break
            except pexpect.TIMEOUT:
                received = '_EOF_' if '.EOF' in repr(process.before) else process.before
                _logger.debug('  received: %s', received)
                process.close(force=True)
                _logger.debug('FAILED: Timeout exceeded.')
                errors.append('Timeout exceeded.')
                break
        elif action == 'send':
            _logger.debug('  sending: %s', data)
            process.sendline(data)
    else:
        process.close(force=True)
    return process.exitstatus, errors


def run_test(test, jailed=False):
    """Run a test and produce a report.

    :sig: (Mapping[str, List[str]], Optional[bool]) -> Mapping[str, Union[str, List[str]]]
    :param test: Test to run.
    :param jailed: Whether to jail the command to the current directory.
    :return: Result report of the test.
    """
    report = {'errors': []}

    command = test['run']
    if jailed:
        command = 'fakechroot chroot %(root)s %(command)s' % {
            'root': os.getcwd(),
            'command': command
        }
    _logger.debug('running command: %s', command)

    script = test.get('script')
    exit_status, errors = run_script(command, script)

    report['errors'].extend(errors)

    expected_status = test.get('return', 0)
    if exit_status != expected_status:
        report['errors'].append('Incorrect exit status.')

    return report


def run_spec(tests, quiet=False):
    """Run a test suite specification.

    :sig: (Mapping[str, Any], bool) -> Mapping[str, Any]
    :param tests: Test specifications to run.
    :param quiet: Whether to suppress progress messages.
    :return: A report containing the results.
    """
    report = OrderedDict()
    earned_points = 0

    os.environ['TERM'] = 'dumb'     # disable color output in terminal

    for test_name, test in tests.items():
        _logger.debug('starting test %s', test_name)
        visible = test.get('visible', True)
        if (not quiet) and visible:
            lead = '%(name)s %(dots)s ' % {
                'name': test_name,
                'dots': '.' * (MAX_LEN - len(test_name) + 1)
            }
            print(lead, end='')

        jailed = SUPPORTS_JAIL and test_name.startswith('case_')
        report[test_name] = run_test(test, jailed=jailed)
        passed = len(report[test_name]['errors']) == 0

        points = test.get('points')
        if points is None:
            if (not quiet) and visible:
                tail = 'PASSED' if passed else 'FAILED'
                print(tail)
        else:
            report[test_name]['points'] = points if passed else 0
            earned_points += report[test_name]['points']
            if (not quiet) and visible:
                tail = '%(scored)d / %(over)d' % {
                    'scored': report[test_name]['points'],
                    'over': points
                }
                print(tail)

        blocker = test.get('blocker', False)
        if blocker and (not passed):
            break

    report['points'] = earned_points
    return report


def _get_parser(prog):
    """Get a parser for command-line arguments.

    :sig: (str) -> ArgumentParser
    :param prog: Name of program.
    """
    parser = ArgumentParser(prog=prog)
    parser.add_argument('spec', help='test specifications file')
    parser.add_argument('-d', '--directory', help='change to directory before doing anything')
    parser.add_argument('--validate', action='store_true',
                        help='don\'t run tests, just validate spec')
    parser.add_argument('--quiet', action='store_true', help='disable most messages')
    parser.add_argument('--log', action='store_true', help='create a log file')
    parser.add_argument('--debug', action='store_true', help='enable debugging messages')
    return parser


def _setup_logging(debug, log):
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
        file_handler = logging.FileHandler('log.txt')
        file_handler.setLevel(logging.DEBUG)
        _logger.addHandler(file_handler)


def main(argv=None):
    """Entry point of the utility.

    :sig: (Optional[List[str]]) -> None
    :param argv: Command line arguments.
    """
    argv = argv if argv is not None else sys.argv
    parser = _get_parser(prog=argv[0])
    arguments = parser.parse_args(argv[1:])

    try:
        spec_filename = os.path.abspath(arguments.spec)
        with open(spec_filename) as f:
            content = f.read()

        if arguments.directory is not None:
            os.chdir(arguments.directory)

        _setup_logging(arguments.debug, arguments.log)

        tests, total_points = parse_spec(content)

        if not arguments.validate:
            report = run_spec(tests, quiet=arguments.quiet)
            summary = 'Grade: %(scored)d / %(over)d' % {
                'scored': report['points'],
                'over': total_points
            }
            print(summary)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

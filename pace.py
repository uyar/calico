# Copyright (C) 2016-2017 H. Turgut Uyar <uyar@itu.edu.tr>
#
# Pace is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pace is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pace.  If not, see <http://www.gnu.org/licenses/>.

from argparse import ArgumentParser
from collections import OrderedDict
from ruamel import yaml

import logging
import os
import pexpect
import shutil
import sys


MAX_LEN = 40

_logger = logging.getLogger(__name__)


def parse_spec(source):
    """Parse a test specification.

    :sig: (str) -> Tuple[Mapping[str, Any], Union[int, float]]
    :param source: Specification to parse.
    :return: Validated tests and total points.
    :raises AssertionError: When given source is invalid.
    """
    try:
        config = yaml.round_trip_load('--- !!omap\n' + source if source else source)
    except yaml.YAMLError as e:
        raise AssertionError(str(e))

    if config is None:
        raise AssertionError('No configuration')

    total_points = 0
    for test_name, test in config.items():
        run = test.get('run')
        assert run is not None, test_name + ': no run command'
        assert isinstance(run, str), test_name + ': run command must be string'

        script = test.get('script')
        if script is None:
            test['script'] = [('expect', 'EOF')]
        else:
            test['script'] = [(k, v) for s in script for k, v in s.items()]
            for action, data in test['script']:
                assert action in ('expect', 'send'), test_name + ': invalid action type'
                assert isinstance(data, str), test_name + ': step data must be string'

        returns = test.get('return')
        if returns is not None:
            assert isinstance(returns, int), test_name + ': return value must be an integer'

        points = test.get('points')
        if points is not None:
            assert isinstance(points, (int, float)), \
                test_name + ': points value must be numeric'
            total_points += test['points']

        blocker = test.get('blocker')
        if blocker is not None:
            assert blocker in ('yes', 'no'), test_name + ': blocker value must be yes or no'
            test['blocker'] = blocker == 'yes'

    return config, total_points


def run_script(command, script):
    """Run a command and check whether it follows a script.

    :sig: (str, List[str]) -> Tuple[int, List[str]]
    :param command: Command to run.
    :param script: Script to follow.
    :return: Exit status and errors.
    """
    process = pexpect.spawn(command)
    process.setecho(False)
    errors = []
    for step_name, step_data in script:
        if step_name == 'expect':
            lhs, *rhs = [s.strip() for s in step_data[0].split('# timeout:')]
            pattern = pexpect.EOF if lhs == 'EOF' else lhs[1:-1]    # remove the quotes
            timeout = int(rhs[0].strip()) if len(rhs) > 0 else None
            try:
                _logger.debug('  expecting (timeout: %2ss): %s', timeout, lhs)
                process.expect(pattern, timeout=timeout)
                _logger.debug('  received                : %s', process.after)
            except (pexpect.TIMEOUT, pexpect.EOF):
                _logger.debug('received: %s', process.before)
                process.close(force=True)
                _logger.debug('FAILED: Expected output not received.')
                errors.append('Expected output not received.')
                break
        elif step_name == 'send':
            user_input = step_data[0].strip()[1:-1]     # remove the quotes
            _logger.debug('  sending: %s', user_input)
            process.sendline(user_input)
    else:
        process.close(force=True)
    return process.exitstatus, errors


def run_test(test):
    """Run a test and produce a report.

    :sig: (Mapping[str, List[str]]) -> Mapping[str, Union[str, List[str]]]
    :param test: Test to run.
    :return: Result report of the test.
    """
    report = {'errors': []}

    command = test['run']
    _logger.debug('running command: %s', command)

    chroot = test.get('chroot')
    if chroot is not None:
        root = chroot[0]
        _logger.debug('changing root: %s', root)
        if os.path.exists(root):
            shutil.rmtree(root)
        shutil.copytree('.', root)
        command = 'fakechroot chroot %(root)s %(command)s' % {
            'root': root,
            'command': command
        }

    script = test.get('script')
    exit_status, errors = run_script(command, script)

    report['errors'].extend(errors)

    expected_status = test.get('return', 0)
    if exit_status != expected_status:
        report['errors'].append('Incorrect exit status.')

    if chroot is not None:
        root = chroot[0]
        if os.path.exists(root):
            shutil.rmtree(root)

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
        if not quiet:
            lead = '%(name)s %(dots)s ' % {
                'name': test_name,
                'dots': '.' * (MAX_LEN - len(test_name) + 1)
            }
            print(lead, end='')

        report[test_name] = run_test(test)
        passed = len(report[test_name]['errors']) == 0

        points = test.get('points')
        if points is None:
            if not quiet:
                tail = 'PASSED' if passed else 'FAILED'
                print(tail)
        else:
            report[test_name]['points'] = points if passed else 0
            earned_points += report[test_name]['points']
            if not quiet:
                tail = '%(scored)3d / %(over)3d' % {
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

    _setup_logging(arguments.debug, arguments.log)

    try:
        if arguments.directory is not None:
            os.chdir(arguments.directory)

        spec_filename = os.path.abspath(arguments.spec)
        with open(spec_filename) as f:
            content = f.read()

        tests, total_points = parse_spec(content)

        if not arguments.validate:
            report = run_spec(tests, quiet=arguments.quiet)
            summary = 'Grade: %(scored)3d / %(over)3d' % {
                'scored': report['points'],
                'over': total_points
            }
            print(summary)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

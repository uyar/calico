# Copyright (C) 2016-2017 H. Turgut Uyar <uyar@itu.edu.tr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from argparse import ArgumentParser
from collections import OrderedDict

import logging
import os
import pexpect
import rsonlite
import shutil
import sys


ENCODING = 'utf-8'
MAX_LEN = 40

_logger = logging.getLogger(__name__)


def parse_spec(source):
    """Parse a test specification.

    :sig: (str) -> Mapping[str, Any]
    :param source: Specification to parse.
    :return: Parsed specification.
    """
    loaded = rsonlite.loads(source)

    tests = OrderedDict()
    spec = {'tests': tests}

    total_points = 0

    for test_name, test_data in loaded:
        test = OrderedDict(test_data)

        assert 'run' in test, test_name + ': no run command'
        assert len(test['run']) == 1, test_name + ': multiple run commands'
        test['run'] = test['run'][0]

        assert 'script' in test, test_name + ': no script'
        # assert len(test['script']) == 1, test_name + ': multiple scripts'
        for step_name, step_data in test['script']:
            assert step_name in ('expect', 'send'), test_name + ': invalid action type'
            assert len(step_data) == 1, test_name + ': multiple step data'

        returns = test.get('return')
        if returns is not None:
            assert len(returns) == 1, test_name + ': multiple returns values'
            assert returns[0].isdigit(), test_name + ': non-numeric returns value'
            test['return'] = int(returns[0])

        points = test.get('points')
        if points is not None:
            assert len(points) == 1, test_name + ': multiple points values'
            assert points[0].isdigit(), test_name + ': non-numeric points value'
            test['points'] = int(points[0])
            total_points += test['points']

        blocker = test.get('blocker')
        if blocker is not None:
            assert len(blocker) == 1, test_name + ': multiple blocker settings'
            assert blocker[0] in ('yes', 'no'), test_name + ': incorrect blocker value'
            test['blocker'] = blocker[0] == 'yes'

        if test_name in ('init', 'cleanup'):
            spec[test_name] = test
        else:
            tests[test_name] = test

    spec['total_points'] = total_points
    return spec


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
    report = {}
    report['errors'] = []

    command, *rhs = test['run'].split('# timeout:')
    timeout = int(rhs[0].strip()) if len(rhs) > 0 else None
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


def run_spec(spec, quiet=False):
    """Run a test suite specification.

    :sig: (Mapping[str, Any], bool) -> Mapping[str, Any]
    :param spec: Test specifications to run.
    :param quiet: Whether to suppress progress messages.
    :return: A report containing the results.
    """
    report = OrderedDict()
    earned_points = 0

    os.environ['TERM'] = 'dumb'     # prevent color output in terminal

    init = spec.get('init')
    if init is not None:
        _logger.debug('running init actions')
        run_test(init)

    for test_name, test in spec['tests'].items():
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

    cleanup = spec.get('cleanup')
    if cleanup is not None:
        _logger.debug('running cleanup actions')
        run_test(cleanup)

    report['points'] = earned_points
    report['total_points'] = spec['total_points']
    return report


def _get_parser():
    parser = ArgumentParser()
    parser.add_argument('spec',
                        help='test specifications file')
    parser.add_argument('-d', '--directory',
                        help='change to directory before doing anything')
    parser.add_argument('--validate', action='store_true',
                        help='don\'t run tests, just validate spec')
    parser.add_argument('--quiet', action='store_true',
                        help='disable most messages')
    parser.add_argument('--log', action='store_true',
                        help='create a log file')
    parser.add_argument('--debug', action='store_true',
                        help='enable debugging messages')
    return parser


def _setup_logging(debug, log):
    _logger.setLevel(logging.DEBUG if debug else logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    _logger.addHandler(handler)

    if debug:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        _logger.addHandler(handler)

    if log:
        _logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler('log.txt')
        handler.setLevel(logging.DEBUG)
        _logger.addHandler(handler)


def main():
    """Entry point of the utility.

    :sig: () -> None
    """
    parser = _get_parser()
    arguments = parser.parse_args()

    spec_filename = os.path.abspath(arguments.spec)

    if arguments.directory is not None:
        os.chdir(arguments.directory)

    _setup_logging(arguments.debug, arguments.log)

    with open(spec_filename, encoding=ENCODING) as f:
        content = f.read()

    try:
        spec = parse_spec(content)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    if not arguments.validate:
        report = run_spec(spec, quiet=arguments.quiet)
        summary = 'Grade: %(scored)3d / %(over)3d' % {
            'scored': report['points'],
            'over': report['total_points']
        }
        print(summary)


if __name__ == '__main__':
    main()

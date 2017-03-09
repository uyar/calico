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


ENCODING = 'utf-8'

_logger = logging.getLogger(__name__)


def validate_spec(spec):
    for test_name, test_data in spec:
        test = OrderedDict(test_data)

        assert 'run' in test, (test_name, 'no run command')
        assert len(test['run']) == 1, (test_name, 'multiple run commands')

        points = test.get('points')
        if points is not None:
            assert len(points) == 1, (test_name, 'multiple points values')
            assert points[0].isdigit(), (test_name, 'non-numeric points value')

        timeout = test.get('timeout')
        if timeout is not None:
            assert len(timeout) == 1, (test_name, 'multiple timeout values')
            assert timeout[0].isdigit(), (test_name, 'non-numeric timeout value')

        blocker = test.get('blocker')
        if blocker is not None:
            assert len(blocker) == 1, (test_name, 'multiple blocker settings')
            assert blocker[0] in ('yes', 'no'), (test_name, 'incorrect blocker value')

        script = test.get('script')
        if script is not None:
            for step_name, step_data in script:
                assert step_name in ('expect', 'send'), (test_name, 'invalid action type')
                assert len(step_data) == 1, (test_name, 'multiple step data')

        returns = test.get('return')
        if returns is not None:
            assert len(returns) == 1, (test_name, 'multiple returns values')
            assert returns[0].isdigit(), (test_name, 'non-numeric returns value')


def execute_command(command, timeout=None):
    """Run the command and return the results.

    :sig: (str, Optional[int]) -> Tuple[str, int, bool]
    :param command: Command to run.
    :param timeout: How long to wait for command to finish, in seconds.
    :return: Outputs, exit status, and whether the command has timed out or not.
    """
    process = pexpect.spawn(command)
    try:
        process.expect(pexpect.EOF, timeout=timeout)
        timed_out = False
    except pexpect.TIMEOUT:
        timed_out = True
    finally:
        process.close(force=True)
    return process.before, process.exitstatus, timed_out


def run_spec(spec, quiet=False):
    # XXX: This function assumes that the spec is valid.
    report = OrderedDict()

    tests = OrderedDict([(test_name, OrderedDict(test_data))
                         for test_name, test_data in spec])

    points = [t.get('points') for _, t in tests.items()]
    total_points = sum([int(p[0]) for p in points if p is not None])

    # max_len = max([len(t) for t in tests])
    max_len = 40

    os.environ['TERM'] = 'dumb'

    for test_name, test in tests.items():
        if not quiet:
            print(test_name, end='')
        report[test_name] = {}

        command, *rhs = test['run'][0].split(':timeout:')
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
        if script is None:
            # if there is no script, assume that the command is not interactive
            # run it and wait for it to finish
            outputs, exit_status, timed_out = execute_command(command, timeout=timeout)
            report[test_name]['outputs'] = outputs
            if timed_out:
                report[test_name]['error'] = 'Time out.'
            else:
                expected_status = int(test.get('return', ['0'])[0])
                if exit_status != expected_status:
                    report[test_name]['error'] = 'Incorrect exit status.'
        else:
            process = pexpect.spawn(command)
            process.setecho(False)

            for step_name, step_data in script:
                if step_name == 'expect':
                    p, t = [s.strip() for s in step_data[0].split(':timeout:')]
                    pattern = pexpect.EOF if p == 'EOF' else p.encode(ENCODING)[1:-1]
                    timeout = int(t)
                    try:
                        _logger.debug('  expecting (timeout: %2ss): %s', timeout, pattern)
                        process.expect(pattern, timeout=timeout)
                        _logger.debug('  received                : %s', process.after)
                    except (pexpect.TIMEOUT, pexpect.EOF):
                        _logger.debug('received: %s', process.before)
                        process.close(force=True)
                        _logger.debug('FAILED: Expected output not received.')
                        report[test_name]['error'] = 'Expected output not received.'
                        break
                elif step_name == 'send':
                    raw_input = step_data[0].strip()[1:-1]
                    _logger.debug('  sending: %s', raw_input)
                    process.sendline(raw_input)
            process.close()
            exit_status = process.exitstatus

            return_code = int(test.get('return', ['0'])[0])
            if exit_status != return_code:
                report[test_name]['error'] = 'Incorrect exit status.'

        if chroot is not None:
            root = chroot[0]
            if os.path.exists(root):
                shutil.rmtree(root)

        if not quiet:
            print(' ' + '.' * (max_len - len(test_name) + 1) + ' ', end='')
        points = test.get('points')
        if points is None:
            if not quiet:
                print('PASSED') if 'error' not in report[test_name] else 'FAILED'
            report[test_name]['points'] = 0
        else:
            p = int(points[0])
            report[test_name]['points'] = p if 'error' not in report[test_name] else 0
            if not quiet:
                print('%2d/%2d' % (report[test_name]['points'], p))

        blocker = test.get('blocker', ['no'])[0] == 'yes'
        if blocker and ('error' in report[test_name]):
            break

    report['total'] = sum([t['points'] for _, t in report.items()])
    report['total_points'] = total_points
    return report


def main():
    parser = ArgumentParser()
    parser.add_argument('spec', help='test specifications file')
    parser.add_argument('-d', '--directory',
                        help='change to directory before doing anything')
    parser.add_argument('--validate', action='store_true',
                        help='validate only, no run')
    parser.add_argument('--quiet', action='store_true',
                        help='disable most messages')
    parser.add_argument('--log', action='store_true',
                        help='create a log file')
    parser.add_argument('--debug', action='store_true',
                        help='enable debugging messages')
    arguments = parser.parse_args()

    spec_filename = os.path.abspath(arguments.spec)

    if arguments.directory is not None:
        os.chdir(arguments.directory)

    _logger.setLevel(logging.DEBUG if arguments.debug else logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    _logger.addHandler(handler)

    if arguments.debug:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        _logger.addHandler(handler)

    if arguments.log:
        _logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler('log.txt')
        handler.setLevel(logging.DEBUG)
        _logger.addHandler(handler)

    with open(spec_filename, encoding=ENCODING) as f:
        spec = rsonlite.loads(f.read())

    if arguments.validate:
        try:
            validate_spec(spec)
        except AssertionError as e:
            print('test: %s, error: %s' % e.args[0])
    else:
        report = run_spec(spec, quiet=arguments.quiet)
        print('Grade: %3d/%3d' % (report['total'], report['total_points']))


if __name__ == '__main__':
    main()

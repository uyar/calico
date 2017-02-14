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
from collections import OrderedDict, namedtuple

import logging
import os
import pexpect
import rsonlite


ENCODING = 'utf-8'

_logger = logging.getLogger(__name__)


def validate_spec(spec):
    for test_name, test_data in spec:
        test = OrderedDict(test_data)
        assert 'run' in test, (test_name, 'no run command')
        assert len(test['run']) == 1, (test_name, 'multiple run commands')
        timeout = test.get('timeout')
        if timeout is not None:
            assert len(timeout) == 1, (test_name, 'multiple timeout values')
            assert timeout[0].isdigit(), (test_name, 'non-numeric timeout value')
        blocker = test.get('blocker')
        if blocker is not None:
            assert len(blocker) == 1, (test_name, 'multiple blocker settings')
            assert blocker[0] in ('yes', 'no'), (test_name, 'incorrect blocker value')
        script = test.get('script')
        for step_name, step_data in script:
            if step_name in ('expect', 'send'):
                assert len(step_data) == 1, (test_name, 'multiple step data')


ExecutionSummary = namedtuple('ExecutionSummary',
                              ['timed_out', 'outputs', 'exit_status'])


def execute_command(command, timeout=None):
    os.environ['TERM'] = 'dumb'
    try:
        process = pexpect.spawn(command)
        process.expect(pexpect.EOF, timeout=timeout)
        timed_out = False
    except pexpect.TIMEOUT:
        timed_out = True
    finally:
        process.close(force=True)
    return ExecutionSummary(timed_out, process.before, process.exitstatus)


def run_spec(spec, quiet=False):
    # XXX: This function assumes that the spec is valid.
    report = OrderedDict()
    
    tests = OrderedDict([(test_name, OrderedDict(test_data))
                         for test_name, test_data in spec])

    points = [t.get('points') for _, t in tests.items()]
    total_points = sum([int(p[0]) for p in points if p is not None])

    # max_len = max([len(t) for t in tests])
    max_len = 40

    for test_name, test in tests.items():
        if not quiet:
            print(test_name, end='')
        report[test_name] = {}
        
        command = test['run'][0]
        _logger.debug('running command: %s', command)

        script = test.get('script')
        if script is None:
            # if there is no script, assume that the command is not interactive
            # run it and wait for it to finish
            t = test.get('timeout')
            timeout = int(t[0]) if t is not None else None
            summary = execute_command(command, timeout=timeout)
            report[test_name]['outputs'] = summary.outputs
            if summary.timed_out:
                report[test_name]['error'] = 'Time out.'
            else:
                expected_status = int(test.get('return', ['0'])[0])
                if summary.exit_status != expected_status:
                    report[test_name]['error'] = 'Incorrect exit status.'
        else:
            process = pexpect.spawn(command)
            process.setecho(False)

            for step_name, step_data in script:
                if step_name == 'expect':
                    p, t = step_data[0].split(',')
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
                    raw_input = step_data[0]
                    _logger.debug('  sending: %s', raw_input)
                    process.sendline(raw_input)
            process.close()
            exit_status = process.exitstatus

            return_code = int(test.get('return', ['0'])[0])
            if exit_status != return_code:
                report[test_name]['error'] = 'Incorrect exit status.'

        if not quiet:
            print(' ' + '.' * (max_len - len(test_name) + 1) + ' ', end='')
        points = test.get('points')
        if points is None:  
            if not quiet:
                print('PASSED') if 'error' not in report[test_name] else 'FAILED'
            report[test_name]['points'] = 0
        else:
            p = int(points[0])
            report[test_name]['points'] = p
            if not quiet:
                print('%2d/%2d' % (p, p) if 'error' not in report[test_name] else '%2d/%2d' % (0, p))

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

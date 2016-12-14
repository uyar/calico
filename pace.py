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


ExecutionSummary = namedtuple('ExecutionSummary',
                              ['timed_out', 'outputs', 'exit_status'])


def execute_command(command, timeout=None):
    os.environ['TERM'] = 'dumb'
    try:
        _logger.info('running command: %s', command)
        process = pexpect.spawn(command)
        process.expect(pexpect.EOF, timeout=timeout)
        timed_out = False
    except pexpect.TIMEOUT:
        timed_out = True
    finally:
        process.close(force=True)
    return ExecutionSummary(timed_out, process.before, process.exitstatus)


def run_spec(spec):
    # XXX: This function assumes that the spec is valid.

    report = OrderedDict()
    for test_name, test_data in spec:
        _logger.info('test: %s', test_name)
        report[test_name] = {}
        test = OrderedDict(test_data)

        command = test['run'][0]
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
            _logger.debug('running command: %s', command)
            process = pexpect.spawn(command)
            process.setecho(False)

            for step_name, step_data in script:
                if step_name == 'expect':
                    assert len(step_data) == 1
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
                        _logger.info('FAILED: Expected output not received.')
                        report[test_name]['error'] = 'Expected output not received.'
                        break
                elif step_name == 'send':
                    assert len(step_data) == 1
                    raw_input = step_data[0]
                    _logger.debug('  sending: %s', raw_input)
                    process.sendline(raw_input)
            process.close()
            exit_status = process.exitstatus

            return_code = int(test.get('return', ['0'])[0])
            if exit_status != return_code:
                report[test_name]['error'] = 'Incorrect exit status.'

        if not 'error' in report[test_name]:
            _logger.info('PASSED')

        blocker = test.get('blocker', ['no'])[0] == 'yes'
        if blocker and ('error' in report[test_name]):
            break

    return report



def main():
    parser = ArgumentParser()
    parser.add_argument('spec', help='test specifications file')
    parser.add_argument('--validate', action='store_true',
                        help='validate only, no run')
    parser.add_argument('--quiet', action='store_true',
                        help='disable most messages')
    parser.add_argument('--debug', action='store_true',
                        help='enable debugging messages')
    arguments = parser.parse_args()

    if arguments.quiet:
        log_level = logging.CRITICAL
    elif arguments.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(message)s')

    with open(arguments.spec, encoding=ENCODING) as f:
        spec = rsonlite.loads(f.read())

    if arguments.validate:
        try:
            validate_spec(spec)
        except AssertionError as e:
            print('test: %s, error: %s' % e.args[0])
    else:
        report = run_spec(spec)
        print(report)


if __name__ == '__main__':
    main()

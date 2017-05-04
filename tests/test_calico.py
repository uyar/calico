from calico import run_script


def test_script_expect_eof_should_be_ok():
    result = run_script('true', [('expect', '_EOF_', None)])
    assert result == (0, [])


def test_script_expect_output_should_be_ok():
    result = run_script('echo 1', [('expect', '1', None), ('expect', '_EOF_', None)])
    assert result == (0, [])


def test_script_expect_with_timeout_should_be_ok():
    result = run_script('sleep 1', [('expect', '_EOF_', 2)])
    assert result == (0, [])


def test_script_expect_with_exceeded_timeout_should_report_error():
    result = run_script('sleep 2', [('expect', '_EOF_', 1)])
    assert result == (None, ['Timeout exceeded.'])


def test_script_expect_with_unmatched_output_should_report_error():
    result = run_script('true', [('expect', '1', None)])
    assert result == (0, ['Expected output not received.'])


# def test_script_expect_with_extra_output_should_report_error():
#     result = run_script('echo 1', [('expect', '_EOF_', None)])
#     assert result == (0, ['Extra output received.'])


def test_script_send_input_should_be_ok():
    result = run_script('bash -c "read x && echo $x"',
                        [('send', '1', None), ('expect', '1', None)])
    assert result == (0, [])


def test_timeout_should_kill_infinite_program():
    result = run_script('yes', [('expect', '_EOF_', 1)])
    assert result == (None, ['Timeout exceeded.'])

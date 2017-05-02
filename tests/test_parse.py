from pytest import raises

from pace import parse_spec


def test_empty_content_should_raise_error():
    with raises(AssertionError):
        parse_spec('')


def test_invalid_format_should_raise_error():
    with raises(AssertionError):
        parse_spec('!dummy')


def test_case_with_run_command_should_be_ok():
    config, _ = parse_spec('- c0:\n    run: ls')
    assert config['c0']['run'] == 'ls'


def test_case_without_run_command_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec('- c0:\n    return: 1')
    assert 'no run command' in str(e)


def test_case_with_multiple_run_commands_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec('- c0:\n    run:\n     - 1\n     - 2\n')
    assert 'run command must be string' in str(e)


def test_case_with_no_script_should_expect_eof():
    config, _ = parse_spec('- c0:\n    run: ls')
    assert config['c0']['script'] == [('expect', 'EOF')]


def test_case_with_invalid_script_action_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec('- c0:\n    run: ls\n    script:\n     - wait: 1\n')
    assert 'invalid action type' in str(e)


def test_case_with_action_with_multiple_data_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec('- c0:\n    run: ls\n    script:\n     - send: [\'1\', \'2\']\n')
    assert 'step data must be string' in str(e)


def test_case_with_action_with_non_quoted_data_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec('- c0:\n    run: ls\n    script:\n     - expect: 1\n')
    assert 'step data must be string' in str(e)


def test_case_with_integer_return_value_should_be_ok():
    config, _ = parse_spec('- c0:\n    run: ls\n    return: 1')
    assert config['c0']['return'] == 1


def test_case_with_non_integer_return_value_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec('- c0:\n    run: ls\n    return: EOF\n')
    assert 'return value must be an integer' in str(e)


def test_case_with_numeric_points_value_should_be_ok():
    config, _ = parse_spec('- c0:\n    run: ls\n    points: 1.5\n')
    assert config['c0']['points'] == 1.5


def test_case_with_non_numeric_points_value_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec('- c0:\n    run: ls\n    points: EOF\n')
    assert 'points value must be numeric' in str(e)


def test_case_with_set_blocker_value_should_be_ok():
    config, _ = parse_spec('- c0:\n    run: ls\n    blocker: yes\n')
    assert config['c0']['blocker']


def test_case_with_unset_blocker_value_should_be_ok():
    config, _ = parse_spec('- c0:\n    run: ls\n    blocker: no\n')
    assert not config['c0']['blocker']


def test_case_with_non_boolean_blocker_value_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec('- c0:\n    run: ls\n    blocker: maybe\n')
    assert 'blocker value must be yes or no' in str(e)


def test_total_points_should_be_correctly_computed():
    source = """
      - c0:
          run: ls
          points: 15
      - c1:
          run: ls
          points: 25
    """
    _, total_points = parse_spec(source)
    assert total_points == 40

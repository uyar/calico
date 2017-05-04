from pytest import raises

from calico import parse_spec


def test_empty_spec_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec('')
    assert 'No configuration' in str(e)


def test_invalid_spec_format_should_raise_error():
    with raises(AssertionError):
        parse_spec('!dummy')


def test_case_with_run_command_should_be_ok():
    source = """
      - c1:
          run: echo 1
    """
    config, _ = parse_spec(source)
    assert config['c1']['run'] == 'echo 1'


def test_case_without_run_command_should_raise_error():
    source = """
      - c1:
          return: 1
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'no run command' in str(e)


def test_case_with_multiple_run_commands_should_raise_error():
    source = """
      - c1:
          run:
            - echo 1a
            - echo 1b
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'run command must be string' in str(e)


def test_case_with_no_script_should_expect_eof():
    source = """
      - c1:
          run: echo 1
    """
    config, _ = parse_spec(source)
    assert config['c1']['script'] == [('expect', '_EOF_', None)]


def test_case_script_with_invalid_action_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - wait: 1
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'invalid action type' in str(e)


def test_case_script_with_string_action_data_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: '1'
    """
    config, _ = parse_spec(source)
    assert config['c1']['script'] == [('expect', '1', None)]


def test_case_script_with_numeric_action_data_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 1
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'step data must be string' in str(e)


def test_case_script_with_action_data_eof_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: _EOF_
    """
    config, _ = parse_spec(source)
    assert config['c1']['script'] == [('expect', '_EOF_', None)]


def test_case_script_with_multiple_action_data_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - send:
                - '1a'
                - '1b'
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'step data must be string' in str(e)


def test_case_script_order_should_be_preserved():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 'foo'
            - send: '1'
            - expect: _EOF_
    """
    config, _ = parse_spec(source)
    assert config['c1']['script'] == [('expect', 'foo', None), ('send', '1', None),
                                      ('expect', '_EOF_', None)]


def test_case_script_action_with_integer_timeout_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 'foo' # timeout: 5
    """
    config, _ = parse_spec(source)
    assert config['c1']['script'] == [('expect', 'foo', 5)]


def test_case_script_action_with_fractional_timeout_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 'foo' # timeout: 4.5
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'timeout value must be integer' in str(e)


def test_case_script_action_with_string_timeout_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 'foo' # timeout: '5'
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'timeout value must be integer' in str(e)


def test_case_run_with_timeout_should_generate_expect_eof_with_timeout():
    source = """
      - c1:
          run: echo 1 # timeout: 5
    """
    config, _ = parse_spec(source)
    assert config['c1']['script'] == [('expect', '_EOF_', 5)]


def test_case_run_with_non_numeric_timeout_value_should_raise_error():
    source = """
      - c1:
          run: echo 1 # timeout: '5'
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'timeout value must be integer' in str(e)


def test_case_integer_return_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          return: 0
    """
    config, _ = parse_spec(source)
    assert config['c1']['return'] == 0


def test_case_fractional_return_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          return: 1.5
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'return value must be integer' in str(e)


def test_case_string_return_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          return: '0'
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'return value must be integer' in str(e)


def test_case_integer_points_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          points: 10
    """
    config, _ = parse_spec(source)
    assert config['c1']['points'] == 10


def test_case_fractional_points_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          points: 1.5
    """
    config, _ = parse_spec(source)
    assert config['c1']['points'] == 1.5


def test_case_non_numeric_points_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          points: '10'
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'points value must be numeric' in str(e)


def test_case_blocker_set_should_be_ok():
    source = """
      - c1:
          run: echo 1
          blocker: true
    """
    config, _ = parse_spec(source)
    assert config['c1']['blocker']


def test_case_blocker_unset_should_be_ok():
    source = """
      - c1:
          run: echo 1
          blocker: false
    """
    config, _ = parse_spec(source)
    assert not config['c1']['blocker']


def test_case_non_boolean_blocker_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          blocker: maybe
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'blocker must be true or false' in str(e)


def test_case_visible_set_should_be_ok():
    source = """
      - c1:
          run: echo 1
          visible: true
    """
    config, _ = parse_spec(source)
    assert config['c1']['visible']


def test_case_visible_unset_should_be_ok():
    source = """
      - c1:
          run: echo 1
          visible: false
    """
    config, _ = parse_spec(source)
    assert not config['c1']['visible']


def test_case_non_boolean_visibility_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          visible: maybe
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'visible must be true or false' in str(e)


def test_case_order_should_be_preserved():
    source = """
      - c2:
          run: echo 2
      - c3:
          run: echo 3
      - c1:
          run: echo 1
    """
    config, _ = parse_spec(source)
    assert [k for k in config] == ['c2', 'c3', 'c1']


def test_total_points_should_be_sum_of_points():
    source = """
      - c1:
          run: echo 1
          points: 15
      - c2:
          run: echo 2
      - c3:
          run: echo 3
          points: 25
    """
    _, total_points = parse_spec(source)
    assert total_points == 40


def test_no_total_points_given_should_sum_zero():
    source = """
      - c1:
          run: echo 1
      - c2:
          run: echo 2
    """
    _, total_points = parse_spec(source)
    assert total_points == 0

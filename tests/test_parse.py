from pytest import raises

from pace import parse_spec


def test_empty_content_should_raise_error():
    with raises(AssertionError):
        parse_spec('')


def test_invalid_format_should_raise_error():
    with raises(AssertionError):
        parse_spec('!dummy')


def test_case_with_run_command_should_be_ok():
    source = """
      - c0:
          run: ls
    """
    config, _ = parse_spec(source)
    assert config['c0']['run'] == 'ls'


def test_case_without_run_command_should_raise_error():
    source = """
      - c0:
          return: 1
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'no run command' in str(e)


def test_case_with_multiple_run_commands_should_raise_error():
    source = """
      - c0:
          run:
            - ls
            - ls
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'run command must be string' in str(e)


def test_case_order_should_be_preserved():
    source = """
      - c1:
          run: ls
      - c2:
          run: ls
      - c0:
          run: ls
    """
    config, _ = parse_spec(source)
    assert [k for k in config] == ['c1', 'c2', 'c0']


def test_case_with_no_script_should_expect_eof():
    source = """
      - c0:
          run: ls
    """
    config, _ = parse_spec(source)
    assert config['c0']['script'] == [('expect', 'EOF')]


def test_case_with_invalid_script_action_should_raise_error():
    source = """
      - c0:
          run: ls
          script:
            - wait: 1
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'invalid action type' in str(e)


def test_case_with_action_with_multiple_data_should_raise_error():
    source = """
      - c0:
          run: ls
          script:
            - send:
                - '1'
                - '2'
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'step data must be string' in str(e)


def test_case_with_action_with_numeric_data_should_raise_error():
    source = """
      - c0:
          run: ls
          script:
            - expect: 1
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'step data must be string' in str(e)


def test_case_script_order_should_be_preserved():
    source = """
      - c0:
          run: ls
          script:
            - expect: 'Foo'
            - send: '1'
            - expect: EOF
    """
    config, _ = parse_spec(source)
    assert config['c0']['script'] == [('expect', 'Foo'), ('send', '1'), ('expect', 'EOF')]


def test_case_with_integer_return_value_should_be_ok():
    config, _ = parse_spec('- c0:\n    run: ls\n    return: 1')
    assert config['c0']['return'] == 1


def test_case_with_non_integer_return_value_should_raise_error():
    source = """
      - c0:
          run: ls
          return: 1.5
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'return value must be an integer' in str(e)


def test_case_with_numeric_points_value_should_be_ok():
    source = """
      - c0:
          run: ls
          points: 1.5
    """
    config, _ = parse_spec(source)
    assert config['c0']['points'] == 1.5


def test_case_with_non_numeric_points_value_should_raise_error():
    source = """
      - c0:
          run: ls
          points: EOF
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'points value must be numeric' in str(e)


def test_case_with_set_blocker_value_should_be_ok():
    source = """
      - c0:
          run: ls
          blocker: yes
    """
    config, _ = parse_spec(source)
    assert config['c0']['blocker']


def test_case_with_unset_blocker_value_should_be_ok():
    source = """
      - c0:
          run: ls
          blocker: no
    """
    config, _ = parse_spec(source)
    assert not config['c0']['blocker']


def test_case_with_non_boolean_blocker_value_should_raise_error():
    source = """
      - c0:
          run: ls
          blocker: maybe
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert 'blocker value must be yes or no' in str(e)


def test_total_points_should_be_sum_of_points():
    source = """
      - c0:
          run: ls
          points: 15
      - c1:
          run: ls
      - c2:
          run: ls
          points: 25
    """
    _, total_points = parse_spec(source)
    assert total_points == 40


def test_total_points_none_should_be_zero():
    source = """
      - c0:
          run: ls
      - c1:
          run: ls
    """
    _, total_points = parse_spec(source)
    assert total_points == 0

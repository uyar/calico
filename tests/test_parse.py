from pytest import mark, raises

from calico import Suite


def test_empty_spec_should_raise_error():
    with raises(AssertionError) as e:
        Suite("")
    assert "No configuration" in str(e)


def test_invalid_spec_format_should_raise_error():
    with raises(AssertionError):
        Suite("!dummy")


def test_case_with_run_command_should_be_ok():
    source = """
      - c1:
          run: echo 1
    """
    suite = Suite(source)
    assert suite["c1"].command == "echo 1"


def test_case_without_run_command_should_raise_error():
    source = """
      - c1:
          return: 1
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "no run command" in str(e)


def test_case_with_multiple_run_commands_should_raise_error():
    source = """
      - c1:
          run:
            - echo 1a
            - echo 1b
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "run command must be a string" in str(e)


def test_case_with_no_script_should_expect_eof():
    source = """
      - c1:
          run: echo 1
    """
    suite = Suite(source)
    assert [s.as_tuple() for s in suite["c1"].script] == [("e", "_EOF_", 0)]


def test_case_script_with_invalid_action_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - wait: 1
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "unknown action type" in str(e)


def test_case_script_with_string_action_data_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: "1"
    """
    suite = Suite(source)
    assert [s.as_tuple() for s in suite["c1"].script] == [("e", "1", 0)]


def test_case_script_with_numeric_action_data_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 1
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "action data must be string" in str(e)


def test_case_script_with_action_data_eof_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: _EOF_
    """
    suite = Suite(source)
    assert [s.as_tuple() for s in suite["c1"].script] == [("e", "_EOF_", 0)]


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
        Suite(source)
    assert "action data must be string" in str(e)


def test_case_script_order_should_be_preserved():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 'foo'
            - send: '1'
            - expect: _EOF_
    """
    suite = Suite(source)
    assert [s.as_tuple() for s in suite["c1"].script] == [
        ("e", "foo", 0),
        ("s", "1", 0),
        ("e", "_EOF_", 0),
    ]


def test_case_script_action_with_integer_timeout_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 'foo' # timeout: 5
    """
    suite = Suite(source)
    assert [s.as_tuple() for s in suite["c1"].script] == [("e", "foo", 5)]


def test_case_script_action_with_fractional_timeout_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 'foo' # timeout: 4.5
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "timeout must be integer" in str(e)


def test_case_script_action_with_string_timeout_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 'foo' # timeout: '5'
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "timeout must be integer" in str(e)


@mark.skip
def test_case_run_with_timeout_should_generate_expect_eof_with_timeout():
    source = """
      - c1:
          run: echo 1 # timeout: 5
    """
    suite = Suite(source)
    assert [s.as_tuple() for s in suite["c1"].script] == [("e", "_EOF_", 5)]


def test_case_run_with_non_numeric_timeout_value_should_raise_error():
    source = """
      - c1:
          run: echo 1 # timeout: '5'
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "timeout must be integer" in str(e)


def test_case_integer_return_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          return: 0
    """
    suite = Suite(source)
    assert suite["c1"].returns == 0


def test_case_fractional_return_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          return: 1.5
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "return value must be integer" in str(e)


def test_case_string_return_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          return: '0'
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "return value must be integer" in str(e)


def test_case_integer_points_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          points: 10
    """
    suite = Suite(source)
    assert suite["c1"].points == 10


@mark.skip
def test_case_fractional_points_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          points: 1.5
    """
    suite = Suite(source)
    assert suite["c1"].points == 1.5


def test_case_non_numeric_points_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          points: '10'
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "points must be integer" in str(e)


def test_case_blocker_set_to_true_should_be_ok():
    source = """
      - c1:
          run: echo 1
          blocker: true
    """
    suite = Suite(source)
    assert suite["c1"].blocker


def test_case_blocker_set_to_false_should_be_ok():
    source = """
      - c1:
          run: echo 1
          blocker: false
    """
    suite = Suite(source)
    assert not suite["c1"].blocker


def test_case_non_boolean_blocker_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          blocker: maybe
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "blocker must be true or false" in str(e)


def test_case_visible_set_to_true_should_be_ok():
    source = """
      - c1:
          run: echo 1
          visible: true
    """
    suite = Suite(source)
    assert suite["c1"].visible


def test_case_visible_set_to_false_should_be_ok():
    source = """
      - c1:
          run: echo 1
          visible: false
    """
    suite = Suite(source)
    assert not suite["c1"].visible


def test_case_non_boolean_visibility_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          visible: maybe
    """
    with raises(AssertionError) as e:
        Suite(source)
    assert "visible must be true or false" in str(e)


def test_case_order_should_be_preserved():
    source = """
      - c2:
          run: echo 2
      - c3:
          run: echo 3
      - c1:
          run: echo 1
    """
    suite = Suite(source)
    assert [k for k in suite] == ["c2", "c3", "c1"]


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
    suite = Suite(source)
    assert suite.points == 40


def test_no_total_points_given_should_sum_zero():
    source = """
      - c1:
          run: echo 1
      - c2:
          run: echo 2
    """
    suite = Suite(source)
    assert suite.points == 0

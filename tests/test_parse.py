from pytest import raises

from calico.parse import parse_spec


def test_empty_spec_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec("")
    assert "No test specification" in str(e)


def test_invalid_spec_format_should_raise_error():
    with raises(AssertionError) as e:
        parse_spec("!dummy")
    assert "Invalid test specification" in str(e)


def test_case_with_run_command_should_be_ok():
    source = """
      - c1:
          run: echo 1
    """
    runner = parse_spec(source)
    assert runner["c1"].command == "echo 1"


def test_case_with_run_shortcut_should_be_ok():
    source = """
      - c1:
          r: echo 1
    """
    runner = parse_spec(source)
    assert runner["c1"].command == "echo 1"


def test_case_order_should_be_preserved():
    source = """
      - c2:
          run: echo 2
      - c3:
          run: echo 3
      - c1:
          run: echo 1
    """
    runner = parse_spec(source)
    assert list(runner.keys()) == ["c2", "c3", "c1"]


def test_case_without_run_command_should_raise_error():
    source = """
      - c1:
          exit: 1
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "No run command" in str(e)


def test_case_with_multiple_run_commands_should_raise_error():
    source = """
      - c1:
          run:
            - echo 1a
            - echo 1b
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Run command must be a string" in str(e)


def test_case_default_exit_status_should_be_zerd():
    source = """
      - c1:
          run: echo 1
    """
    runner = parse_spec(source)
    assert runner["c1"].exits == 0


def test_case_integer_exit_status_should_be_ok():
    source = """
      - c1:
          run: echo 1
          exit: 2
    """
    runner = parse_spec(source)
    assert runner["c1"].exits == 2


def test_case_fractional_exit_status_should_raise_error():
    source = """
      - c1:
          run: echo 1
          exit: 1.5
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Exit status value must be an integer" in str(e)


def test_case_string_exit_status_should_raise_error():
    source = """
      - c1:
          run: echo 1
          exit: "0"
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Exit status value must be an integer" in str(e)


def test_case_exit_shortcut_should_be_ok():
    source = """
      - c1:
          r: echo 1
          x: 2
    """
    runner = parse_spec(source)
    assert runner["c1"].exits == 2


def test_case_default_points_value_should_be_none():
    source = """
      - c1:
          run: echo 1
    """
    runner = parse_spec(source)
    assert runner["c1"].points is None


def test_case_integer_points_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          points: 10
    """
    runner = parse_spec(source)
    assert runner["c1"].points == 10


def test_case_fractional_points_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          points: 1.5
    """
    runner = parse_spec(source)
    assert runner["c1"].points == 1.5


def test_case_non_numeric_points_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          points: "10"
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Points value must be numeric" in str(e)


def test_case_points_shortcut_should_be_ok():
    source = """
      - c1:
          run: echo 1
          p: 10
    """
    runner = parse_spec(source)
    assert runner["c1"].points == 10


def test_case_default_blocker_value_should_be_false():
    source = """
      - c1:
          run: echo 1
    """
    runner = parse_spec(source)
    assert not runner["c1"].blocker


def test_case_blocker_set_to_true_should_be_ok():
    source = """
      - c1:
          run: echo 1
          blocker: true
    """
    runner = parse_spec(source)
    assert runner["c1"].blocker


def test_case_blocker_set_to_false_should_be_ok():
    source = """
      - c1:
          run: echo 1
          blocker: false
    """
    runner = parse_spec(source)
    assert not runner["c1"].blocker


def test_case_non_boolean_blocker_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          blocker: maybe
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Blocker value must be true or false" in str(e)


def test_case_blocker_shortcut_should_be_ok():
    source = """
      - c1:
          run: echo 1
          b: true
    """
    runner = parse_spec(source)
    assert runner["c1"].blocker


def test_case_default_visibility_value_should_be_true():
    source = """
      - c1:
          run: echo 1
    """
    runner = parse_spec(source)
    assert runner["c1"].visible


def test_case_visible_set_to_true_should_be_ok():
    source = """
      - c1:
          run: echo 1
          visible: true
    """
    runner = parse_spec(source)
    assert runner["c1"].visible


def test_case_visible_set_to_false_should_be_ok():
    source = """
      - c1:
          run: echo 1
          visible: false
    """
    runner = parse_spec(source)
    assert not runner["c1"].visible


def test_case_non_boolean_visibility_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          visible: maybe
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Visibility value must be true or false" in str(e)


def test_case_visibility_shortcut_should_be_ok():
    source = """
      - c1:
          run: echo 1
          v: true
    """
    runner = parse_spec(source)
    assert runner["c1"].visible


def test_case_with_no_script_should_expect_eof():
    source = """
      - c1:
          run: echo 1
    """
    runner = parse_spec(source)
    assert [tuple(s) for s in runner["c1"].script] == [("e", "_EOF_", None)]


def test_case_run_with_timeout_should_generate_expect_eof_with_timeout():
    source = """
      - c1:
          run: echo 1 # timeout: 5
    """
    runner = parse_spec(source)
    assert [tuple(s) for s in runner["c1"].script] == [("e", "_EOF_", 5)]


def test_case_run_with_non_numeric_timeout_value_should_raise_error():
    source = """
      - c1:
          run: echo 1 # timeout: "5"
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Timeout value must be an integer" in str(e)


def test_case_script_with_invalid_action_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - wait: 1
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Unknown action type" in str(e)


def test_case_script_with_string_action_data_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: "1"
    """
    runner = parse_spec(source)
    assert [tuple(s) for s in runner["c1"].script] == [("e", "1", None)]


def test_case_script_with_numeric_action_data_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: 1
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Action data must be a string" in str(e)


def test_case_script_with_action_data_eof_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: _EOF_
    """
    runner = parse_spec(source)
    assert [tuple(s) for s in runner["c1"].script] == [("e", "_EOF_", None)]


def test_case_script_with_multiple_action_data_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - send:
                - "1a"
                - "1b"
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Action data must be a string" in str(e)


def test_case_script_with_expect_shortcut_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - e: "1"
    """
    runner = parse_spec(source)
    assert [tuple(s) for s in runner["c1"].script] == [("e", "1", None)]


def test_case_script_with_send_shortcut_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - s: "1"
    """
    runner = parse_spec(source)
    assert [tuple(s) for s in runner["c1"].script] == [("s", "1", None)]


def test_case_script_order_should_be_preserved():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: "foo"
            - send: "1"
            - expect: _EOF_
    """
    runner = parse_spec(source)
    assert [tuple(s) for s in runner["c1"].script] == [
        ("e", "foo", None),
        ("s", "1", None),
        ("e", "_EOF_", None),
    ]


def test_case_script_action_with_integer_timeout_value_should_be_ok():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: "foo" # timeout: 5
    """
    runner = parse_spec(source)
    assert [tuple(s) for s in runner["c1"].script] == [("e", "foo", 5)]


def test_case_script_action_with_fractional_timeout_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: "foo" # timeout: 4.5
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Timeout value must be an integer" in str(e)


def test_case_script_action_with_string_timeout_value_should_raise_error():
    source = """
      - c1:
          run: echo 1
          script:
            - expect: "foo" # timeout: "5"
    """
    with raises(AssertionError) as e:
        parse_spec(source)
    assert "Timeout value must be an integer" in str(e)


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
    runner = parse_spec(source)
    assert runner.points == 40


def test_total_fractional_points_should_be_sum_of_points():
    source = """
      - c1:
          run: echo 1
          points: 1.5
      - c2:
          run: echo 2
      - c3:
          run: echo 3
          points: 2.25
    """
    runner = parse_spec(source)
    assert runner.points == 3.75


def test_no_total_points_given_should_sum_zero():
    source = """
      - c1:
          run: echo 1
      - c2:
          run: echo 2
    """
    runner = parse_spec(source)
    assert runner.points == 0


def test_case_define_variable_should_be_ok():
    source = """
      - _define:
          vars:
            foo: bar
    """
    runner = parse_spec(source)
    assert runner["_define_vars"]["foo"] == "bar"

from pytest import raises

from pace import parse_spec


def test_invalid_format_should_raise_error():
    with raises(ValueError):
        parse_spec('dummy')


def test_empty_content_should_generate_basic_data():
    assert parse_spec('') == {'tests': {}, 'total_points': 0}


def test_case_without_run_should_raise_error():
    with raises(AssertionError):
        parse_spec('case_0\n return = 1')

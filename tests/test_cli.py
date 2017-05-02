from pytest import raises

from unittest.mock import mock_open, patch

import os

import pace


base_dir = os.path.dirname(__file__)
demo_dir = os.path.join(base_dir, '..', 'demo')
circle_spec_file = os.path.join(demo_dir, 'circle.t')


def test_help_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        pace.main(argv=['pace', '--help'])
    out, err = capsys.readouterr()
    assert out.startswith('usage: ')


def test_no_spec_file_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        pace.main(argv=['pace'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'required: spec' in err


def test_existing_spec_file_should_be_ok(capsys):
    pace.main(argv=['pace', circle_spec_file])
    out, err = capsys.readouterr()
    assert err == ''


def test_valid_spec_file_should_be_validated(capsys):
    pace.main(argv=['pace', '--validate', circle_spec_file])
    out, err = capsys.readouterr()
    assert out == ''


def test_invalid_spec_file_should_raise_error(capsys):
    with patch('builtins.open', mock_open(read_data='dummy'), create=True):
        with raises(SystemExit):
            pace.main(argv=['pace', '--validate', circle_spec_file])
        out, err = capsys.readouterr()
        assert 'too many values' in err

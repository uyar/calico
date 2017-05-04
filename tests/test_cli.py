from pytest import raises

from unittest.mock import mock_open, patch

import os

import calico


base_dir = os.path.dirname(__file__)
circle_spec_file = os.path.join(base_dir, 'circle.yaml')


def test_help_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        calico.main(argv=['calico', '--help'])
    out, err = capsys.readouterr()
    assert out.startswith('usage: ')


def test_no_spec_file_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        calico.main(argv=['calico'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'required: spec' in err


def test_existing_spec_file_should_be_ok(capsys):
    calico.main(argv=['calico', circle_spec_file])
    out, err = capsys.readouterr()
    assert err == ''


def test_non_existing_spec_file_should_exit_with_error(capsys):
    with raises(SystemExit):
        calico.main(argv=['calico', 'dummy.spec'])
    out, err = capsys.readouterr()
    assert 'No such file or directory:' in err


# TODO: add tests for -d option


def test_non_existing_base_directory_should_exit_with_error(capsys):
    with raises(SystemExit):
        calico.main(argv=['calico', '-d', 'dummy', circle_spec_file])
    out, err = capsys.readouterr()
    assert 'No such file or directory:' in err


def test_validate_valid_spec_file_should_not_print_output(capsys):
    calico.main(argv=['calico', '--validate', circle_spec_file])
    out, err = capsys.readouterr()
    assert out == ''


def test_validate_invalid_spec_file_should_exit_with_error(capsys):
    with patch('builtins.open', mock_open(read_data=''), create=True):
        with raises(SystemExit):
            calico.main(argv=['calico', '--validate', circle_spec_file])
        out, err = capsys.readouterr()
        assert 'No configuration' in err


# TODO: add tests for --quiet option


# TODO: add tests for --log option


# TODO: add tests for --debug option


# TODO: add tests for summary output

from pytest import raises

import pace


def test_help_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        pace.main(argv=['pace', '--help'])
    out, err = capsys.readouterr()
    assert out.startswith('usage: ')

# Copyright (C) 2016-2018 H. Turgut Uyar <uyar@itu.edu.tr>
#
# Calico is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Calico is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Calico.  If not, see <http://www.gnu.org/licenses/>.

"""Specification parsing."""

from __future__ import absolute_import, division, print_function, unicode_literals

from ruamel import yaml
from ruamel.yaml import comments

from .base import Action, ActionType, Calico, TestCase


# sigalias: SpecNode = comments.CommentedMap


def get_comment_value(node, name, field):
    """Get the value of a comment field.

    :sig: (SpecNode, str, str) -> str
    :param node: Node to get the comment from.
    :param name: Name of setting in the node.
    :param field: Name of comment field.
    :return: Value of comment field.
    """
    try:
        comment = node.ca.items[name][2].value[1:].strip()  # remove the leading hash
    except KeyError:
        comment = None
    if comment is not None:
        delim = field + ":"
        if comment.startswith(delim):
            return comment[len(delim) :].strip()
    return None


def get_attribute(node, test_name, names, val_func, val_args, err_message):
    """Get the value of an test attribute.

    :sig: (SpecNode, str, Tuple[str], Callable[[Any, ...], bool], Any, str) -> Any
    :param node: Node to get the attribute
    :param test_name: Name of the test
    :param names: Long and short names of the attribute
    :param val_func: A validator function for the attribute
    :param val_args: An argument to the validator function
    :param err_message: An error message to shown when validation fails
    """
    _short, _long = names
    attr = node.get(_long, node.get(_short))
    if attr is not None:
        if val_args is None:
            result = val_func(attr)
        else:
            result = val_func(attr, val_args)

        assert result, err_message % test_name
    return attr


def parse_spec(content):
    """Parse a test specification.

    :sig: (str) -> Calico
    :param content: Specification to parse.
    :return: Created Calico runner.
    :raise AssertionError: When given specification is invalid.
    """
    try:
        spec = yaml.round_trip_load(content)
    except yaml.YAMLError as e:
        raise AssertionError(str(e))

    if spec is None:
        raise AssertionError("No test specification")

    if not isinstance(spec, comments.CommentedSeq):
        raise AssertionError("Invalid test specification")

    action_types = {i: m for m in ActionType for i in m.value}

    runner = Calico()

    tests = [(n, t) for c in spec for n, t in c.items()]
    attributes = [
        (
            "command",
            {
                "names": ("r", "run"),
                "val_func": isinstance,
                "val_args": str,
                "err_message": "%s: Run command must be a string",
            },
        ),
        (
            "points",
            {
                "names": ("p", "points"),
                "val_func": isinstance,
                "val_args": (int, float),
                "err_message": "%s: Points value must be numeric",
            },
        ),
        (
            "blocker",
            {
                "names": ("b", "blocker"),
                "val_func": isinstance,
                "val_args": bool,
                "err_message": "%s: Blocker value must be true or false",
            },
        ),
        (
            "exits",
            {
                "names": ("x", "exit"),
                "val_func": isinstance,
                "val_args": int,
                "err_message": "%s: Exit status value must be an integer",
            },
        ),
        (
            "visible",
            {
                "names": ("v", "visible"),
                "val_func": isinstance,
                "val_args": bool,
                "err_message": "%s: Visibility value must be true or false",
            },
        ),
    ]

    for test_name, test in tests:
        if test_name[0] == "_":
            for section, section_value in test.items():
                runner[test_name + "_" + section] = section_value
            continue

        kwargs = {}
        for kwarg, attr in attributes:
            attr_ = get_attribute(test, test_name, **attr)
            if attr_ is not None:
                kwargs[kwarg] = attr_

        assert "command" in kwargs, "%(t)s: No run command" % {"t": test_name}

        timeout = get_comment_value(test, name="run", field="timeout")
        if timeout is not None:
            assert timeout.isdigit(), "%(t)s: Timeout value must be an integer" % {
                "t": test_name
            }
            kwargs["timeout"] = int(timeout)

        case = TestCase(test_name, **kwargs)

        script = test.get("script")
        if script is None:
            # If there's no script, just expect EOF.
            action = Action(ActionType.EXPECT, "_EOF_", timeout=case.timeout)
            case.add_action(action)
        else:
            for step in script:
                action_type, data = [(k, v) for k, v in step.items()][0]
                assert action_type in action_types, "%(t)s: Unknown action type" % {
                    "t": test_name
                }
                assert isinstance(data, str), "%(t)s: Action data must be a string" % {
                    "t": test_name
                }

                kwargs = {}

                timeout = get_comment_value(step, name=action_type, field="timeout")
                if timeout is not None:
                    assert timeout.isdigit(), "%(t)s: Timeout value must be an integer" % {
                        "t": test_name
                    }
                    kwargs["timeout"] = int(timeout)

                action = Action(action_types[action_type], data, **kwargs)
                case.add_action(action)

        runner.add_case(case)

    return runner

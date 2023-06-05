"""Tests for parsing puml files
"""
import flatdict
from test_event_generator.io.parse_puml import get_graph_defs_from_puml


def test_get_graph_defs_from_puml_ANDFork_loop(
    ANDFork_loop_puml: str,
    ANDFork_loop_graph_def: dict[str, dict]
) -> None:
    """Tests `get_graph_defs_from_puml` for an AND fork with nested loop

    :param ANDFork_loop_puml: Fixture providing raw puml file string
    :type ANDFork_loop_puml: `str`
    :param ANDFork_loop_graph_def: Fixture providing the expected graph
    definition that is equivalent to the puml
    :type ANDFork_loop_graph_def: `dict`[`str`, `dict`]
    """
    graph_defs = get_graph_defs_from_puml(ANDFork_loop_puml)
    assert len(graph_defs) == 1
    assert "ANDFork_loop_a" in graph_defs
    produced_graph_def = graph_defs["ANDFork_loop_a"]
    # check the keys are the same
    assert len(ANDFork_loop_graph_def) == len(produced_graph_def)
    assert not set(produced_graph_def.keys()).difference(
        set(ANDFork_loop_graph_def.keys())
    )
    # loop over keys and check basic equivalency
    for key, expected_event_def in ANDFork_loop_graph_def.items():
        produced_event_def = produced_graph_def[key]
        check_event_def_equivalency(
            expected_event_def,
            produced_event_def
        )


def test_get_graph_defs_from_puml_bunched_xor(
    bunched_xor_puml: str,
    bunched_xor_graph_def: dict[str, dict]
) -> None:
    """Tests `get_graph_defs_from_puml` for XOR groups bunched on one event

    :param bunched_xor_puml: Fixture providing raw puml file string
    :type bunched_xor_puml: `str`
    :param bunched_xor_graph_def: Fixture providing the expected graph
    definition that is equivalent to the puml
    :type bunched_xor_graph_def: `dict`[`str`, `dict`]
    """
    graph_defs = get_graph_defs_from_puml(bunched_xor_puml)
    assert len(graph_defs) == 1
    assert "bunched_XOR_switch" in graph_defs
    produced_graph_def = graph_defs["bunched_XOR_switch"]
    # check the keys are the same
    assert len(bunched_xor_graph_def) == len(produced_graph_def)
    assert not set(produced_graph_def.keys()).difference(
        set(bunched_xor_graph_def.keys())
    )
    # loop over keys and check basic equivalency
    for key, expected_event_def in bunched_xor_graph_def.items():
        produced_event_def = produced_graph_def[key]
        check_event_def_equivalency(
            expected_event_def,
            produced_event_def
        )


def test_get_graph_defs_from_puml_loop_loop(
    loop_loop_puml: str,
    loop_loop_graph_def: dict[str, dict]
) -> None:
    """Tests `get_graph_defs_from_puml` for an loop with nested loop

    :param loop_loop_puml: Fixture providing raw puml file string
    :type loop_loop_puml: `str`
    :param loop_loop_graph_def: Fixture providing the expected graph
    definition that is equivalent to the puml
    :type loop_loop_graph_def: `dict`[`str`, `dict`]
    """
    graph_defs = get_graph_defs_from_puml(loop_loop_puml)
    assert len(graph_defs) == 1
    assert "loop_loop_a" in graph_defs
    produced_graph_def = graph_defs["loop_loop_a"]
    # check the keys are the same
    assert len(loop_loop_graph_def) == len(produced_graph_def)
    assert not set(produced_graph_def.keys()).difference(
        set(loop_loop_graph_def.keys())
    )
    # loop over keys and check basic equivalency
    for key, expected_event_def in loop_loop_graph_def.items():
        produced_event_def = produced_graph_def[key]
        check_event_def_equivalency(
            expected_event_def,
            produced_event_def
        )


def check_event_def_equivalency(
    event_def_1: dict,
    event_def_2: dict
) -> None:
    """Helper function to check if two evnet def dicts are equivalent

    :param event_def_1: The first event def dictionary
    :type event_def_1: `dict`
    :param event_def_2: The second event def dictionary
    :type event_def_2: `dict`
    """
    event_def_1_group_in = event_def_1["group_in"]
    event_def_2_group_in = event_def_2["group_in"]
    event_def_1_group_out = event_def_1["group_out"]
    event_def_2_group_out = event_def_2["group_out"]
    if event_def_1_group_in and event_def_2_group_in:
        check_group_equivalency(
            event_def_1_group_in,
            event_def_2_group_in
        )
    else:
        assert event_def_1_group_in == event_def_2_group_in
    if event_def_1_group_out and event_def_2_group_out:
        check_group_equivalency(
            event_def_1_group_out,
            event_def_2_group_out
        )
        pass
    else:
        assert event_def_1_group_out == event_def_2_group_out
    assert (
        event_def_1["meta_data"]["EventType"]
    ) == (
        event_def_2["meta_data"]["EventType"]
    )


def check_group_equivalency(
    group_def_1: dict,
    group_def_2: dict
) -> None:
    """Helper function to check that two group def dictionaries are equivalent

    :param group_def_1: The first group def dictionary
    :type group_def_1: `dict`
    :param group_def_2: The second group def dictionary
    :type group_def_2: `dict`
    """
    assert group_def_1["type"] == group_def_2["type"]
    sub_groups_1 = group_def_1["sub_groups"]
    sub_groups_2 = group_def_2["sub_groups"]
    assert len(sub_groups_1) == len(sub_groups_2)
    if all(
        isinstance(entry, str)
        for entry in sub_groups_1
    ) and all(
        isinstance(entry, str)
        for entry in sub_groups_2
    ):
        assert all(
            sub_group_1 == sub_group_2
            for sub_group_1, sub_group_2 in zip(
                sorted(sub_groups_1),
                sorted(sub_groups_2)
            )
        )
    else:
        flat_sub_group_1 = flatdict.FlatterDict(
            sub_groups_1
        )
        flat_sub_group_2 = flatdict.FlatterDict(
            sub_groups_2
        )
        for sub_1_item, sub_2_item in zip(
            sorted(flat_sub_group_1.items(), key=lambda item: item[1]),
            sorted(flat_sub_group_2.items(), key=lambda item: item[1])
        ):
            # check sorted values are the same
            assert sub_1_item[1] == sub_2_item[1]
            # check the value lies at the correct depth
            assert (
                len(sub_1_item[0].split(":"))
            ) == (
                len(sub_2_item[0].split(":"))
            )

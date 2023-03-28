# pylint: disable=redefined-outer-name
# pylint: disable=C0413
"""
PyTest fixtures for Test Event Generator
"""
from typing import Union

import pytest
from ortools.sat.python.cp_model import CpModel, CpSolver
from test_event_generator.core.edge import Edge
from test_event_generator.core.group import Group
from test_event_generator.graph import Graph


@pytest.fixture
def model() -> CpModel:
    """PyTest fixture to instantiate :class:`CpModel`.

    :return: CP-Sat Model
    :rtype: :class:`CpModel`
    """
    return CpModel()


@pytest.fixture
def solver():
    """PyTest fixture to instantiate :class:`CpSolver`.

    :return: CP-Sat Solver
    :rtype: :class:`CpModel`
    """
    return CpSolver()


@pytest.fixture
def sub_variables(model: CpModel) -> list[Union[Edge, Group]]:
    """PyTest fixture  that sets up a list of Groups and Edges for subsequent
    tests

    :param model: CP-SAT model
    :type model: :class:`CpModel`
    :return: A list of the Edges and Groups
    :rtype: `list`[:class:`Union`[class:`Edge`, class:`Group`]]
    """
    edge_1 = Edge(model, "edge_1")
    edge_2 = Edge(model, "edge_2")
    group_1 = Group(
        model=model,
        uid="group_1",
        group_variables=[],
        is_into_event=False
    )
    group_2 = Group(
        model=model,
        uid="group_2",
        group_variables=[],
        is_into_event=False
    )
    return [
        edge_1, edge_2, group_1, group_2
    ]


@pytest.fixture
def graph_def() -> dict[str, dict]:
    """Py-Test fixture that defines a standard graph definition.

    :return: Returns a standar graph definition
    :rtype: `dict`[`str`, `dict`]
    """
    json = {
        "Event_A": {
            "group_in": None,
            "group_out": {
                "type": "XOR",
                "sub_groups": [
                    "edge_A_B",
                    {
                        "type": "AND",
                        "sub_groups": [
                            "edge_A_C",
                            "edge_A_D"
                        ]
                    }
                ]
            },
        },
        "Event_B": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_A_B"
                ]
            },
            "group_out": None
        },
        "Event_C": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_A_C"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "edge_C_E"
                ]
            }
        },
        "Event_D": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_A_D"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "edge_D_E"
                ]
            }
        },
        "Event_E": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_C_E",
                    "edge_D_E"
                ]
            },
            "group_out": None
        }
    }
    return json


@pytest.fixture
def edges() -> list[str]:
    """Py-Test fixture to define a list of edge uids that corresponds to the
    edge uids found in the above graph definition.

    :return: _description_
    :rtype: `list`[`str`]
    """
    edges_uids = [
        "edge_A_B",
        "edge_A_C",
        "edge_A_D",
        "edge_C_E",
        "edge_D_E"
    ]
    return edges_uids


@pytest.fixture
def parsed_graph(graph_def: dict[str, dict]) -> Graph:
    """PyTest fixture that provides a :class:`Graph` instance that has has the
    fixture graph_def parsed by the instance.

    :param graph_def: Standard graph definition.
    :type graph_def: `dict`[`str`, `dict`]
    :return: Returns the :class:`Graph` instance containing the parsed
    graph_def.
    :rtype: :class:`Graph`
    """
    graph = Graph()
    graph.parse_graph_def(graph_def)
    return graph


@pytest.fixture
def expected_solutions() -> list[dict[str, int]]:
    """Py-Test fixture that defines the event solutions for the above graph
    definition.

    :return: Returns a list of dictionaries that hold the event solutions for
    two distinct solution paths.
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "Event_A": 1,
            "Event_B": 1,
            "Event_C": 0,
            "Event_D": 0,
            "Event_E": 0,
        },
        {
            "Event_A": 1,
            "Event_B": 0,
            "Event_C": 1,
            "Event_D": 1,
            "Event_E": 1,
        },
    ]


@pytest.fixture
def expected_group_solutions() -> dict[int, dict[str, int]]:
    """Py-Test fixture to define the expected group defined solutions of the
    above graph definition.

    :return: Returns the expected group solutions as a dictionary of
    dictionaries with each entry of the dictionary a distinct solution.
    :rtype: `dict`[`int`, `dict`[`str`, `int`]]
    """
    return {
        0: {
            "Event_A.out": 1,
            "Event_B.in": 1,
            "Event_C.in": 0,
            "Event_C.out": 0,
            "Event_D.in": 0,
            "Event_D.out": 0,
            "Event_E.in": 0,
        },
        1: {
            "Event_A.out": 1,
            "Event_B.in": 0,
            "Event_C.in": 1,
            "Event_C.out": 1,
            "Event_D.in": 1,
            "Event_D.out": 1,
            "Event_E.in": 1,
        },
    }


@pytest.fixture
def loop_sub_graph_def(graph_def: dict[str, dict]) -> dict[str, dict]:
    """PyTest fixture that defines a standard graph definition for the sub
    graph of a loop event.

    :param graph_def: Standard graph definition.
    :type graph_def: `dict`[`str`, `dict`]
    :return: Returns the standard graph definition for the loop sub graph.
    :rtype: `dict`[`str`, `dict`]
    """
    sub_graph = graph_def
    sub_graph["StartEvent"] = {
        "group_in": None,
        "group_out": {
            "type": "OR",
            "sub_groups": [
                "edge_Start_A"
            ]
        },
    }
    sub_graph["EndEvent"] = {
        "group_in": {
            "type": "OR",
            "sub_groups": [
                "edge_B_End",
                "edge_E_End"
            ]
        },
        "group_out": None
    }
    sub_graph["Event_A"]["group_in"] = {
        "type": "OR",
        "sub_groups": [
            "edge_Start_A"
        ]
    }
    sub_graph["Event_B"]["group_out"] = {
        "type": "OR",
        "sub_groups": [
            "edge_B_End"
        ]
    }
    sub_graph["Event_E"]["group_out"] = {
        "type": "OR",
        "sub_groups": [
            "edge_E_End"
        ]
    }
    return sub_graph


@pytest.fixture
def sub_graph_edges() -> list[str]:
    """PyTest fixture to define edge uids for the loop sub graph.

    :return: Returns the list of edge uids.
    :rtype: `list`[`str`]
    """
    edges_uids = [
        "edge_Start_A",
        "edge_A_B",
        "edge_B_End",
        "edge_A_C",
        "edge_A_D",
        "edge_C_E",
        "edge_D_E",
        "edge_E_End"
    ]
    return edges_uids


@pytest.fixture
def graph_def_with_loop(
    loop_sub_graph_def: dict[str, dict]
) -> dict[str, dict]:
    """PyTest fixture that defines a graph definition containing a loop event
    that contains the standard graph definition of the loop sub graph

    :param loop_sub_graph_def: The loop sub graph standard definition.
    :type loop_sub_graph_def: `dict`[`str`, `dict`]
    :return: Returns the standardised graph definition with loop event with
    loop sub graph.
    :rtype: `dict`[`str`, `dict`]
    """
    graph_def_loop = {
        "Event_X": {
            "group_in": None,
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "edge_X_loop"
                ]
            }
        },
        "Event_Loop": {
            "is_loop": True,
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_X_loop"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "edge_loop_Y"
                ]
            },
            "loop_graph": loop_sub_graph_def,
        },
        "Event_Y": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_loop_Y"
                ]
            },
            "group_out": None
        }
    }
    return graph_def_loop


@pytest.fixture
def edges_graph_loop() -> list[str]:
    """PyTest fixture to define the edge uids found in the graph with loop
    event and subgraph defined above.

    :return: The list of edge uids.
    :rtype: `list`[`str`]
    """
    return [
        "edge_X_loop",
        "edge_loop_Y"
    ]

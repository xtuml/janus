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
def solver() -> CpSolver:
    """PyTest fixture to instantiate :class:`CpSolver`.

    :return: CP-Sat Solver
    :rtype: :class:`CpSolver`
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
            "meta_data": {"EventType": "Event_A"}
        },
        "Event_B": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_A_B"
                ]
            },
            "group_out": None,
            "meta_data": {"EventType": "Event_B"}
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
            },
            "meta_data": {"EventType": "Event_C"}
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
            },
            "meta_data": {"EventType": "Event_D"}
        },
        "Event_E": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_C_E",
                    "edge_D_E"
                ]
            },
            "group_out": None,
            "meta_data": {"EventType": "Event_E"}
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
def expected_solutions_and_to_or() -> list[dict[str, int]]:
    """Py-Test fixture that defines the event solutions for the above graph
    definition.

    :return: Returns a list of dictionaries that hold the event solutions for
    two distinct solution paths.
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "Event_A": 1,
            "Event_B": 0,
            "Event_C": 1,
            "Event_D": 0,
            "Event_E": 1,
        },
        {
            "Event_A": 1,
            "Event_B": 0,
            "Event_C": 0,
            "Event_D": 1,
            "Event_E": 1,
        },
    ]


@pytest.fixture
def expected_solutions_xor_to_or() -> list[dict[str, int]]:
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
            "Event_C": 1,
            "Event_D": 1,
            "Event_E": 1,
        },
    ]


@pytest.fixture
def expected_group_solutions() -> list[dict[str, int]]:
    """Py-Test fixture to define the expected group defined solutions of the
    above graph definition.

    :return: Returns the expected group solutions as a list of
    dictionaries with each entry of the list a distinct solution.
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "Event_A.out": 1,
            "Event_B.in": 1,
            "Event_C.in": 0,
            "Event_C.out": 0,
            "Event_D.in": 0,
            "Event_D.out": 0,
            "Event_E.in": 0,
        },
        {
            "Event_A.out": 1,
            "Event_B.in": 0,
            "Event_C.in": 1,
            "Event_C.out": 1,
            "Event_D.in": 1,
            "Event_D.out": 1,
            "Event_E.in": 1,
        },
    ]


@pytest.fixture
def expected_edge_solutions() -> list[dict[str, int]]:
    """Pytest fixture to provide the edge solutions for the above graph
    definition

    :return: List of dictionaries with keys as edge uid and values as the
    value in the solutions
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "edge_A_B": 1,
            "edge_A_C": 0,
            "edge_A_D": 0,
            "edge_C_E": 0,
            "edge_D_E": 0
        },
        {
            "edge_A_B": 0,
            "edge_A_C": 1,
            "edge_A_D": 1,
            "edge_C_E": 1,
            "edge_D_E": 1
        },
    ]


@pytest.fixture
def expected_edge_solutions_and_to_or() -> list[dict[str, int]]:
    """Pytest fixture to provide the edge solutions for the above graph
    definition

    :return: List of dictionaries with keys as edge uid and values as the
    value in the solutions
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "edge_A_B": 0,
            "edge_A_C": 1,
            "edge_A_D": 0,
            "edge_C_E": 1,
            "edge_D_E": 0
        },
        {
            "edge_A_B": 0,
            "edge_A_C": 0,
            "edge_A_D": 1,
            "edge_C_E": 0,
            "edge_D_E": 1
        },
    ]


@pytest.fixture
def graph_def_with_loop(
    graph_def: dict[str, dict]
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
            },
            "meta_data": {"EventType": "Event_X"}
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
            "loop_graph": graph_def,
            "meta_data": {"EventType": "Event_Loop"}
        },
        "Event_Y": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_loop_Y"
                ]
            },
            "group_out": None,
            "meta_data": {"EventType": "Event_Y"}
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


@pytest.fixture
def expected_solutions_graph_loop_event() -> list[dict[str, int]]:
    """PyTest fixture to provide the expected Event solutions for the graph
    with loop event.

    :return: List of Event solutions.
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "Event_X": 1,
            "Event_Loop": 1,
            "Event_Y": 1,
        }
    ]


@pytest.fixture
def expected_group_solutions_graph_loop_event() -> list[dict[str, int]]:
    """PyTest fixture to provide expected Group solutions for the graph with
    loop event.

    :return: Dictionary of group solutions.
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "Event_X.out": 1,
            "Event_Loop.in": 1,
            "Event_Loop.out": 1,
            "Event_Y.in": 1
        }
    ]


@pytest.fixture
def expected_edge_solutions_graph_loop_event() -> list[dict[str, int]]:
    """Pytest fixture to provide the edge solutions for the above graph
    definition

    :return: List of dictionaries with keys as edge uid and values as the
    value in the solutions
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "edge_X_loop": 1,
            "edge_loop_Y": 1
        }
    ]


@pytest.fixture
def graph_def_with_branch(
    graph_def: dict[str, dict]
) -> dict[str, dict]:
    """PyTest fixture that defines a graph definition containing a branch event
    that contains the standard graph definition of the branch sub graph

    :param loop_sub_graph_def: The branch sub graph standard definition.
    :type loop_sub_graph_def: `dict`[`str`, `dict`]
    :return: Returns the standardised graph definition with branch event with
    branch sub graph.
    :rtype: `dict`[`str`, `dict`]
    """
    graph_def_branch = {
        "Event_X": {
            "group_in": None,
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "edge_X_branch"
                ]
            },
            "meta_data": {"EventType": "Event_X"}
        },
        "Event_Branch": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_X_branch"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "edge_branch_Y"
                ]
            },
            "branch_graph": graph_def,
            "meta_data": {"EventType": "Event_Branch"}
        },
        "Event_Y": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_branch_Y"
                ]
            },
            "group_out": None,
            "meta_data": {"EventType": "Event_Y"}
        }
    }
    return graph_def_branch


@pytest.fixture
def edges_graph_branch() -> list[str]:
    """PyTest fixture to define the edge uids found in the graph with branch
    event and subgraph defined above.

    :return: The list of edge uids.
    :rtype: `list`[`str`]
    """
    return [
        "edge_X_branch",
        "edge_branch_Y"
    ]


@pytest.fixture
def expected_solutions_graph_branch_event() -> list[dict[str, int]]:
    """PyTest fixture to provide the expected Event solutions for the graph
    with branch event.

    :return: List of Event solutions.
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "Event_X": 1,
            "Event_Branch": 1,
            "Event_Y": 1,
        }
    ]


@pytest.fixture
def expected_group_solutions_graph_branch_event() -> list[dict[str, int]]:
    """PyTest fixture to provide expected Group solutions for the graph with
    branch event.

    :return: Dictionary of group solutions.
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "Event_X.out": 1,
            "Event_Branch.in": 1,
            "Event_Branch.out": 1,
            "Event_Y.in": 1
        }
    ]


@pytest.fixture
def expected_edge_solutions_graph_branch_event() -> list[dict[str, int]]:
    """Pytest fixture to provide the edge solutions for the above graph
    definition

    :return: List of dictionaries with keys as edge uid and values as the
    value in the solutions
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    return [
        {
            "edge_X_branch": 1,
            "edge_branch_Y": 1
        }
    ]


@pytest.fixture
def parsed_graph_with_branch(
    graph_def_with_branch: dict[str, dict]
) -> Graph:
    """Pytest fixture to generate a :class:`Graph` instances from a graph
    definition with a branch event

    :param graph_def_with_branch: Dictionary containing the graph defintion
    :type graph_def_with_branch: `dict`[`str`, `dict`]
    :return: Returns the parsed :class:`Graph`
    :rtype: :class:`Graph`
    """
    graph = Graph()
    graph.parse_graph_def(graph_def=graph_def_with_branch)
    return graph


@pytest.fixture
def graph_def_with_nested_loop_in_branch(
    graph_def_with_branch: dict[str, dict],
    graph_def_with_loop: dict[str, dict]
) -> dict[str, dict]:
    """PyTest fixture that defines a graph definition containing a branch event
    that contains the standard graph definition of the branch sub graph

    :param graph_def_with_branch: Dictionary containing the graph defintion
    :type graph_def_with_branch: `dict`[`str`, `dict`]
    :param graph_def_with_loop: The sub graph with loop standard definition.
    :type graph_def_with_loop: `dict`[`str`, `dict`]
    :return: Returns the standardised graph definition with branch event with
    branch sub graph and nested loop.
    :rtype: `dict`[`str`, `dict`]
    """
    graph_def_with_branch["Event_Branch"]["branch_graph"] = (
        graph_def_with_loop
    )
    return graph_def_with_branch


@pytest.fixture
def parsed_graph_with_nested_loop_in_branch(
    graph_def_with_nested_loop_in_branch: dict[str, dict]
) -> Graph:
    """

    :param graph_def_with_nested_loop_in_branch: Standard graph definition
    containing a graph with branch event with a nested loop
    :type graph_def_with_nested_loop_in_branch: `dict`[`str`, `dict`]
    :return: Returns the parsed :class:`Graph`
    :rtype: :class:`Graph`
    """
    graph = Graph()
    graph.parse_graph_def(graph_def=graph_def_with_nested_loop_in_branch)
    return graph


@pytest.fixture
def graph_def_with_loop_and_branch():
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
            "meta_data": {"EventType": "Event_A"}
        },
        "Event_B": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "edge_A_B"
                ]
            },
            "group_out": None,
            "meta_data": {"EventType": "Event_B"}
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
            },
            "meta_data": {"EventType": "Event_C"},
            "loop_graph": {
                "Event_F": {
                    "group_in": None,
                    "group_out": None,
                    "meta_data": {
                        "EventType": "Event_F"
                    }
                }
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
            },
            "meta_data": {"EventType": "Event_D"},
            "branch_graph": {
                "Event_G": {
                    "group_in": None,
                    "group_out": None,
                    "meta_data": {
                        "EventType": "Event_G"
                    }
                }
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
            "group_out": None,
            "meta_data": {"EventType": "Event_E"}
        }
    }
    return json


@pytest.fixture
def parsed_graph_with_loop_and_branch(
    graph_def_with_loop_and_branch: dict[str, dict]
) -> Graph:
    graph = Graph()
    graph.parse_graph_def(graph_def_with_loop_and_branch)
    return graph

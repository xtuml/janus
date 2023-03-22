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

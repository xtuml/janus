# pylint: disable=R1732
"""Testing group.py
"""
from typing import Type, Union
from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar
from test_event_generator.core.event import Event
from test_event_generator.core.edge import Edge
from test_event_generator.core.group import Group, ORGroup, XORGroup, ANDGroup
from test_event_generator.utils.utils import solve_model


class TestSetSubGroupParentsGroups:
    """Class to group test concerning the instance method of :class:`Group`
    `set_sub_groups_parent`
    """
    def test_into_event(self, model: CpModel) -> None:
        """Test  that nested Edges and Groups have the corrent parent Group
        when the parent Group and sub-Groups/sub-Edges are directed into an
        Event.

        :param model: The CP-SAT model
        :type model: :class:`CpModel`
        """
        edge = Edge(model, "edge")
        group_1 = Group(model, "group_1", [edge], is_into_event=True)
        group_2 = Group(model, "group_2", [group_1], is_into_event=True)

        group_2.set_sub_groups_parent()

        assert group_2.parent_group is None
        assert group_1.parent_group == group_2
        assert edge.group_in == group_1

    def test_not_into_event(self, model: CpModel) -> None:
        """Test  that nested Edges and Groups have the corrent parent Group
        when the parent Group and sub-Groups/sub-Edges are directed out of an
        Event.

        :param model: The CP-SAT model
        :type model: :class:`CpModel`
        """
        edge = Edge(model, "edge")
        group_1 = Group(model, "group_1", [edge], is_into_event=False)
        group_2 = Group(model, "group_2", [group_1], is_into_event=False)

        group_2.set_sub_groups_parent()

        assert group_2.parent_group is None
        assert group_1.parent_group == group_2
        assert edge.group_out == group_1

    def test_event_propagation_into_event(self, model: CpModel) -> None:
        """Test that the Event of highest parent Group is propagated correctly
        to the nested Edges and Groups when the Group and sub-Groups/sub-Edges
        are directed into an Event.

        :param model: The CP-SAT model
        :type model: :class:`CpModel`
        """
        edge = Edge(model, "edge")
        group_1 = Group(model, "group_1", [edge], is_into_event=True)
        group_2 = Group(model, "group_2", [group_1], is_into_event=True)
        event = Event(model)
        group_2.event = event

        group_2.set_sub_groups_parent()

        assert group_1.event == event
        assert edge.event_in == event

    def test_event_propagation_not_into_event(self, model: CpModel) -> None:
        """Test that the Event of highest parent Group is propagated correctly
        to the nested Edges and Groups when the Group and sub-Groups/sub-Edges
        are directed out of an Event.

        :param model: The CP-SAT model
        :type model: :class:`CpModel`
        """
        edge = Edge(model, "edge")
        group_1 = Group(model, "group_1", [edge], is_into_event=False)
        group_2 = Group(model, "group_2", [group_1], is_into_event=False)
        event = Event(model)
        group_2.event = event

        group_2.set_sub_groups_parent()

        assert group_1.event == event
        assert edge.event_out == event


def get_main_group_update_list(
    model: CpModel,
    sub_variables: list[Union[Edge, Group]],
    group_class: Type[Group],
    uid: str
) -> tuple[list[IntVar], Group]:
    """Helper function to get a list of all the IntVar variables after
    creating a new :class:`Group` instance that contains the input
    :class:`Edge`'s and :class:`Group`'s

    :param model: CP-SAT model
    :type model: :class:`CpModel`
    :param sub_variables: List of Edges and Groups of the newly created parent
    :class:`Group`
    :type sub_variables: `list`[class:`Union`[:class:`Edge`, :class:`Group`]]
    :param group_class: The :class:`Group` type that is to be used as the
    parent :class:`Group` instance
    :type group_class: :class:`Type`[:class:`Group`]
    :param uid: The uid of the newly created parent :class:`Group`
    :type uid: `str`
    :return: Returns a list of the extracted :class:`IntVar` variables
    including the newly created :class:`Group`
    :rtype: `list`[:class:`IntVar`]
    """
    group = group_class(
        model=model,
        uid=uid,
        group_variables=sub_variables,
        is_into_event=False
    )
    all_variables = [
        group_edge.variable
        for group_edge in sub_variables + [group]
    ]
    return all_variables, group


class TestConstraints:
    """Class to group tests of the constraints for:
    * :class:`ORGroup`
    * :class:`XORGroup`
    * :class:`ANDGroup`
    """
    def test_or_group_multiple_edges_and_groups(
        self,
        model: CpModel,
        solver: CpSolver,
        sub_variables: list[Union[Edge, Group]]
    ) -> None:
        """Tests the OR constraint. There should be 16 solutions (2^4
        combinations of either 0's and 1's).
        The sub variables and parent group variable should satisfy the
        following logical or equation
        edge_1 | edge_2 | group_1 | group_2 = or_group

        :param model: The CP-SAT model
        :type model: :class:`CpModel`
        :param solver: The CP-SAT solver
        :type solver: :class:`CpSolver`
        :param sub_variables: The list of Edges and Groups that are within
        the parent Group
        :type sub_variables: `list`[:class:`Union`[:class:`Edge`,
        :class:`Group`]]
        """
        all_variables, _ = get_main_group_update_list(
            model=model,
            sub_variables=sub_variables,
            group_class=ORGroup,
            uid="or_group"
        )
        solutions = solve_model(
            model=model,
            solver=solver,
            variables=all_variables
        )
        assert len(solutions) == 16
        for solution in solutions:
            assert (
                solution["edge_1"] | solution["edge_2"]
                | solution["group_1"] | solution["group_2"]
                == solution["or_group"]
            )

    def test_xor_group_multiple_edges_and_groups(
        self,
        model: CpModel,
        solver: CpSolver,
        sub_variables: list[Union[Edge, Group]]
    ) -> None:
        """Tests the XOR constraint. There should be 5 solutions. (2^4
        combinations of either 0's and 1's minus the number of situations
        where any of the sub-variables are equal to 1 at the same time).
        The sub variables and parent group variable should satisfy the
        following logical xor equation
        edge_1 ^ edge_2 ^ group_1 ^ group_2 = xor_group

        :param model: The CP-SAT model
        :type model: :class:`CpModel`
        :param solver: The CP-SAT solver
        :type solver: :class:`CpSolver`
        :param sub_variables: The list of Edges and Groups that are within
        the parent Group
        :type sub_variables: `list`[:class:`Union`[:class:`Edge`,
        :class:`Group`]]
        """
        all_variables, _ = get_main_group_update_list(
            model=model,
            sub_variables=sub_variables,
            group_class=XORGroup,
            uid="xor_group"
        )
        solutions = solve_model(
            model=model,
            solver=solver,
            variables=all_variables
        )
        assert len(solutions) == 5
        for solution in solutions:
            assert (
                solution["edge_1"] ^ solution["edge_2"]
                ^ solution["group_1"] ^ solution["group_2"]
                == solution["xor_group"]
            )

    def test_and_group_multiple_edges_and_groups(
        self,
        model: CpModel,
        solver: CpSolver,
        sub_variables: list[Union[Edge, Group]]
    ) -> None:
        """Tests the AND constraint. There should be 2 solutions (all
         sub-variables are 1 and all sub-variables are 0). The sub variables
         and parent group variable should satisfy the following logical and
         equation
        edge_1 & edge_2 & group_1 & group_2 = and_group

        :param model: The CP-SAT model
        :type model: :class:`CpModel`
        :param solver: The CP-SAT solver
        :type solver: :class:`CpSolver`
        :param sub_variables: The list of Edges and Groups that are within
        the parent Group
        :type sub_variables: `list`[:class:`Union`[:class:`Edge`,
        :class:`Group`]]
        """
        all_variables, _ = get_main_group_update_list(
            model=model,
            sub_variables=sub_variables,
            group_class=ANDGroup,
            uid="and_group"
        )
        solutions = solve_model(
            model=model,
            solver=solver,
            variables=all_variables
        )
        assert len(solutions) == 2
        for solution in solutions:
            assert (
                solution["edge_1"] & solution["edge_2"]
                & solution["group_1"] & solution["group_2"]
                == solution["and_group"]
            )

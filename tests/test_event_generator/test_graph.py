# pylint: disable=R0903
"""
Tests for graph.py
"""
from copy import deepcopy
from typing import Type

import pytest
from ortools.sat.python.cp_model import CpModel, CpSolver
from test_event_generator.graph import Graph
from test_event_generator.core.event import Event, LoopEvent
from test_event_generator.core.group import ORGroup, XORGroup, ANDGroup, Group
from test_event_generator.solutions import (
    EventSolution,
    LoopEventSolution,
    GraphSolution,
    BranchEventSolution
)
from test_event_generator.utils.utils import solve_model
from tests.utils import (
    check_length_attr,
    check_solution_correct
)


class TestSelectGroup:
    """Test for :class:`Graph`.`select_group`
    """
    @staticmethod
    def test_select_group_or() -> None:
        """OR Group test
        """
        assert Graph.select_group("OR") == ORGroup

    @staticmethod
    def test_select_group_xor() -> None:
        """XOR Group test
        """
        assert Graph.select_group("XOR") == XORGroup

    @staticmethod
    def test_select_group_and() -> None:
        """AND Group test
        """
        assert Graph.select_group("AND") == ANDGroup

    @staticmethod
    def test_select_group_default() -> None:
        """Default behaviour test
        """
        assert Graph.select_group("Unknown") == ORGroup


class TestCreateSubGroups:
    """Tests for :class:`Graph`.`create_sub_groups`
    """
    @staticmethod
    def test_no_graph_def() -> None:
        """Test that providing the parameter group_def with `None` returns
        `None`.
        """
        graph = Graph()
        assert not graph.create_sub_groups(
            group_def=None,
            key_tuple=("Event_A", "in"),
            is_into_event=True
        )

    @staticmethod
    def test_incorrect_key_tuple(graph_def: dict) -> None:
        """Test that providing an incorrect key_tuple raise the correct
        Exception.

        :param graph_def: Standardised graph definition
        :type graph_def: `dict`
        """
        graph = Graph()
        with pytest.raises(RuntimeError) as e_info:
            graph.create_sub_groups(
                group_def=graph_def,
                key_tuple=("Event_A",),
                is_into_event=True
            )
        assert str(e_info.value) == (
            "Key tuple must at least have entry for parent event and the "
            "highest group"
        )

    @staticmethod
    def test_incorrect_group_def_no_type_key() -> None:
        """Test that not providing the key "type" in the group_def dictionary
        raises the correct Exception.
        """
        graph = Graph()
        with pytest.raises(KeyError) as e_info:
            graph.create_sub_groups(
                group_def={"sub_groups": []},
                key_tuple=("Event_A", "in"),
                is_into_event=True
            )
        assert e_info.value.args[0] == "type"

    @staticmethod
    def test_incorrect_group_def_no_sub_groups_key() -> None:
        """Test not providing the key "sub_groups" in the group_def dictionary
        raises the correct Exception.
        """
        graph = Graph()
        with pytest.raises(KeyError) as e_info:
            graph.create_sub_groups(
                group_def={"type": "OR"},
                key_tuple=("Event_A", "in"),
                is_into_event=True
            )
        assert e_info.value.args[0] == "sub_groups"

    @staticmethod
    def test_edge_not_found(
        graph_def: dict,
        edges: list[str]
    ) -> None:
        """Test that correct exception is raised when a graph defintion
        dictionary contains an edge uid cannot be found in the
        :class:`Graph` instances edges dictionary.

        :param graph_def: Standardised graph definition.
        :type graph_def: `dict`
        :param edges: List of edges in the graph definition.
        :type edges: `list`[`str`]
        """
        graph = Graph()
        group_def = graph_def["Event_A"]["group_out"]
        edges_slice = edges[:2]
        graph.add_edges(edges_slice)
        with pytest.raises(RuntimeError) as e_info:
            graph.create_sub_groups(
                group_def=group_def,
                key_tuple=("Event_A", "out"),
                is_into_event=False
            )
            assert str(e_info.value) == (
                f"The edge {edges[2]} is not in the list provided."
                " Check the edge uid is correct or add it to the list."
                " The edge is located within the input json at: \n"
                f"{'Event_A'}\ngroup_{'out'}\n"
                "\n".join([
                    f"Sub-group list position {key}"
                    for key in ["1", "1"]
                ])
            )

    @staticmethod
    def test_shallow_edges(
        graph_def: dict,
        edges: list[str]
    ) -> None:
        """Test that all edges and groups are added correctly to the
        :class:`Graph` instance from a selected group definition. Tests a
        group definition that has only edges with parent group a top level
        group of an event.

        :param graph_def: Standardised graph definition.
        :type graph_def: `dict`
        :param edges: List of edge uids found in the graph definition.
        :type edges: `list`[`str`]
        """
        graph = Graph()
        group_def = graph_def["Event_E"]["group_in"]
        edges_slice = edges[-2:]
        graph.add_edges(edges_slice)
        graph.create_sub_groups(
            group_def=group_def,
            key_tuple=("Event_E", "in"),
            is_into_event=True
        )
        # correct key is present
        assert ("Event_E", "in") in graph.groups
        # check that group is of the correct subclass
        assert isinstance(graph.groups[("Event_E", "in")], ORGroup)
        # check all the edges created are part of the group
        for edge in graph.edges.values():
            assert edge in graph.groups[("Event_E", "in")].group_variables

    @staticmethod
    def test_nested_groups(
        graph_def: dict,
        edges: list[str]
    ) -> None:
        """Test that all edges and groups are added correctly to the
        :class:`Graph` instance from a selected group definition. Tests a
        group definition with groups and edges nested within groups.

        :param graph_def: Standardised graph defintion.
        :type graph_def: `dict`
        :param edges: List of edges within the graph definition.
        :type edges: `list`[`str`]
        """
        graph = Graph()
        group_def = graph_def["Event_A"]["group_out"]
        edges_slice = edges[:3]
        graph.add_edges(edges_slice)
        graph.create_sub_groups(
            group_def=group_def,
            key_tuple=("Event_A", "out"),
            is_into_event=False
        )
        # check all correct keys are present
        assert ("Event_A", "out") in graph.groups
        assert ("Event_A", "out", "1") in graph.groups
        # check that the groups are of the correct subclass
        assert isinstance(graph.groups[("Event_A", "out")], XORGroup)
        assert isinstance(graph.groups[("Event_A", "out", "1")], ANDGroup)
        # check that sub-groups/edges are correct
        for subgroup_edge in [
            graph.groups[("Event_A", "out", "1")],
            graph.edges["edge_A_B"]
        ]:
            assert (
                subgroup_edge
                in graph.groups[("Event_A", "out")].group_variables
            )
        for edge in edges_slice[1:]:
            assert (
                graph.edges[edge]
                in graph.groups[("Event_A", "out", "1")].group_variables
            )
        # check that sub group name is correct
        assert (
            graph.groups[("Event_A", "out", "1")].variable.Name()
        ) == (
            ".".join(("Event_A", "out", "1"))
        )


class TestEdgeExtraction:
    """Tests that test methods for edge extraction from a graph definition.
    """
    @staticmethod
    def test_unique_edges_too_many(edges: list[str]) -> None:
        """Tests that the correct Exception is raised when there are too many
        of the same edge uid in a list. Tests :class:`Graph`.`unique_edges`.

        :param edges: List of edge uids.
        :type edges: `list`[`str`]
        """
        edges_too_many = edges * 3
        with pytest.raises(RuntimeError) as e_info:
            Graph.unique_edges(edges_too_many)
        assert str(e_info.value) == (
            "Some of the edges have more than 2 ocurrences"
        )

    @staticmethod
    def test_unique_edges_too_few(edges: list[str]) -> None:
        """Tests that the correct Exception is raised when there are too few
        of the same edge uid in a list. Tests :class:`Graph`.`unique_edges`.

        :param edges: List of edge uids.
        :type edges: `list`[`str`]
        """
        edges_too_few = edges
        with pytest.raises(RuntimeError) as e_info:
            Graph.unique_edges(edges_too_few)
        assert str(e_info.value) == (
            "Some of the edges have less than 2 ocurrences"
        )

    @staticmethod
    def test_unique_edges_too_few_too_many(edges: list[str]) -> None:
        """Tests that the correct Exception is raised when there are both too
        few and too many of some of the edge uids in a list. Tests
        :class:`Graph`.`unique_edges`.

        :param edges: List of edge uids.
        :type edges: `list`[`str`]
        """
        edges_too_few_too_many = edges + edges[1:] + edges[1:]
        with pytest.raises(RuntimeError) as e_info:
            Graph.unique_edges(edges_too_few_too_many)
        assert str(e_info.value) == (
            "Some of the edges have more than 2 occurences"
            " and some have less than 2 occurences."
        )

    @staticmethod
    def test_get_duplicates_remove_one(
        graph_def: dict,
        edges: list[str]
    ) -> None:
        """Tests that the correct number of each edge are extracted from a
        graph definition after an existing edge uid is removed from a graph
        definition. Tests :class:`Graph`.`get_duplicates`.

        :param graph_def: Standardised graph defintion.
        :type graph_def: `dict`
        :param edges: List of edge uids.
        :type edges: `list`[`str`]
        """
        graph_def["Event_A"]["group_out"]["sub_groups"][1][
            "sub_groups"
        ].pop(0)
        duplicate_edges = Graph.get_duplicates(graph_def)
        for edge in edges:
            if edge == "edge_A_C":
                assert duplicate_edges.count(edge) == 1
            else:
                assert duplicate_edges.count(edge) == 2

    @staticmethod
    def test_get_duplicates_add_one(
        graph_def: dict,
        edges: list[str]
    ) -> None:
        """Tests that the correct number of each edge are extracted from a
        graph definition after adding a repeat of an existing edge uid to a
        graph definition. Tests :class:`Graph`.`get_duplicates`.

        :param graph_def: Standardised graph defintion.
        :type graph_def: `dict`
        :param edges: List of edge uids.
        :type edges: `list`[`str`]
        """
        graph_def["Event_A"]["group_out"]["sub_groups"][1][
            "sub_groups"
        ].append("edge_C_E")
        duplicate_edges = Graph.get_duplicates(graph_def)
        for edge in edges:
            if edge == "edge_C_E":
                assert duplicate_edges.count(edge) == 3
            else:
                assert duplicate_edges.count(edge) == 2

    @staticmethod
    def test_get_duplicates(
        graph_def: dict,
        edges: list[str]
    ) -> None:
        """Tests that the correct number of each edge are extracted from a
        graph definition.

        :param graph_def: Standardised graph defintion.
        :type graph_def: `dict`
        :param edges: List of edge uids.
        :type edges: `list`[`str`]
        """
        duplicate_edges = Graph.get_duplicates(graph_def)
        for edge in edges:
            assert duplicate_edges.count(edge) == 2

    @staticmethod
    def test_extract_edges_correct(
        graph_def: dict,
        edges: list[str]
    ) -> None:
        """Tests that edges are extracted correctly from a graph definition
        using the method :class:`Graph`.`extract_edges`.

        :param graph_def: Standardised graph defintion.
        :type graph_def: `dict`
        :param edges: List of edge uids.
        :type edges: `list`[`str`]
        """
        extracted_edges = Graph.extract_edges(graph_def)
        assert sorted(edges) == sorted(extracted_edges)


class TestParseGraphDef:
    """Tests for the method :class:`Graph`.`parse_graph_def`.
    """
    @staticmethod
    def test_edges_added_correctly(
        parsed_graph: Graph,
        edges: list[str]
    ) -> None:
        """Test that edges are added correctly to :class:`Graph` instance.

        :param parsed_graph: A graph instance containing a parsed graph
        definition.
        :type parsed_graph: :class:`Graph`
        :param edges: List of edge uids.
        :type edges: `list`[`str`]
        """
        assert sorted(edges) == sorted(parsed_graph.edges.keys())

    @staticmethod
    def test_events_added_correctly(
        parsed_graph: Graph,
        graph_def: dict[str, dict]
    ) -> None:
        """Test that events are added correctly to :class:`Graph` instance.

        :param parsed_graph: A graph instance containing a parsed graph
        definition.
        :type parsed_graph: :class:`Graph`
        :param graph_def: Standardised graph defintion.
        :type graph_def: `dict`
        """
        assert sorted(graph_def.keys()) == sorted(parsed_graph.events.keys())

    @staticmethod
    def test_events_contain_correct_groups(
        parsed_graph: Graph,
        graph_def: dict
    ) -> None:
        """Test that "in" and "out" groups are added correctly to
        :class:`Graph` instance.

        :param parsed_graph: A graph instance containing a parsed graph
        definition.
        :type parsed_graph: :class:`Graph`
        :param graph_def: Standardised graph defintion.
        :type graph_def: `dict`
        """
        for event_uid, event_def in graph_def.items():
            group_in = parsed_graph.events[event_uid].in_group
            group_out = parsed_graph.events[event_uid].out_group
            if event_def["group_in"]:
                assert parsed_graph.groups[(event_uid, "in")] == group_in
            if event_def["group_out"]:
                assert parsed_graph.groups[(event_uid, "out")] == group_out

    @staticmethod
    def test_event_is_start(
        parsed_graph: Graph,
        graph_def: dict
    ) -> None:
        """Test that an event is correctly identified as a start point if it
        only has an "out" group.
        :class:`Graph` instance.

        :param parsed_graph: A graph instance containing a parsed graph
        definition.
        :type parsed_graph: :class:`Graph`
        :param graph_def: Standardised graph defintion.
        :type graph_def: `dict`
        """
        for event_uid, event_def in graph_def.items():
            if not event_def["group_in"] and event_def["group_out"]:
                assert parsed_graph.events[event_uid].is_start

    @staticmethod
    def test_event_is_end(
        parsed_graph: Graph,
        graph_def: dict
    ) -> None:
        """Test that an event is correctly identified as an end point if it
        only has an "in" group.
        :class:`Graph` instance.

        :param parsed_graph: A graph instance containing a parsed graph
        definition.
        :type parsed_graph: :class:`Graph`
        :param graph_def: Standardised graph defintion.
        :type graph_def: `dict`
        """
        for event_uid, event_def in graph_def.items():
            if not event_def["group_out"] and event_def["group_in"]:
                assert parsed_graph.events[event_uid].is_end


class TestCreateEvent:
    """Tests :class:`Graph`.`create_event` method.
    """
    @staticmethod
    def test_create_event_class(
        model: CpModel
    ) -> None:
        """Test an :class:`Event` instance is created and not a
        :class:`LoopEvent` instance.

        :param model: CP-SAT model.
        :type model: :class:`CpModel`
        """
        event = Graph.create_event(
            model=model
        )
        assert isinstance(event, Event)
        assert not isinstance(event, LoopEvent)

    @staticmethod
    def test_create_loop_event_class(
        model: CpModel,
        graph_def: dict
    ) -> None:
        """Test that :class:`LoopEvent` instance is created when providing a
        loop sub graph definition.

        :param model: CP-SAT model.
        :type model: :class:`CpModel`
        :param graph_def: Standardised graph definition.
        :type graph_def: `dict`
        """
        event = Graph.create_event(
            model=model,
            loop_graph=graph_def
        )
        assert isinstance(event, LoopEvent)

    @staticmethod
    def test_is_start_event(
        model: CpModel
    ) -> None:
        """Test that property `is_start` evaluates to `True` if and only if a
        :class:`Group` instance is provided to the parameter `group_out`.

        :param model: CP-SAT model.
        :type model: :class:`CpModel`
        """
        event = Graph.create_event(
            model=model,
            group_out=Group(
                model=model,
                uid="group_out",
                group_variables=[],
                is_into_event=False
            )
        )
        assert event.is_start

    @staticmethod
    def test_is_end_event(
        model: CpModel
    ) -> None:
        """Test that property `is_end` evaluates to `True` if and only if a
        :class:`Group` instance is provided to the parameter `group_in`.

        :param model: CP-SAT model.
        :type model: :class:`CpModel`
        """
        event = Graph.create_event(
            model=model,
            group_in=Group(
                model=model,
                uid="group_in",
                group_variables=[],
                is_into_event=False
            )
        )
        assert event.is_end

    @staticmethod
    def test_is_not_start_or_end_event(
        model: CpModel
    ) -> None:
        """Test that property `is_end` evaluates to `False` and `is_start`
        evaluates to `False` if separate :class:`Group` instances are provided
        to the parameters `group_in` and `group_out`, rerspectively.

        :param model: CP-SAT model.
        :type model: :class:`CpModel`
        """
        event = Graph.create_event(
            model=model,
            group_in=Group(
                model=model,
                uid="group_in",
                group_variables=[],
                is_into_event=False
            ),
            group_out=Group(
                model=model,
                uid="group_out",
                group_variables=[],
                is_into_event=False
            )
        )
        assert not event.is_start
        assert not event.is_end

    @staticmethod
    def test_meta_data(
        model: CpModel
    ) -> None:
        """Test that meta data is added to the :class:`Event` instance
        correctly.

        :param model: CP-SAT model.
        :type model: :class:`CpModel`
        """
        event = Graph.create_event(
            model=model,
            meta_data={"some_data": 2}
        )
        assert event.meta_data
        meta_data_keys = list(event.meta_data.keys())
        assert len(meta_data_keys) == 1
        assert meta_data_keys[0] == "some_data"
        assert event.meta_data["some_data"] == 2


def test_set_start_point_constraint(
    model: CpModel,
    solver: CpSolver
) -> None:
    """Test that :class:`Graph`.`set_start_points_constraint` is producing the
    correct results. There should be `2^n - 1` solutions (n being the number
    of group variables) which is the number of combinations for choosing the
    values 0 or 1 for n different variables minus 1 so that not all of the
    variables have the value 0.

    :param model: CP-SAT model.
    :type model: :class:`CpModel`
    :param solver: CP-SAT solver.
    :type solver: :class:`CpSolver`
    """
    group_variables: list[Group] = []
    for i in range(3):
        group_variables.append(
            Group(
                model=model,
                uid=str(i),
                group_variables=[],
                is_into_event=False
            ).variable
        )
    Graph.set_start_point_constraint(
        model=model,
        group_variables=group_variables
    )
    solutions = solve_model(
        model=model,
        solver=solver,
        variables=group_variables
    )
    assert len(solutions) == 7
    sorted_solutions = sorted(
        solutions,
        key=lambda x: x["0"] + 0.1 * x["1"] + 0.01 * x["2"]
    )
    expected_solutions = [
        [0, 0, 1], [0, 1, 0], [0, 1, 1],
        [1, 0, 0], [1, 0, 1], [1, 1, 0],
        [1, 1, 1]
    ]
    for expected_solution, test_solution in zip(
        expected_solutions, sorted_solutions
    ):
        assert all(
            test_solution[str(i)] == variable_value
            for i, variable_value in enumerate(expected_solution)
        )


class TestSolve:
    """Tests of the solving of the ILP model and converting to Event solutions.
    """
    @staticmethod
    def test_convert_to_event_solutions(
        parsed_graph: Graph,
        expected_solutions: list[dict[str, int]],
        expected_group_solutions: list[dict[str, int]]
    ) -> None:
        """Tests :class:`Graph`.`convert_to_event_solutions` and ensure the
        correct Event solutions are output from the given input group
        solutions.

        :param parsed_graph: A graph instance containing a parsed graph
        definition.
        :type parsed_graph: :class:`Graph`
        :param expected_solutions: List of expected event solutions.
        :type expected_solutions: `list`[`dict`[`str`, `int`]]
        :param expected_group_solutions: The group solutions to convert to
        event solutions.
        :type expected_group_solutions: `list`[`dict`[`str`, `int`]]
        """
        converted_solutions = parsed_graph.convert_to_event_solutions(
            expected_group_solutions
        )
        converted_solutions = sorted(
            converted_solutions,
            key=lambda x: sum(x.values())
        )
        for i in range(2):
            for event_id, value in expected_solutions[i].items():
                assert value == converted_solutions[i][event_id]

    @staticmethod
    def test_solve_num_sols(
        parsed_graph: Graph
    ) -> None:
        """Tests :class:`Graph`.`solve` to ensure the number of found
        solutions from the input graph definition is correct.

        :param parsed_graph: A graph instance containing a parsed graph
        definition.
        :type parsed_graph: :class:`Graph`
        """
        parsed_graph.solve()
        assert len(parsed_graph.solutions["Event"]) == 2

    @staticmethod
    def test_solve_sols_correct(
        parsed_graph: Graph,
        expected_solutions: list[dict[str, int]],
    ) -> None:
        """Tests :class:`Graph`.`solve` to ensure the solutons found from the
        input graph definition are correct.

        :param parsed_graph: A graph instance containing a parsed graph
        definition.
        :type parsed_graph: :class:`Graph`
        :param expected_solutions: List of expected event solutions.
        :type expected_solutions: `list`[`dict`[`str`, `int`]]
        """
        parsed_graph.solve()
        actual_solutions = parsed_graph.solutions["Event"]
        # sort actual solutions by total sum of values to order like expected
        actual_solutions = sorted(
            actual_solutions,
            key=lambda x: sum(x.values())
        )
        for i, actual_solution in enumerate(actual_solutions):
            for event_id, value in expected_solutions[i].items():
                assert value == actual_solution[event_id]


class TestLoopFixtures:
    """Base Class to hold fixtures for subclass tests
    """
    @staticmethod
    @pytest.fixture
    def parsed_graph_with_loop(
        graph_def_with_loop: dict[str, dict]
    ) -> Graph:
        """PyTest fixture to provide a :class:`Graph` instance that has parsed
        a standard graph definition that contains a loop event.

        :param graph_def_with_loop: Standardised graph definition containing a
        loop event.
        :type graph_def_with_loop: `dict`[`str`, `dict`]
        :return: Returns a :class:`Graph` instance that has parsed the graph
        defintion with loop event.
        :rtype: :class:`Graph`
        """
        graph = Graph()
        graph.parse_graph_def(graph_def_with_loop)
        return graph


class TestLoopEvents(TestLoopFixtures):
    """Test the implementation of loop event when parsed by
    :class:`Graph`.`parse_graph_def`.
    """
    @staticmethod
    @pytest.fixture
    def loop_event(parsed_graph_with_loop: Graph) -> Event | LoopEvent:
        """PyTest fixture that extracts the loop event from the parsed graph

        :param parsed_graph_with_loop: The :class:`Graph` instance that parsed
        the graph definition with loop event.
        :type parsed_graph_with_loop: :class:`Graph`
        :return: Returns the extracted :class:`Event`
        :rtype: :class:`Event` | :class:`LoopEvent`
        """
        return parsed_graph_with_loop.events["Event_Loop"]

    @staticmethod
    def test_loop_event_added_correctly(
        loop_event: LoopEvent
    ) -> None:
        """Tests that the loop event is an instance of :class:`LoopEvent`.

        :param loop_event: The extracted loop event.
        :type loop_event: :class:`LoopEvent`
        """
        assert isinstance(loop_event, LoopEvent)

    @staticmethod
    def test_loop_event_sub_graph_correct(
        loop_event: LoopEvent,
        graph_def: dict[str, dict],
        edges: list[str]
    ) -> None:
        """Tests the sub graph has been correctly formed from the parsed graph
        definition.

        :param loop_event: The :class:`LoopEvent`
        :type loop_event: :class:`LoopEvent`
        :param graph_def: The graph definition for the loop subgraph.
        :type graph_def: `dict`[`str`, `dict`]
        :param edges: The edge uids in the loop subgraph.
        :type edges: `list`[`str`]
        """
        loop_event_sub_graph: Graph = loop_event.sub_graph
        # test edges added correctly
        TestParseGraphDef.test_edges_added_correctly(
            loop_event_sub_graph,
            edges
        )
        # test events added correctly
        TestParseGraphDef.test_events_added_correctly(
            parsed_graph=loop_event_sub_graph,
            graph_def=graph_def
        )
        # test events contain correct groups
        TestParseGraphDef.test_events_contain_correct_groups(
            parsed_graph=loop_event_sub_graph,
            graph_def=graph_def
        )
        # test start events
        TestParseGraphDef.test_event_is_start(
            parsed_graph=loop_event_sub_graph,
            graph_def=graph_def
        )


class TestSolveLoopSubGraphs(TestLoopFixtures):
    """Tests the solution of LoopEvent subgraphs and helper functions.
    """
    @staticmethod
    @pytest.fixture
    def loop_event(
        model: CpModel,
        graph_def: dict[str, dict]
    ) -> LoopEvent:
        """PyTest fixture to define :class:`LoopEvent`.

        :param model: CP-SAT model
        :type model: :class`CpModel`
        :param graph_def: Standardised graph definition for the loop
        sub graph.
        :type graph_def: `dict`[`str`, `dict`]
        :return: Returns the loop event with sub graph definied by the input
        graph definition.
        :rtype: :class:`LoopEvent`
        """
        sub_graph = Graph()
        event = LoopEvent(
            model=model,
            sub_graph=sub_graph
        )
        event.set_graph_with_graph_def(graph_def)
        return event

    @staticmethod
    @pytest.fixture
    def events_list(
        model: CpModel,
        loop_event: LoopEvent
    ) -> list[Event | LoopEvent]:
        """PyTest fixture to define a mixed list of :class:`Event`'s and
        :class:`LoopEvent`'s.

        :param model: CP-SAT model
        :type model: :class:`CpModel`
        :param loop_event: A :class:`LoopEvent` instance with a parsed sub
        graph.
        :type loop_event: :class:`LoopEvent`
        :return: Returns a mixed list of :class:`Event`'s and
        :class:`LoopEvent`'s.
        :rtype: `list`[:class:`Event` | :class:`LoopEvent`]
        """
        return [
            Event(model=model),
            Event(model=model),
            loop_event,
            deepcopy(loop_event)
        ]

    @staticmethod
    def test_filter_events(
        events_list: list[Event | LoopEvent],
    ) -> None:
        """Tests :class:`Graph`.`filter_events` correctly filters out the
        :class:`Event` instances and retains the :class:`LoopEvent` instances.

        :param events_list: Mixed list of :class:`Event`'s and
        :class:`LoopEvent`'s.
        :type events_list: `list`[:class:`Event`  |  :class:`LoopEvent`]
        """
        filtered_list = Graph.filter_events(events_list)
        assert len(filtered_list) == 2
        for event in filtered_list:
            assert isinstance(event, LoopEvent)

    @staticmethod
    def test_solve_loop_events_sub_graph_error(
        events_list: list[Event | LoopEvent]
    ) -> None:
        """Tests :class:`Graph`.`solve_loop_events_sub_graphs` raises the
        correct :class:`RuntimeError`

        :param events_list: Mixed list of :class:`Event`'s and
        :class:`LoopEvent`'s.
        :type events_list: `list`[:class:`Event` | :class:`LoopEvent`]
        """
        with pytest.raises(RuntimeError) as e_info:
            Graph.solve_loop_events_sub_graphs(
                loop_events=events_list
            )
        assert e_info.value.args[0] == (
            "At least one of the events is not a LoopEvent."
        )

    @staticmethod
    def test_solve_loop_events_sub_graph_correct(
        events_list: list[Event | LoopEvent],
        expected_solutions: list[dict[str, int]]
    ) -> None:
        """Tests :class:`Graph`.`solve_loop_events_sub_graphs` gives the
        corrrect solutions.

        :param events_list: Mixed list of :class:`Event`'s and
        :class:`LoopEvent`'s.
        :type events_list: `list`[:class:`Event` | :class:`LoopEvent`]
        :param expected_solutions: List of expected solutions.
        :type expected_solutions: `list`[`dict`[`str`, `int`]]
        """
        filtered_events = Graph.filter_events(events_list)
        Graph.solve_loop_events_sub_graphs(filtered_events)
        for event in filtered_events:
            assert len(event.sub_graph.solutions["Event"]) == 2
            TestSolve.test_solve_sols_correct(
                parsed_graph=event.sub_graph,
                expected_solutions=expected_solutions
            )

    @staticmethod
    def test_solve_graph_with_loop(
        parsed_graph_with_loop: Graph,
        expected_solutions_graph_loop_event: list[dict[str, int]]
    ) -> None:
        """Tests that the solution to the main :class:`Graph` with loop event
        is correct.

        :param parsed_graph_with_loop: A :class:`Graph` instance that has
        parsed a standardised graph definition.
        :type parsed_graph_with_loop: :class:`Graph`
        :param expected_solutions_graph_loop_event: The expected solutions.
        :type expected_solutions_graph_loop_event: `list`[`dict`[`str`, `int`]]
        """
        parsed_graph_with_loop.solve()
        assert len(parsed_graph_with_loop.solutions["Event"]) == 1
        TestSolve.test_solve_sols_correct(
            parsed_graph=parsed_graph_with_loop,
            expected_solutions=expected_solutions_graph_loop_event
        )

    @staticmethod
    def test_solve_graph_with_loop_sub_graph(
        parsed_graph_with_loop: Graph,
        expected_solutions: list[dict[str, int]]
    ) -> None:
        """Tests that the solution to the sub graph of the :class:`LoopEvent`
        in the main :class:`Graph` with loop event is correct.

        :param parsed_graph_with_loop: A :class:`Graph` instance that has
        parsed a standardised graph definition.
        :type parsed_graph_with_loop: :class:`Graph`
        :param expected_solutions: The expected solutions.
        :type expected_solutions: `list`[`dict`[`str`, `int`]]
        """
        parsed_graph_with_loop.solve()
        assert len(
            parsed_graph_with_loop.events["Event_Loop"].sub_graph.solutions[
                "Event"
            ]
        ) == 2
        TestSolve.test_solve_sols_correct(
            parsed_graph=parsed_graph_with_loop.events["Event_Loop"].sub_graph,
            expected_solutions=expected_solutions
        )


@pytest.fixture()
def loop_event_graph_solutions() -> dict[str, list[GraphSolution]]:
    """Fixture representing a loop event dictionary
    containing the following two graph solutions:

    * (Event_A)-(Event_B)

    *
              ->(Event_C)-V
    (Event_A)-|           |->(Event_E)
              ->(Event_D)-^


    :return: Returns a dictionary containing a list of :class:`GraphSolution`'s
    :rtype: `dict`[`str`, `list`[:class:`GraphSolution`]]
    """
    event_A = EventSolution(
        meta_data={"EventType": "Event_A"}
    )
    event_B = EventSolution(
        meta_data={"EventType": "Event_B"}
    )
    event_C = EventSolution(
        meta_data={"EventType": "Event_C"}
    )
    event_D = EventSolution(
        meta_data={"EventType": "Event_D"}
    )
    event_E = EventSolution(
        meta_data={"EventType": "Event_E"}
    )
    # solution 1
    event_A_1 = deepcopy(event_A)
    event_B_1 = deepcopy(event_B)
    event_A_1.add_post_event(event_B_1)
    event_A_1.add_to_connected_events()
    graph_solution_1 = GraphSolution()
    graph_solution_1.parse_event_solutions(
        [event_A_1, event_B_1]
    )
    # solution 2
    event_A_2 = deepcopy(event_A)
    event_C_2 = deepcopy(event_C)
    event_D_2 = deepcopy(event_D)
    event_E_2 = deepcopy(event_E)
    event_A_2.add_post_event(event_C_2)
    event_A_2.add_post_event(event_D_2)
    event_A_2.add_to_connected_events()
    event_E_2.add_prev_event(event_C_2)
    event_E_2.add_prev_event(event_D_2)
    event_E_2.add_to_connected_events()
    graph_solution_2 = GraphSolution()
    graph_solution_2.parse_event_solutions(
        [event_A_2, event_C_2, event_D_2, event_E_2]
    )
    return {
        "Event_Loop": [
            graph_solution_1,
            graph_solution_2
        ]
    }


@pytest.fixture
def event_solutions() -> dict[str, EventSolution]:
    """Fixture to create a dictionary of :class:`EventSolution`'s

    :return: Return a dictionary of :class:`EventSolution`'s
    :rtype: `dict`[`str`, :class:`EventSolution`]
    """
    return {
        "Event_A": EventSolution(
            meta_data={"EventType": "Event_A"}
        ),
        "Event_C": EventSolution(
            meta_data={"EventType": "Event_C"}
        ),
        "Event_D": EventSolution(
            meta_data={"EventType": "Event_D"}
        ),
        "Event_E": EventSolution(
            meta_data={"EventType": "Event_E"}
        ),
    }


@pytest.fixture
def graph_solution(
    loop_event_graph_solutions: dict[str, EventSolution]
) -> GraphSolution:
    """Fixture to provide a :class:`GraphSolution` containing a
    :class:`LoopEventSolution` with two sub-graph solutions. The parent graph
    is:

    * (Event_X)->(Event_Loop)->(Event_Y)

    The sub-graph solutions are:

    * (Event_A)-(Event_B)


    *         ->(Event_C)-V
    (Event_A)-|           |->(Event_E)
              ->(Event_D)-^

    :param loop_event_graph_solutions: Fixture providing a dictionary of the
    list of :class:`GraphSolution`'s
    :type loop_event_graph_solutions: `dict`[`str`, :class:`EventSolution`]
    :return: Returns a :class:`GraphSolution` wtih 3 events one a loop event
    with 2 sub-graph solutions
    :rtype: :class:`GraphSolution`
    """
    event_X = EventSolution(
        meta_data={"EventType": "Event_X"}
    )
    event_loop = LoopEventSolution(
        graph_solutions=loop_event_graph_solutions["Event_Loop"],
        meta_data={"EventType": "Event_Loop"}
    )
    event_Y = EventSolution(
        meta_data={"EventType": "Event_Y"}
    )
    event_loop.add_prev_event(event_X)
    event_loop.add_post_event(event_Y)
    event_loop.add_to_connected_events()
    graph = GraphSolution()
    graph.parse_event_solutions(
        [event_X, event_loop, event_Y]
    )
    return graph


class TestGraphGenerateSolutions(TestLoopFixtures):
    """Groups of tests for the generating of :class:`GraphSolution`'s from
    found integer solutions for :class:`Graph`. Sub-classes
    :class:`TestLoopFixtures` to gain the fixtures provided by the parent class
    """
    @staticmethod
    def test_get_event_solution_instances_no_sub_graph_event(
        parsed_graph: Graph,
        expected_solutions: list[dict[str, int]]
    ) -> None:
        """Tests the method :class:`Graph`.`get_event_solution_objects`
        without a loop

        :param parsed_graph: Fixture providing a pre-parsed :class:`Graph`
        :type parsed_graph: :class:`Graph`
        :param expected_solutions: List of expected solutions to the parsed
        :class:`Graph`
        :type expected_solutions: `list`[`dict`[`str`, `int`]]
        """
        event_solutions = Graph.get_event_solution_instances(
            graph_events_solution=expected_solutions[0],
            events=parsed_graph.events,
            events_with_sub_graph_event_solutions={}
        )
        # There should be 2 EventSolution's in the dictionary
        assert len(event_solutions) == 2
        # all of the instances within the dictionary shoul only be
        # EventSolution with no LoopEventSolution's
        assert all(
            isinstance(event_solution, EventSolution)
            and not isinstance(event_solution, LoopEventSolution)
            and not isinstance(event_solution, BranchEventSolution)
            for event_solution in event_solutions.values()
        )

    @staticmethod
    def test_get_event_solution_instances_with_loop(
        parsed_graph_with_loop: Graph,
        expected_solutions_graph_loop_event: list[dict[str, int]],
    ) -> None:
        """Tests the method :class:`Graph`.`get_event_solution_objects`
        with a :class:`LoopEvent`

        :param parsed_graph_with_loop: Fixture providing a parsed
        :class:`Graph` containing a :class:`LoopEvent` with a sub-graph
        :type parsed_graph_with_loop: :class:`Graph`
        :param expected_solutions_graph_loop_event: Fixture providing expected
        solutions for the :class:`Graph` with :class:`LoopEvent`
        :type expected_solutions_graph_loop_event: `list`[`dict`[`str`, `int`]]
        """
        loop_event = LoopEventSolution(
            graph_solutions=[],
            meta_data=parsed_graph_with_loop.events["Event_Loop"].meta_data
        )
        event_solutions = Graph.get_event_solution_instances(
            graph_events_solution=expected_solutions_graph_loop_event[0],
            events=parsed_graph_with_loop.events,
            events_with_sub_graph_event_solutions={
                "Event_Loop": loop_event
            }
        )
        # there should be 3 EventSolution's in the dictionary
        assert len(event_solutions) == 3
        # check that the instances of EventSolution are correct
        assert isinstance(event_solutions["Event_Loop"], LoopEventSolution)
        assert isinstance(event_solutions["Event_X"], EventSolution)
        assert isinstance(event_solutions["Event_Y"], EventSolution)
        # check that the loop event solution is a copy
        assert loop_event != event_solutions["Event_Loop"]

    @staticmethod
    def test_get_event_solution_instances_with_branch(
        parsed_graph_with_branch: Graph,
        expected_solutions_graph_branch_event: list[dict[str, int]],
    ) -> None:
        """Tests the method :class:`Graph`.`get_event_solution_objects`
        with a :class:`BranchEvent`

        :param parsed_graph_with_branch: Fixture providing a parsed
        :class:`Graph` containing a :class:`BranchEvent` with a sub-graph
        :type parsed_graph_with_branch: :class:`Graph`
        :param expected_solutions_graph_branch_event: Fixture providing
        expected
        solutions for the :class:`Graph` with :class:`BranchEvent`
        :type expected_solutions_graph_branch_event: `list`[`dict`[`str`,
        `int`]]
        """
        branch_event = BranchEventSolution(
            graph_solutions=[],
            meta_data=parsed_graph_with_branch.events["Event_Branch"].meta_data
        )
        event_solutions = Graph.get_event_solution_instances(
            graph_events_solution=expected_solutions_graph_branch_event[0],
            events=parsed_graph_with_branch.events,
            events_with_sub_graph_event_solutions={
                "Event_Branch": branch_event
            }
        )
        # there should be 3 EventSolution's in the dictionary
        assert len(event_solutions) == 3
        # check that the instances of EventSolution are correct
        assert isinstance(event_solutions["Event_Branch"], BranchEventSolution)
        assert isinstance(event_solutions["Event_X"], EventSolution)
        assert isinstance(event_solutions["Event_Y"], EventSolution)
        # check that the loop event solution is a copy
        assert branch_event != event_solutions["Event_Branch"]

    @staticmethod
    def check_connected_events_correct(
        event_solution: EventSolution,
        event_solutions_in_prev: list[EventSolution],
        event_solutions_in_post: list[EventSolution]
    ) -> None:
        """Helper function to check that a :class:`EventSolution` contains the
        correct previous and post :class:`EventSolution`'s

        :param event_solution: The :class:`EventSolution` to check
        :type event_solution: :class:`EventSolution`
        :param event_solutions_in_prev: List of :class:`EventSolution`'s that
        should appear in the previous events
        :type event_solutions_in_prev: `list`[:class:`EventSolution`]
        :param event_solutions_in_post: List of :class:`EventSolution`'s that
        should appear in the post events
        :type event_solutions_in_post: `list`[:class:`EventSolution`]
        """
        # check that the len of post events is equal to the input list of post
        # events
        assert len(event_solution.post_events) == len(event_solutions_in_post)
        # check that the len of previous events is equal to the input list of
        # previous events
        assert len(event_solution.previous_events) == len(
            event_solutions_in_prev
        )
        # check that the post and previous events are correct
        for prev_event_solution in event_solutions_in_prev:
            assert (
                prev_event_solution
            ) in event_solution.previous_events
        for post_event_solution in event_solutions_in_post:
            assert (
                post_event_solution
            ) in event_solution.post_events

    @staticmethod
    def test_update_prev_events(
        parsed_graph: Graph,
        event_solutions: dict[str, EventSolution],
        expected_edge_solutions: list[dict[str, int]]
    ) -> None:
        """Test the method :class:`Graph`.`update_connected_events`.
        Tests updating the previous events of Event_E given the
        edge solutions

        "edge_A_B"=0,
        "edge_A_C"=1,
        "edge_A_D"=1,
        "edge_C_E"=1,
        "edge_D_E"=1

        :param parsed_graph: Fixture representing a parsed :class:`Graph`
        :type parsed_graph: :class:`Graph`
        :param event_solutions: Dictionary of :class:`EventSolution`'s
        :type event_solutions: `dict`[`str`, :class:`EventSolution`]
        :param expected_edge_solutions: Fixture representing the expected list
        of dictionaries of edge solutions for the graph
        :type expected_edge_solutions: `list`[`dict`[`str`, `int`]]
        """
        event = parsed_graph.events["Event_E"]
        Graph.update_prev_events(
            event=event,
            event_solution=event_solutions["Event_E"],
            event_solution_instances=event_solutions,
            graph_edges_solution=expected_edge_solutions[1]
        )
        # check that the previous events are correct
        TestGraphGenerateSolutions.check_connected_events_correct(
            event_solution=event_solutions["Event_E"],
            event_solutions_in_prev=[
                event_solutions["Event_C"],
                event_solutions["Event_D"]
            ],
            event_solutions_in_post=[]
        )

    @staticmethod
    def test_update_post_events(
        parsed_graph: Graph,
        event_solutions: dict[str, EventSolution],
        expected_edge_solutions: list[dict[str, int]]
    ) -> None:
        """Test the method :class:`Graph`.`update_connected_events`.
        Tests updating the post events of Event_A given the
        edge solutions

        "edge_A_B"=0,
        "edge_A_C"=1,
        "edge_A_D"=1,
        "edge_C_E"=1,
        "edge_D_E"=1

        :param parsed_graph: Fixture representing a parsed :class:`Graph`
        :type parsed_graph: :class:`Graph`
        :param event_solutions: Dictionary of :class:`EventSolution`'s
        :type event_solutions: `dict`[`str`, :class:`EventSolution`]
        :param expected_edge_solutions: Fixture representing the expected list
        of dictionaries of edge solutions for the graph
        :type expected_edge_solutions: `list`[`dict`[`str`, `int`]]
        """
        event = parsed_graph.events["Event_A"]
        Graph.update_post_events(
            event=event,
            event_solution=event_solutions["Event_A"],
            event_solution_instances=event_solutions,
            graph_edges_solution=expected_edge_solutions[1]
        )
        # check that the post events are correct
        TestGraphGenerateSolutions.check_connected_events_correct(
            event_solution=event_solutions["Event_A"],
            event_solutions_in_prev=[],
            event_solutions_in_post=[
                event_solutions["Event_C"],
                event_solutions["Event_D"]
            ],
        )

    @staticmethod
    def test_update_connected_events(
        parsed_graph: Graph,
        event_solutions: dict[str, EventSolution],
        expected_edge_solutions: list[dict[str, int]]
    ) -> None:
        """Test the method :class:`Graph`.`update_connected_events`.
        Tests updating the post and previous events of Event_C given the
        edge solutions

        "edge_A_B"=0,
        "edge_A_C"=1,
        "edge_A_D"=1,
        "edge_C_E"=1,
        "edge_D_E"=1

        :param parsed_graph: Fixture representing a parsed :class:`Graph`
        :type parsed_graph: :class:`Graph`
        :param event_solutions: Dictionary of :class:`EventSolution`'s
        :type event_solutions: `dict`[`str`, :class:`EventSolution`]
        :param expected_edge_solutions: Fixture representing the expected list
        of dictionaries of edge solutions for the graph
        :type expected_edge_solutions: `list`[`dict`[`str`, `int`]]
        """
        event = parsed_graph.events["Event_C"]
        Graph.update_connected_events(
            event=event,
            event_solution=event_solutions["Event_C"],
            event_solution_instances=event_solutions,
            graph_edges_solution=expected_edge_solutions[1]
        )
        # check that the post and previous events are correct
        TestGraphGenerateSolutions.check_connected_events_correct(
            event_solution=event_solutions["Event_C"],
            event_solutions_in_prev=[
                event_solutions["Event_A"],
            ],
            event_solutions_in_post=[
                event_solutions["Event_E"],
            ],
        )

    @staticmethod
    def test_update_connected_events_for_all_event_solutions(
        parsed_graph: Graph,
        event_solutions: dict[str, EventSolution],
        expected_edge_solutions: list[dict[str, int]]
    ) -> None:
        """Test the method
        :class:`Graph`.`update_connected_events_for_all_event_solutions`.
        Tests updating the post and previous events for all events given the
        edge solutions

        "edge_A_B"=0,
        "edge_A_C"=1,
        "edge_A_D"=1,
        "edge_C_E"=1,
        "edge_D_E"=1

        :param parsed_graph: Fixture representing a parsed :class:`Graph`
        :type parsed_graph: :class:`Graph`
        :param event_solutions: Dictionary of :class:`EventSolution`'s
        :type event_solutions: `dict`[`str`, :class:`EventSolution`]
        :param expected_edge_solutions: Fixture representing the expected list
        of dictionaries of edge solutions for the graph
        :type expected_edge_solutions: `list`[`dict`[`str`, `int`]]
        """
        Graph.update_connected_events_for_all_event_solutions(
            event_solution_instances=event_solutions,
            events=parsed_graph.events,
            graph_edges_solution=expected_edge_solutions[1]
        )
        # check all post and previous events are correct
        for (
            event_solution, event_solutions_in_prev, event_solutions_in_post
        ) in zip(
            event_solutions.values(),
            [
                [],
                [event_solutions["Event_A"]],
                [event_solutions["Event_A"]],
                [event_solutions["Event_C"], event_solutions["Event_D"]],
            ],
            [
                [event_solutions["Event_C"], event_solutions["Event_D"]],
                [event_solutions["Event_E"]],
                [event_solutions["Event_E"]],
                []
            ]
        ):
            TestGraphGenerateSolutions.check_connected_events_correct(
                event_solution=event_solution,
                event_solutions_in_prev=event_solutions_in_prev,
                event_solutions_in_post=event_solutions_in_post
            )

    @staticmethod
    def test_get_solution_unexpanded_graph_solution(
        parsed_graph_with_loop: Graph,
        expected_solutions_graph_loop_event: list[dict[str, int]],
        expected_edge_solutions_graph_loop_event: list[dict[str, int]]
    ) -> None:
        """Tests the method :class:`Graph`.`get_unexpanded_graph_solution`

        :param parsed_graph_with_loop: Fixture representing a parsed
        :class:`Graph` with :class:`LoopEvent`
        :type parsed_graph_with_loop: :class:`Graph`
        :param expected_solutions_graph_loop_event: Fixture providing the
        expected event solutions for the :class:`Graph` with
        :class:`LoopEvent`.
        :type expected_solutions_graph_loop_event: `list`[`dict`[`str`, `int`]]
        :param expected_edge_solutions_graph_loop_event: Fixture providing the
        expected edge solutions for the :class:`Graph` with
        :class:`LoopEvent`.
        :type expected_edge_solutions_graph_loop_event: `list`[`dict`[`str`,
        `int`]]
        """
        loop_event = LoopEventSolution(
            graph_solutions=[],
            meta_data=parsed_graph_with_loop.events["Event_Loop"].meta_data
        )
        graph_solution = Graph.get_unexpanded_graph_solution(
            graph_events_solution=expected_solutions_graph_loop_event[0],
            graph_edges_solution=expected_edge_solutions_graph_loop_event[0],
            events=parsed_graph_with_loop.events,
            events_with_sub_graph_event_solutions={
                "Event_Loop": loop_event
            }
        )
        # The loop event solution from the input
        # "event_with_sub_graph_event_solutions" should not be the same as
        # that for the output graph solution
        assert loop_event != graph_solution.loop_events[2]
        # check the output graph solution is correct
        TestGraphGenerateSolutions.check_simple_graph_correct(
            graph_solution=graph_solution,
            lens=[1, 3, 1, 1, 0, 0],
            event_types=["Event_X", "Event_Loop", "Event_Y"],
            type_dict={2: LoopEventSolution}
        )

    @staticmethod
    def check_simple_graph_correct(
        graph_solution: GraphSolution,
        lens: list[int],
        event_types: list[str],
        type_dict: dict[int, Type[
            EventSolution | LoopEventSolution | BranchEventSolution
        ]]
    ) -> None:
        """Method the check a graph solutions adheres to have the correct
        attribute lengths, the correct sequence and doesn't contain specified
        :class:`EventSolution` instances

        :param graph_solution: Input :class:`GraphSolution`
        :type graph_solution: :class:`GraphSolution`
        :param lens: The length of each of the attributes
        :type lens: `list`[`int`]
        :param event_types: List of event types in a sequence
        :type event_types: `list`[`str`]
        :param type_dict: Dictionary of key and a :class:`EventSolution` that
        shouldn't be found in the input :class:`GraphSolution`
        :type type_dict: `dict`[`int`, :class:`Type`[ :class:`EventSolution`
        | :class:`LoopEventSolution` | :class:`BranchEventSolution` ]]
        """
        assert check_length_attr(
            graph_solution,
            lens=lens,
            attrs=[
                "start_events", "events",
                "end_events", "loop_events",
                "branch_points", "break_points"
            ]
        )
        check_solution_correct(
            solution=graph_solution,
            event_types=event_types
        )
        for key, type_event_sol in type_dict.items():
            assert isinstance(graph_solution.events[key], type_event_sol)

    @staticmethod
    def test_get_unexpanded_graph_solutions(
        parsed_graph_with_loop: Graph,
        expected_solutions_graph_loop_event: list[dict[str, EventSolution]],
        expected_edge_solutions_graph_loop_event: list[dict[str, int]]
    ) -> None:
        """Tests the method :class:`Graph`.`get_unexpanded_graph_solutions`

        :param parsed_graph_with_loop: Fixture representing a parsed
        :class:`Graph` with :class:`LoopEvent`
        :type parsed_graph_with_loop: :class:`Graph`
        :param expected_solutions_graph_loop_event: Fixture providing the
        expected event solutions for the :class:`Graph` with
        :class:`LoopEvent`.
        :type expected_solutions_graph_loop_event: `list`[`dict`[`str`, `int`]]
        :param expected_edge_solutions_graph_loop_event: Fixture providing the
        expected edge solutions for the :class:`Graph` with
        :class:`LoopEvent`.
        :type expected_edge_solutions_graph_loop_event: `list`[`dict`[`str`,
        `int`]]
        """
        loop_event = LoopEventSolution(
            graph_solutions=[],
            meta_data=parsed_graph_with_loop.events["Event_Loop"].meta_data
        )
        graph_solutions = Graph.get_unexpanded_graph_solutions(
            graph_events_solutions=[
                expected_solutions_graph_loop_event[0]
                for _ in range(2)
            ],
            graph_edges_solutions=[
                expected_edge_solutions_graph_loop_event[0]
                for _ in range(2)
            ],
            events=parsed_graph_with_loop.events,
            events_with_sub_graph_event_solutions={
                "Event_Loop": loop_event
            }
        )
        for graph_solution in graph_solutions:
            assert loop_event != graph_solution.loop_events[2]
            TestGraphGenerateSolutions.check_simple_graph_correct(
                graph_solution=graph_solution,
                lens=[1, 3, 1, 1, 0, 0],
                event_types=["Event_X", "Event_Loop", "Event_Y"],
                type_dict={2: LoopEventSolution}
            )

    @staticmethod
    def test_get_nested_unexpanded_graph_solutions_no_sub_graph_events(
        parsed_graph: Graph,
        expected_solutions: list[dict[str, int]],
        expected_edge_solutions: list[dict[str, int]]
    ) -> None:
        """Tests the method
        :class:`Graph`.`get_nested_unexpanded_graph_solutions` when there are
        no :class:`LoopEvent`'s or :class:`BranchEvent`'s

        :param parsed_graph: Fixture representing a parsed :class:`Graph`
        :type parsed_graph: :class:`Graph`
        :param event_solutions: Dictionary of :class:`EventSolution`'s
        :type event_solutions: `dict`[`str`, :class:`EventSolution`]
        :param expected_edge_solutions: Fixture representing the expected list
        of dictionaries of edge solutions for the graph
        :type expected_edge_solutions: `list`[`dict`[`str`, `int`]]
        """
        graph_solutions = Graph.get_nested_unexpanded_graph_solutions(
            graph_events_solutions=expected_solutions,
            graph_edges_solutions=expected_edge_solutions,
            events=parsed_graph.events
        )
        TestGraphGenerateSolutions.check_nested_unexpanded_graph_solutions(
            graph_solutions=graph_solutions
        )

    def check_nested_unexpanded_graph_solutions(
        graph_solutions: list[GraphSolution]
    ) -> None:
        """Method to check that the specified list of :class:`GraphSolution`'s
        has been produced correctly

        :param graph_solutions: List of input :class:`GraphSolution`'s
        :type graph_solutions: `list`[:class:`GraphSolution`]
        """
        graph_sol_1 = graph_solutions[0]
        expected_event_types_sol_1 = ["Event_A", "Event_B"]
        graph_sol_2 = graph_solutions[1]
        expected_event_types_sol_2 = [
            ["Event_A", "Event_C", "Event_E"],
            ["Event_A", "Event_D", "Event_E"]
        ]
        assert len(graph_solutions) == 2
        #######################################################################
        # first solution
        #######################################################################
        # there should be 2 events with 1 start event, 1 end event
        assert check_length_attr(
            graph_sol_1,
            lens=[1, 2, 1, 0, 0, 0],
            attrs=[
                "start_events", "events",
                "end_events", "loop_events",
                "branch_points", "break_points"
            ]
        )
        # check that the events are linked correctly
        assert check_solution_correct(
            solution=graph_sol_1,
            event_types=expected_event_types_sol_1
        )
        #######################################################################
        # second solution
        #######################################################################
        # there should be 4 events with 1 start event, 1 end event
        assert check_length_attr(
            graph_sol_2,
            lens=[1, 4, 1, 0, 0, 0],
            attrs=[
                "start_events", "events",
                "end_events", "loop_events",
                "branch_points", "break_points"
            ]
        )
        # check that the events are linked correctly for first path
        assert check_solution_correct(
            solution=graph_sol_2,
            event_types=expected_event_types_sol_2[0]
        )
        # reverse post events for Event_A
        graph_sol_2.start_events[1].post_events = list(
            reversed(graph_sol_2.start_events[1].post_events)
        )
        # check that the events are linked correctly for second path
        assert check_solution_correct(
            solution=graph_sol_2,
            event_types=expected_event_types_sol_2[1]
        )

    @staticmethod
    def test_process_sub_graph_event_solution(
        parsed_graph_with_loop: Graph
    ) -> None:
        """Tests :class:`Graph`.`process_sub_graph_event_solution` using a
        :class:`Graph` containing a :class:`LoopEvent`

        :param parsed_graph_with_loop: Fixture providing a :class:`Graph` that
        has parsed in a graph definition with a loop
        :type parsed_graph_with_loop: :class:`Graph`
        """
        parsed_graph_with_loop.solve()
        processed_sub_graph_event_solution = (
            Graph.process_sub_graph_event_solution(
                event=parsed_graph_with_loop.events["Event_Loop"]
            )
        )
        # make sure the output is a LoopEventSolution
        assert isinstance(
            processed_sub_graph_event_solution,
            LoopEventSolution
        )
        # sort the graph solutions to get in order for checking
        sorted_graph_solutions = sorted(
            processed_sub_graph_event_solution.graph_solutions,
            key=lambda x: len(x.events)
        )
        # check that the sorted graph solutions are what they should be
        TestGraphGenerateSolutions.check_nested_unexpanded_graph_solutions(
            graph_solutions=sorted_graph_solutions
        )

    @staticmethod
    def test_get_nested_unexpanded_graph_solutions(
        parsed_graph_with_loop: Graph
    ) -> None:
        """Tests :class:`Graph`.`pget_nested_unexpanded_graph_solutions` using
        a :class:`Graph` containing a :class:`LoopEvent`

        :param parsed_graph_with_loop: Fixture providing a :class:`Graph` that
        has parsed in a graph definition with a loop
        :type parsed_graph_with_loop: :class:`Graph`
        """
        parsed_graph_with_loop.solve()
        solutions = parsed_graph_with_loop.solutions
        graph_solutions = Graph.get_nested_unexpanded_graph_solutions(
            graph_events_solutions=solutions["Event"],
            graph_edges_solutions=solutions["Edge"],
            events=parsed_graph_with_loop.events
        )
        # there must be only 1 solution
        assert len(graph_solutions) == 1
        # check that the output GraphSolution is as expected
        TestGraphGenerateSolutions.check_simple_graph_correct(
            graph_solution=graph_solutions[0],
            lens=[1, 3, 1, 1, 0, 0],
            event_types=["Event_X", "Event_Loop", "Event_Y"],
            type_dict={2: LoopEventSolution}
        )
        # sort loop events subgraph solutions for checking
        sorted_sub_graph_graph_solutions = sorted(
            graph_solutions[0].loop_events[2].graph_solutions,
            key=lambda x: len(x.events)
        )
        # check loop events sub graph solutions are correct
        TestGraphGenerateSolutions.check_nested_unexpanded_graph_solutions(
            graph_solutions=sorted_sub_graph_graph_solutions
        )

    @staticmethod
    def test_get_nested_unexpanded_graph_solutions_nested(
        parsed_graph_with_nested_loop_in_branch: Graph
    ) -> None:
        """Tests the method
        :class:`Graph`.`get_nested_unexpanded_graph_solutions` for a
        :class:`Graph` with a :class:`LoopEvent` nested in a
        :class:`BranchEvent`

        :param parsed_graph_with_nested_loop_in_branch: Fixture providing a
        :class:`Graph` that has had a graph definition parsed containing a
        nested :class:`LoopEvent` in a :class:`BranchEvent`
        :type parsed_graph_with_nested_loop_in_branch: :class:`Graph`
        """
        parsed_graph_with_nested_loop_in_branch.solve()
        solutions = parsed_graph_with_nested_loop_in_branch.solutions
        graph_solutions = Graph.get_nested_unexpanded_graph_solutions(
            graph_events_solutions=solutions["Event"],
            graph_edges_solutions=solutions["Edge"],
            events=parsed_graph_with_nested_loop_in_branch.events
        )
        # there should only be 1 solution
        assert len(graph_solutions) == 1
        # check that the parent graph solution is as expected
        TestGraphGenerateSolutions.check_simple_graph_correct(
            graph_solution=graph_solutions[0],
            lens=[1, 3, 1, 0, 1, 0],
            event_types=["Event_X", "Event_Branch", "Event_Y"],
            type_dict={2: BranchEventSolution}
        )
        # check that the sub graph solution of the branch event is as expected
        branch_event = graph_solutions[0].branch_points[2]
        branch_event_sub_graph_solutions = branch_event.graph_solutions
        assert len(branch_event_sub_graph_solutions) == 1
        TestGraphGenerateSolutions.check_simple_graph_correct(
            graph_solution=branch_event_sub_graph_solutions[0],
            lens=[1, 3, 1, 1, 0, 0],
            event_types=["Event_X", "Event_Loop", "Event_Y"],
            type_dict={2: LoopEventSolution}
        )
        # check that the sub graph solution of the nested loop event is as
        # expected
        nested_loop_event = branch_event_sub_graph_solutions[0].loop_events[2]
        nested_loop_event_sub_graph_solutions = (
            nested_loop_event.graph_solutions
        )
        assert len(nested_loop_event_sub_graph_solutions) == 2
        sorted_graph_solutions = sorted(
            nested_loop_event_sub_graph_solutions,
            key=lambda x: len(x.events)
        )
        TestGraphGenerateSolutions.check_nested_unexpanded_graph_solutions(
            graph_solutions=sorted_graph_solutions
        )

    @staticmethod
    def test_get_all_combined_graph_solutions(
        parsed_graph_with_nested_loop_in_branch: Graph
    ) -> None:
        """Test the method :class:`Graph`.`get_all_combined_graph_solutions`
        for a :class:`Graph` with a :class:`LoopEvent` nested in a
        :class:`BranchEvent`

        :param parsed_graph_with_nested_loop_in_branch: Fixture providing a
        :class:`Graph` that has had a graph definition parsed containing a
        nested :class:`LoopEvent` in a :class:`BranchEvent`
        :type parsed_graph_with_nested_loop_in_branch: :class:`Graph`
        """
        graph = parsed_graph_with_nested_loop_in_branch
        graph.solve()
        graph_solutions = graph.get_all_combined_graph_solutions(
            num_loops=1,
            num_branches=2
        )
        # there should only be 3 solutions
        assert len(graph_solutions) == 3
        sequences = [
            [
                "X", "Branch", "X", "A", "B", "Y", "Y"
            ],
            [
                "X", "Branch", "X", "A", "C", "E", "Y", "Y"
            ],
        ]
        sequences = [
            [f"Event_{event_suffix}" for event_suffix in sequence]
            for sequence in sequences
        ]
        sequence_appearance_count = {
            0: 0,
            1: 0
        }
        # check that the two sequences appear 3 times each when traversing the
        # branched sequences
        for graph_sol in graph_solutions:
            copied_graph_0 = deepcopy(graph_sol)
            copied_graph_1 = deepcopy(graph_sol)
            copied_graph_1.branch_points[2].post_events = list(
                reversed(
                    copied_graph_1.branch_points[2].post_events
                )
            )
            for copied_graph in [
                copied_graph_0, copied_graph_1
            ]:
                for i, sequence in enumerate(sequences):
                    if check_solution_correct(
                        copied_graph,
                        sequence
                    ):
                        sequence_appearance_count[i] += 1
        assert all(
            count == 3
            for count in sequence_appearance_count.values()
        )

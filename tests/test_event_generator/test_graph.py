# pylint: disable=R0903
"""
Tests for graph.py
"""
from copy import deepcopy

import pytest
from ortools.sat.python.cp_model import CpModel, CpSolver
from test_event_generator.graph import Graph
from test_event_generator.core.event import Event, LoopEvent
from test_event_generator.core.group import ORGroup, XORGroup, ANDGroup, Group
from test_event_generator.utils.utils import solve_model


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
            graph.groups[("Event_A", "out", "1")].variable.Name() ==
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
        loop_sub_graph_def: dict
    ) -> None:
        """Test that :class:`LoopEvent` instance is created when providing a
        loop sub graph definition.

        :param model: CP-SAT model.
        :type model: :class:`CpModel`
        :param loop_sub_graph_def: Standardised graph definition.
        :type loop_sub_graph_def: `dict`
        """
        event = Graph.create_event(
            model=model,
            loop_graph=loop_sub_graph_def
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
        solutions.values(),
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
        expected_group_solutions: dict[int, dict[str, int]]
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
        :type expected_group_solutions: `dict`[`int`, `dict`[`str`, `int`]]
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
        assert len(parsed_graph.solutions) == 2

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
        actual_solutions = parsed_graph.solutions
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
        loop_sub_graph_def: dict[str, dict],
        sub_graph_edges: list[str]
    ) -> None:
        """Tests the sub graph has been correctly formed from the parsed graph
        definition.

        :param loop_event: The :class:`LoopEvent`
        :type loop_event: :class:`LoopEvent`
        :param loop_sub_graph_def: The graph definition for the loop subgraph.
        :type loop_sub_graph_def: `dict`[`str`, `dict`]
        :param sub_graph_edges: The edge uids in the loop subgraph.
        :type sub_graph_edges: `list`[`str`]
        """
        loop_event_sub_graph: Graph = loop_event.sub_graph
        # test edges added correctly
        TestParseGraphDef.test_edges_added_correctly(
            loop_event_sub_graph,
            sub_graph_edges
        )
        # test events added correctly
        TestParseGraphDef.test_events_added_correctly(
            parsed_graph=loop_event_sub_graph,
            graph_def=loop_sub_graph_def
        )
        # test events contain correct groups
        TestParseGraphDef.test_events_contain_correct_groups(
            parsed_graph=loop_event_sub_graph,
            graph_def=loop_sub_graph_def
        )
        # test start events
        TestParseGraphDef.test_event_is_start(
            parsed_graph=loop_event_sub_graph,
            graph_def=loop_sub_graph_def
        )


class TestSolveLoopSubGraphs(TestLoopFixtures):
    """Tests the solution of LoopEvent subgraphs and helper functions.
    """
    @staticmethod
    @pytest.fixture
    def loop_event(
        model: CpModel,
        loop_sub_graph_def: dict[str, dict]
    ) -> LoopEvent:
        """PyTest fixture to define :class:`LoopEvent`.

        :param model: CP-SAT model
        :type model: :class`CpModel`
        :param loop_sub_graph_def: Standardised graph definition for the loop
        sub graph.
        :type loop_sub_graph_def: `dict`[`str`, `dict`]
        :return: Returns the loop event with sub graph definied by the input
        graph definition.
        :rtype: :class:`LoopEvent`
        """
        sub_graph = Graph()
        event = LoopEvent(
            model=model,
            sub_graph=sub_graph
        )
        event.set_graph_with_graph_def(loop_sub_graph_def)
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
        expected_solutions_sub_graph: list[dict[str, int]]
    ) -> None:
        """Tests :class:`Graph`.`solve_loop_events_sub_graphs` gives the
        corrrect solutions.

        :param events_list: Mixed list of :class:`Event`'s and
        :class:`LoopEvent`'s.
        :type events_list: `list`[:class:`Event` | :class:`LoopEvent`]
        :param expected_solutions_sub_graph: List of expected solutions.
        :type expected_solutions_sub_graph: `list`[`dict`[`str`, `int`]]
        """
        filtered_events = Graph.filter_events(events_list)
        Graph.solve_loop_events_sub_graphs(filtered_events)
        for event in filtered_events:
            assert len(event.sub_graph.solutions) == 2
            TestSolve.test_solve_sols_correct(
                parsed_graph=event.sub_graph,
                expected_solutions=expected_solutions_sub_graph
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
        assert len(parsed_graph_with_loop.solutions) == 1
        TestSolve.test_solve_sols_correct(
            parsed_graph=parsed_graph_with_loop,
            expected_solutions=expected_solutions_graph_loop_event
        )

    @staticmethod
    def test_solve_graph_with_loop_sub_graph(
        parsed_graph_with_loop: Graph,
        expected_solutions_sub_graph: list[dict[str, int]]
    ) -> None:
        """Tests that the solution to the sub graph of the :class:`LoopEvent`
        in the main :class:`Graph` with loop event is correct.

        :param parsed_graph_with_loop: A :class:`Graph` instance that has
        parsed a standardised graph definition.
        :type parsed_graph_with_loop: :class:`Graph`
        :param expected_solutions_sub_graph: The expected solutions.
        :type expected_solutions_sub_graph: `list`[`dict`[`str`, `int`]]
        """
        parsed_graph_with_loop.solve()
        assert len(
            parsed_graph_with_loop.events["Event_Loop"].sub_graph.solutions
        ) == 2
        TestSolve.test_solve_sols_correct(
            parsed_graph=parsed_graph_with_loop.events["Event_Loop"].sub_graph,
            expected_solutions=expected_solutions_sub_graph
        )

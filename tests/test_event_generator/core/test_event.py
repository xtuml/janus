# pylint: disable=R1732
"""Testing event.py.py
"""
from ortools.sat.python.cp_model import CpModel, CpSolver
from test_event_generator.core.event import Event, LoopEvent
from test_event_generator.core.edge import Edge
from test_event_generator.core.group import Group
from test_event_generator.graph import Graph
from test_event_generator.utils.utils import solve_model


def test_event_is_correct(model: CpModel) -> None:
    """Test setting a groups event through :class:`Event.set_groups_event`

    :param model: CP-SAT model
    :type model: :class:`CpModel`
    """
    edge = Edge(model, "edge")
    group = Group(model, "group", [edge], is_into_event=True)
    event = Event(model)

    event.set_groups_event(group=group)

    assert group.event == event


class TestSetFlowConstraint:
    """Class to group test flow constraints into and out of events when the
    Event is instantiated.
    """
    def test_flow_conservation(self, model: CpModel, solver: CpSolver) -> None:
        """Test flow conservation when in and out :class:`Groups` are present.
        There should be two solutions satisfying flow conservation:
        * group_in = group_out = 0
        * group_in = group_out = 1

        :param model: CP-SAT model
        :type model: :class:`CpModel`
        :param solver: CP-SAT solver
        :type solver: :class:`CpSolver`
        """
        group_in = Group(
            model=model,
            uid="group_in",
            group_variables=[],
            is_into_event=True
        )
        group_out = Group(
            model=model,
            uid="group_out",
            group_variables=[],
            is_into_event=False
        )
        _ = Event(model=model, in_group=group_in, out_group=group_out)
        solutions = solve_model(
            model=model,
            solver=solver,
            variables=[group_in.variable, group_out.variable]
        )
        # sort solutions so that the solution with all variables equal to 0 is
        # first and all variables equal to 1 is second
        sorted_solutions = sorted(
            solutions.values(),
            key=lambda x: x["group_in"]
        )
        variables_to_equal = [0, 1]
        assert len(sorted_solutions) == 2
        for i, solution in enumerate(sorted_solutions):
            assert variables_to_equal[i] == solution["group_in"]
            assert solution["group_in"] == solution["group_out"]

    def test_start_point(self, model: CpModel, solver: CpSolver) -> None:
        """Test start constraints when only a :class:`Group` exiting the Event
        is present. Test that the event property is_start evaluates to `True`.
        There should be two solutions:
        * group_out = 1
        * group_out = 0

        :param model: CP-SAT model
        :type model: :class:`CpModel`
        :param solver: CP-SAT solver
        :type solver: :class:`CpSolver`
        """
        group_out = Group(
            model=model,
            uid="group_out",
            group_variables=[],
            is_into_event=False
        )
        event = Event(model=model, out_group=group_out)
        solutions = solve_model(
            model=model,
            solver=solver,
            variables=[group_out.variable]
        )
        # check that Event is_start
        assert event.is_start
        # sort solutions so that the solution with all variables equal to 0 is
        # first and all variables equal to 1 is second
        sorted_solutions = sorted(
            solutions.values(),
            key=lambda x: x["group_out"]
        )
        variables_to_equal = [0, 1]
        assert len(sorted_solutions) == 2
        for i, solution in enumerate(sorted_solutions):
            assert variables_to_equal[i] == solution["group_out"]

    def test_end_point(self, model: CpModel, solver: CpSolver) -> None:
        """Test start constraints when only a :class:`Group` entering the Event
        is present. Test that the event property is_end evaluates to `True`.
        There should be two solutions:
        * group_in = 1
        * group_in = 0

        :param model: CP-SAT model
        :type model: :class:`CpModel`
        :param solver: CP-SAT solver
        :type solver: :class:`CpSolver`
        """
        group_in = Group(
            model=model,
            uid="group_in",
            group_variables=[],
            is_into_event=False
        )
        event = Event(model=model, in_group=group_in)
        solutions = solve_model(
            model=model,
            solver=solver,
            variables=[group_in.variable]
        )
        # check that Event is_end
        assert event.is_end
        # sort solutions so that the solution with all variables equal to 0 is
        # first and all variables equal to 1 is second
        sorted_solutions = sorted(
            solutions.values(),
            key=lambda x: x["group_in"]
        )
        variables_to_equal = [0, 1]
        assert len(sorted_solutions) == 2
        for i, solution in enumerate(sorted_solutions):
            assert variables_to_equal[i] == solution["group_in"]


def test_set_graph_with_graph_def(
    model: CpModel,
    graph_def: dict[str, dict]
) -> None:
    """Test to check that no errors are thrown when calling
    :class:`LoopEvent`.`set_graph_with_graph_def`. All subfunctions of
    the method have been tested so only a check is needed for no errors.

    :param model: CP-SAT model.
    :type model: :class:`CpModel`
    :param loop_sub_graph_def: Standard graph definition.
    :type loop_sub_graph_def: `dict`[`str`, `dict`]
    """
    graph = Graph()
    loop_event = LoopEvent(
        model=model,
        sub_graph=graph
    )
    loop_event.set_graph_with_graph_def(graph_def)

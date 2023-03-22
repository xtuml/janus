# pylint: disable=R1732
"""Testing event.py.py
"""
from ortools.sat.python.cp_model import CpModel, CpSolver
from test_event_generator.core.event import Event
from test_event_generator.core.edge import Edge
from test_event_generator.core.group import Group
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

    def test_source_constraint(self, model: CpModel, solver: CpSolver) -> None:
        """Test source constraint when only a :class:`Group` exiting the Event
        is present. The Event must attribute `is_source = True`.
        There should be one solution satisfying flow:
        * group_out = 1

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
        _ = Event(model=model, out_group=group_out, is_source=True)
        solutions = solve_model(
            model=model,
            solver=solver,
            variables=[group_out.variable]
        )
        assert len(solutions) == 1
        assert solutions[0]["group_out"] == 1

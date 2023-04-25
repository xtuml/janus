"""
Utility functions to help with testing
"""
from __future__ import annotations
from typing import Iterable, TYPE_CHECKING
if TYPE_CHECKING:
    from test_event_generator.solutions import EventSolution, GraphSolution


def check_length_attr(
    obj: object,
    lens: int | list[int],
    attrs: list[str]
) -> bool:
    """Helper function to check the length of a attributes

    :param obj: Generic python `object`
    :type obj: `object`
    :param lens: Integer or list of integers giving the length of each
    attribute
    :type lens: `int` | `list`[`int`]
    :param attrs: List of attribute names
    :type attrs: `list`[`str`]
    :raises RuntimeError: Raises :class:`RuntimeError` if the lens list and
    attrs list are not of equal length
    :return: Returns a `bool` indicating if all the lengths of the attributes
    are correct or not
    :rtype: `bool`
    """
    if isinstance(lens, int):
        lens = [lens] * len(attrs)
    else:
        if len(lens) != len(attrs):
            raise RuntimeError("lens and attrs must be of same length")
    return all(
        len(getattr(obj, attr)) == lens[i]
        for i, attr in enumerate(attrs)
    )


def check_solution_correct(
    solution: GraphSolution,
    event_types: list[str]
) -> bool:
    """Helper method to check that a :class:`GraphSolution` event sequence is
    correct

    :param solution: The :class:`GraphSolution` to check
    :type solution: :class:`GraphSolution`
    :param event_types: The list of EventTypes to check (in order)
    :type event_types: `list`[`str`]
    :return: Returns a boolean indicating if all the event types matched
    :rtype: `bool`
    """
    events = [solution.start_events[1]]
    event_types_correct = []
    for event_type in event_types:
        event_types_correct.append(
            events[-1].meta_data["EventType"] == event_type
        )
        if not events[-1].is_end:
            assert events[-1] in events[-1].post_events[0].previous_events
            events.append(events[-1].post_events[0])
    return all(event_types_correct)


def check_multiple_solutions_correct(
        solutions: list[GraphSolution],
        event_types_sequences: list[list[str]]
) -> None:
    """Helper function to check if all solutions in a list of
    :class:`GraphSolution` are correct

    :param solutions: List of :class:`GraphSolution` to check
    :type solutions: `list`[:class:`GraphSolution`]
    :param event_types_sequences: A list of list of expected EventTypes in
    order
    :type event_types_sequences: `list`[`list`[`str`]]
    """
    for event_types in event_types_sequences:
        assert len([
            True
            for solution in solutions
            if check_solution_correct(
                solution=solution,
                event_types=event_types
            )
        ]) == 1


def add_event_type_suffix(
    events: Iterable[EventSolution],
    suffix: str
) -> None:
    """Helper function to add a suffix to EventTypes in an :class:`Iterable`
    of :class:`EventSolution`'s

    :param events: :class:`Iterable` of :class:`EventSolution`
    :type events: :class:`Iterable`[:class:`EventSolution`]
    :param suffix: Suffix to add
    :type suffix: `str`
    """
    for event in events:
        event.meta_data["EventType"] += f"_{suffix}"

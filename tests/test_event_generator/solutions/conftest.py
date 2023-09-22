"""Fixtures for tests for solutions.py
"""
from copy import deepcopy

import pytest
from test_event_generator.solutions import (
    EventSolution,
    LoopEventSolution,
    BranchEventSolution,
    GraphSolution
)


@pytest.fixture()
def event_solution() -> EventSolution:
    """Fixture to create :class:`EventSolution` with meta-data
    attached

    :return: :class:`EventSolution` with meta-data
    :rtype: :class:`EventSolution`
    """
    return EventSolution(meta_data={"EventType": "Middle"})


@pytest.fixture()
def prev_event_solution() -> EventSolution:
    """Fixture to create :class:`EventSolution` with meta-data
    attached

    :return: :class:`EventSolution` with meta-data
    :rtype: :class:`EventSolution`
    """
    return EventSolution(meta_data={"EventType": "Start"})


@pytest.fixture()
def post_event_solution() -> EventSolution:
    """Fixture to create :class:`EventSolution` with meta-data
    attached

    :return: :class:`EventSolution` with meta-data
    :rtype: :class:`EventSolution`
    """
    return EventSolution(meta_data={"EventType": "End"})


@pytest.fixture()
def graph_solution() -> GraphSolution:
    """Fixture to instantiate a clean :class:`GraphSolution` instance.

    :return: Instance of :class:`GraphSolution`
    :rtype: :class:`GraphSolution`
    """
    return GraphSolution()


@pytest.fixture()
def graph_simple(
    event_solution: EventSolution,
    prev_event_solution: EventSolution,
    post_event_solution: EventSolution
) -> GraphSolution:
    """Fixture to set up a :class:`GraphSolution` instance containing a
    sequence of simply linked :class:`EventSolution`'s as below:

                    (Start)->(Middle)->(End)


    :param event_solution: Middle :class:`EventSolution`
    :type event_solution: :class:`EventSolution`
    :param prev_event_solution: Start :class:`EventSolution`
    :type prev_event_solution: :class:`EventSolution`
    :param post_event_solution: End :class:`EventSolution`
    :type post_event_solution: :class:`EventSolution`
    :return: Returns the :class:`GraphSolution` containing the
    :class:`EventSolution` sequence
    :rtype: :class:`GraphSolution`
    """
    graph_solution = GraphSolution()
    # copy fixtures so there are no conflicts with other fixtures
    prev_event_solution = deepcopy(prev_event_solution)
    post_event_solution = deepcopy(post_event_solution)
    event_solution = deepcopy(event_solution)
    # add 'Start' event to 'Middle' events previous events
    event_solution.add_prev_event(prev_event_solution)
    # add 'End' event to 'Middle' events post events
    event_solution.add_post_event(post_event_solution)
    # add 'Middle' event to 'Start' post events and 'End' previous events
    event_solution.add_to_connected_events()
    # parse EventSolution's into GraphSolution instance
    graph_solution.parse_event_solutions([
        prev_event_solution, event_solution, post_event_solution
    ])
    return graph_solution


@pytest.fixture()
def graph_two_start_two_end(
    event_solution: EventSolution,
    prev_event_solution: EventSolution,
    post_event_solution: EventSolution
) -> GraphSolution:
    """Fixture to set up a :class:`GraphSolution` instance containing a
    sequence of linked :class:`EventSolution`'s with two 'Start' and two 'End'
    points as below:

    (Start)->(      )->(End)
             (Middle)
    (Start)->(      )->(End)



    :param event_solution: Middle :class:`EventSolution`
    :type event_solution: :class:`EventSolution`
    :param prev_event_solution: Start :class:`EventSolution`
    :type prev_event_solution: :class:`EventSolution`
    :param post_event_solution: End :class:`EventSolution`
    :type post_event_solution: :class:`EventSolution`
    :return: Returns the :class:`GraphSolution` containing the
    :class:`EventSolution` sequence
    :rtype: :class:`GraphSolution`
    """
    graph_solution = GraphSolution()
    # copy fixture EventSolution's so there are no fixture conflicts
    prev_event_solution = deepcopy(prev_event_solution)
    post_event_solution = deepcopy(post_event_solution)
    event_solution = deepcopy(event_solution)
    # copy 'Start' and 'End' events
    prev_event_solution_copy = deepcopy(prev_event_solution)
    post_event_solution_copy = deepcopy(post_event_solution)
    # add both 'Start' events to the 'Middle' events previous events
    event_solution.add_prev_event(prev_event_solution)
    event_solution.add_prev_event(prev_event_solution_copy)
    # add both 'End' events to the 'Middle' events post events
    event_solution.add_post_event(post_event_solution)
    event_solution.add_post_event(post_event_solution_copy)
    # update 'Start' events ppost events with 'Middle' event and update 'End'
    # events previous events with 'Middle' event
    event_solution.add_to_connected_events()
    # add EventSolution's to the GraphSolution
    graph_solution.parse_event_solutions([
        prev_event_solution, prev_event_solution_copy,
        event_solution, post_event_solution, post_event_solution_copy
    ])
    # identify the 'Start' events as 'Start_0' and 'Start_1'
    for i, event in enumerate(
        graph_solution.start_events.values()
    ):
        event.meta_data["EventType"] += f"_{i}"
    # identify the 'End' events as 'End_0' and 'End_1'
    for i, event in enumerate(
        graph_solution.end_events.values()
    ):
        event.meta_data["EventType"] += f"_{i}"
    return graph_solution


@pytest.fixture()
def loop_event_solution(
    graph_simple: GraphSolution
) -> LoopEventSolution:
    """Fixture to create a :class:`LoopEventSolution` containing three
    :class:`GraphSolution`'s. The first is

    ``(Start)->(Middle)->(End)``

    The second is the same

    ``(Start)->(Middle)->(End)``

    The third is

    ``(Start)->(Middle)->(End, is_break=True)``

    :param graph_simple: Fixture representing a simple 3 event sequence
    :type graph_simple: :class:`GraphSolution`
    :return: Returns :class:`LoopEventSolution` instance that holds three
    :class:`GraphSolution`
    :rtype: :class:`LoopEventSolution`
    """
    graph_with_break = deepcopy(graph_simple)
    graph_with_break.events[3].is_break_point = True
    graph_with_break.break_points[3] = graph_with_break.events[3]
    loop_event = LoopEventSolution(
        graph_solutions=[
            deepcopy(graph_simple),
            deepcopy(graph_simple),
            graph_with_break
        ]
    )
    return loop_event


@pytest.fixture
def graph_single_event(
    event_solution: EventSolution
) -> GraphSolution:
    graph = GraphSolution()
    graph.add_event(deepcopy(event_solution))
    return graph


@pytest.fixture
def branch_event_solution(
    graph_single_event: GraphSolution,
    graph_simple: GraphSolution
) -> BranchEventSolution:
    branch_event = BranchEventSolution(
        graph_solutions=[
            deepcopy(graph_single_event),
            deepcopy(graph_simple)
        ],
        meta_data={
            "EventType": "Branch"
        }
    )
    return branch_event


@pytest.fixture()
def graph_with_branch(
    branch_event_solution: BranchEventSolution,
    prev_event_solution: EventSolution,
    post_event_solution: EventSolution,
) -> GraphSolution:
    """Fixture to generate a :class:`GraphSolution` with a branch point. The
    sequence is

    (Start)->(Branch, graph_solutions = [
        (Middle),
        (Start)->(Middle)->(End)
    ])->(End)

    """
    branch_event = deepcopy(branch_event_solution)
    prev_event = deepcopy(prev_event_solution)
    post_event = deepcopy(post_event_solution)
    branch_event.add_prev_event(prev_event)
    branch_event.add_post_event(post_event)
    branch_event.add_to_connected_events()
    graph = GraphSolution()
    graph.parse_event_solutions([prev_event, branch_event, post_event])
    return graph


@pytest.fixture()
def graph_with_loop(
    prev_event_solution: EventSolution,
    event_solution: EventSolution,
    post_event_solution: EventSolution
) -> GraphSolution:
    """Fixture to generate a :class:`GraphSolution` containing a
    :class:`LoopEventSolution` containing a :class:`GraphSolution` with only
    one :class:`EventSolution`. The parent graph sequence is:

    (Start)->(Loop)->(End)

    The sub-graph within the loop event is:

    (Middle)

    :param prev_event_solution: Start :class:`EventSolution`
    :type prev_event_solution: :class:`EventSolution`
    :param event_solution: Middle :class:`EventSolution`
    :type event_solution: :class:`EventSolution`
    :param post_event_solution: End :class:`EventSolution`
    :type post_event_solution: :class:`EventSolution`
    :return: Returns the :class:`GraphSolution` containing the
    :class:`EventSolution` and :class:`LoopEventSolution` sequence.
    :rtype: :class:`GraphSolution`
    """
    prev_event_solution = deepcopy(prev_event_solution)
    event_solution = deepcopy(event_solution)
    post_event_solution = deepcopy(post_event_solution)
    single_event_graph = GraphSolution()
    single_event_graph.add_event(event_solution)
    loop_event_solution = LoopEventSolution(
        graph_solutions=[single_event_graph],
        meta_data={"EventType": "Loop"}
    )
    graph = GraphSolution()
    loop_event_solution.add_prev_event(prev_event_solution)
    loop_event_solution.add_post_event(post_event_solution)
    loop_event_solution.add_to_connected_events()
    graph.parse_event_solutions([
        prev_event_solution,
        loop_event_solution,
        post_event_solution
    ])
    return graph


@pytest.fixture()
def graph_with_nested_loop(
    graph_with_loop: GraphSolution,
) -> GraphSolution:
    """Fixture to create a :class:`GraphSolution` containing a nested loop.
    The parent graph is:

    (Start_upper)->(Loop_upper)->(End_upper)

    The sub graph is (within the Event Loop_upper):

    (Start_nested)->(Loop_nested)->(End_nested)

    The sub-sub-graph (within the event Loop_nested):

    (Middle)

    :param graph_with_loop: Fixture for a :class:`GraphSolution` with a loop
    :type graph_with_loop: :class:`GraphSolution`
    :return: Returns a :class:`GraphSolution` with a nested loop
    :rtype: :class:`GraphSolution`
    """
    graph = deepcopy(graph_with_loop)
    # for event in graph.events.values():
    #     event.meta_data["EventType"] += "_upper"
    nested_loop_graph = deepcopy(graph_with_loop)
    # for event in nested_loop_graph.events.values():
    #     event.meta_data["EventType"] += "_nested"
    graph.loop_events[2].graph_solutions = [
        deepcopy(nested_loop_graph)
    ]
    return graph


@pytest.fixture
def graph_branch_event_id_tuple(
    graph_with_branch: GraphSolution
) -> GraphSolution:
    """Pytest fixture to provide a :class:`GraphSolution` with
    :class:`BranchEventSolution` with the events `event_id_tuple` attribute
    updated

    :param graph_with_branch: Fixture providing :class:`GraphSolution` with a
    :class:`BranchEventSolution`
    :type graph_with_branch: :class:`GraphSolution`
    :return: Returns the :class:`GraphSolution` with updated attribute
    :rtype: :class:`GraphSolution`
    """
    graph = deepcopy(graph_with_branch)
    for event in graph.events.values():
        event.event_id_tuple = (event.meta_data["EventType"], 0)
    return graph


@pytest.fixture
def graph_loop_event_count_id_tuple(
    graph_with_loop: GraphSolution
) -> GraphSolution:
    """Pytest fixture to provide a :class:`GraphSolution` with
    :class:`LoopEventSolution` with the events `event_id_tuple` attribute
    updated and dynamic control loop count added before the loop and inside
    the loop

    :param graph_with_loop: Fixture providing a :class:`GraphSolution`
    containing a :class:`LoopEventSolution` with sub :class:`GraphSolution`
    :type graph_with_loop: :class:`GraphSolution`
    :return: Returns the updated :class:`GraphSolution`
    :rtype: :class:`GraphSolution`
    """
    graph = deepcopy(graph_with_loop)
    events = list(graph.events.values()) + [
        event
        for graph_sol in graph.loop_events[2].graph_solutions
        for event in graph_sol.events.values()
    ]
    GraphSolution.update_event_type_counts(events)
    for event in events:
        event.event_id_tuple = (event.meta_data["EventType"], event.count)
    provider_event = graph.events[1]
    user_event = graph.loop_events[2].graph_solutions[0].events[1]
    dynamic_control_events = {
        "X": {
            "control_type": "LOOPCOUNT",
            "provider": {
                "EventType": provider_event.event_id_tuple[0],
                "occurenceId": provider_event.event_id_tuple[1],
            },
            "user": {
                "EventType": user_event.event_id_tuple[0],
                "occurenceId": user_event.event_id_tuple[1],
            }
        }
    }
    provider_event.parse_dynamic_control_events(
        dynamic_control_events
    )
    user_event.parse_dynamic_control_events(
        dynamic_control_events
    )
    return graph


@pytest.fixture
def graph_multiple_branches(
    graph_with_branch: GraphSolution,
) -> GraphSolution:
    """Pytest fixture to provide a :class:`GraphSolution` containing multiple
    un-nested :class:`BranchEventSolution`'s

    :param graph_with_branch: Fixture providing a :class:`GraphSolution` with
    a single :class:`BranchEventSolution`
    :type graph_with_branch: :class:`GraphSolution`
    :return: Returns the updated :class:`GraphSolution` containing two
    :class:`BranchEventSolution`'s
    :rtype: :class:`GraphSolution`
    """
    graph = graph_with_branch + graph_with_branch
    GraphSolution.update_event_type_counts(
        graph.events.values()
    )
    for event in graph.events.values():
        event.event_id_tuple = (event.meta_data["EventType"], event.count)
    return graph


@pytest.fixture
def graph_multiple_loop_events(
    graph_with_loop: GraphSolution
) -> GraphSolution:
    """Pytest fixture providing a :class:`GraphSolution` containing multiple
    un-nested :class:`LoopEventSolution`'s with the events `event_id_tuple`
    attribute updated and dynamic control loop count added before the loops
    and inside the loops

    :param graph_with_loop: Fixture providing :class:`GraphSolution`
    containing a single :class:`LoopEventSolution`
    :type graph_with_loop: :class:`GraphSolution`
    :return: Returns the updated :class:`GraphSolution` containing two
    :class:`LoopEventSolution`s
    :rtype: :class:`GraphSolution`
    """
    graph_with_loop_copy = deepcopy(graph_with_loop)
    graph_with_loop_copy.loop_events[2].graph_solutions = [
        deepcopy(graph_with_loop_copy.loop_events[2].graph_solutions[0])
    ]
    graph = graph_with_loop + graph_with_loop_copy
    events = list(graph.events.values()) + [
        event
        for loop_event in graph.loop_events.values()
        for graph_sol in loop_event.graph_solutions
        for event in graph_sol.events.values()
    ]
    GraphSolution.update_event_type_counts(events)
    for event in events:
        event.event_id_tuple = (event.meta_data["EventType"], event.count)
    for provider_key, user_key in [(1, 2), (4, 5)]:
        provider_event = graph.events[provider_key]
        user_event = graph.loop_events[user_key].graph_solutions[0].events[1]
        dynamic_control_events = {
            "X": {
                "control_type": "LOOPCOUNT",
                "provider": {
                    "EventType": provider_event.event_id_tuple[0],
                    "occurenceId": provider_event.event_id_tuple[1],
                },
                "user": {
                    "EventType": user_event.event_id_tuple[0],
                    "occurenceId": user_event.event_id_tuple[1],
                }
            }
        }
        provider_event.parse_dynamic_control_events(
            dynamic_control_events
        )
        user_event.parse_dynamic_control_events(
            dynamic_control_events
        )
    return graph


@pytest.fixture
def graph_branch_nested_branch(
    graph_with_branch: GraphSolution
) -> GraphSolution:
    """Pytest fixture providing a :class:`GraphSolution` containing a
    :class:`BranchEventSolution` containg another nested
    :class:`BranchEventSolution` within its sub :class:`GraphSolution`.
    The provider of the dynamic control for the nested
    :class:`BranchEventSolution` is itself.

    :param graph_with_branch: Fixture providing :class:`GraphSolution`
    containing a :class:`BranchEventSolution`
    :type graph_with_branch: :class:`GraphSolution`
    :return: Returns the update :class:`GraphSolution` with nested
    :class:`BranchEventSolution`'s
    :rtype: :class:`GraphSolution`
    """
    graph = deepcopy(graph_with_branch)
    graph.branch_points[2].graph_solutions = [deepcopy(graph_with_branch)]
    events = list(graph.events.values()) + [
        event
        for branch_event in graph.branch_points.values()
        for graph_sol in branch_event.graph_solutions
        for event in graph_sol.events.values()
    ]
    GraphSolution.update_event_type_counts(events)
    for event in events:
        event.event_id_tuple = (event.meta_data["EventType"], event.count)
    branch_events = [
        graph.branch_points[2],
        graph.branch_points[2].graph_solutions[0].branch_points[2],
    ]
    for event in branch_events:
        event.parse_dynamic_control_events(
            {
                "X": {
                    "control_type": "BRANCHCOUNT",
                    "provider": {
                        "EventType": event.event_id_tuple[0],
                        "occurenceId": event.event_id_tuple[1]
                    },
                    "user": {
                        "EventType": event.event_id_tuple[0],
                        "occurenceId": event.event_id_tuple[1]
                    }
                }
            }
        )
    return graph


@pytest.fixture
def graph_branch_nested_branch_prov_outside(
    graph_with_branch: GraphSolution
) -> GraphSolution:
    """Pytest fixture providing a :class:`GraphSolution` containing a
    :class:`BranchEventSolution` containg another nested
    :class:`BranchEventSolution` within its sub :class:`GraphSolution`.
    The provider of the dynamic control for the nested
    :class:`BranchEventSolution` is outside of the top level
    :class:`BranchEventSolution`.

    :param graph_with_branch: Fixture providing :class:`GraphSolution`
    containing a :class:`BranchEventSolution`
    :type graph_with_branch: :class:`GraphSolution`
    :return: Returns the update :class:`GraphSolution` with nested
    :class:`BranchEventSolution`'s with provider outside
    :rtype: :class:`GraphSolution`
    """
    graph = deepcopy(graph_with_branch)
    graph.branch_points[2].graph_solutions = [deepcopy(graph_with_branch)]
    events = list(graph.events.values()) + [
        event
        for branch_event in graph.branch_points.values()
        for graph_sol in branch_event.graph_solutions
        for event in graph_sol.events.values()
    ]
    GraphSolution.update_event_type_counts(events)
    for event in events:
        event.event_id_tuple = (event.meta_data["EventType"], event.count)

    nested_provider = graph.events[1]
    nested_user = graph.branch_points[2].graph_solutions[0].branch_points[2]
    for event in [nested_provider, nested_user]:
        event.parse_dynamic_control_events(
            {
                "X": {
                    "control_type": "BRANCHCOUNT",
                    "provider": {
                        "EventType": nested_provider.event_id_tuple[0],
                        "occurenceId": nested_provider.event_id_tuple[1]
                    },
                    "user": {
                        "EventType": nested_user.event_id_tuple[0],
                        "occurenceId": nested_user.event_id_tuple[1]
                    }
                }
            }
        )
    graph.branch_points[2].parse_dynamic_control_events(
        {
            "X": {
                "control_type": "BRANCHCOUNT",
                "provider": {
                    "EventType": graph.branch_points[2].event_id_tuple[0],
                    "occurenceId": graph.branch_points[2].event_id_tuple[1],
                },
                "user": {
                    "EventType": graph.branch_points[2].event_id_tuple[0],
                    "occurenceId": graph.branch_points[2].event_id_tuple[1],
                }
            }
        }
    )
    return graph


@pytest.fixture
def graph_branch_nested_loop_prov_outside(
    graph_with_branch: GraphSolution,
    graph_with_loop: GraphSolution
) -> GraphSolution:
    """Pytest fixture providing a :class:`GraphSolution` containing a
    :class:`BranchEventSolution` containg a nested
    :class:`LoopEventSolution` within its sub :class:`GraphSolution`.
    The provider of the dynamic control for the nested
    :class:`LoopEventSolution` is outside of the top level
    :class:`BranchEventSolution`.

    :param graph_with_branch: Fixture providing :class:`GraphSolution`
    containing a :class:`BranchEventSolution`
    :type graph_with_branch: :class:`GraphSolution`
    :param graph_with_loop: Fixture providing :class:`GraphSolution`
    containing a single :class:`LoopEventSolution`
    :return: Returns the updated :class:`GraphSolution` with
    :class:`LoopEventSolution` nested in the :class:`BranchEventSolution`
    :rtype: :class:`GraphSolution`
    """
    graph = deepcopy(graph_with_branch)
    graph.branch_points[2].graph_solutions = [deepcopy(graph_with_loop)]
    events = list(graph.events.values()) + [
        event
        for branch_event in graph.branch_points.values()
        for graph_sol in branch_event.graph_solutions
        for event in graph_sol.events.values()
    ] + [
        event
        for branch_event in graph.branch_points.values()
        for graph_sol in branch_event.graph_solutions
        for loop_event in graph_sol.loop_events.values()
        for nested_graph_sol in loop_event.graph_solutions
        for event in nested_graph_sol.events.values()
    ]
    GraphSolution.update_event_type_counts(events)
    for event in events:
        event.event_id_tuple = (event.meta_data["EventType"], event.count)

    nested_provider = graph.events[1]
    nested_user = (
        graph.branch_points[2].graph_solutions[0].loop_events[2].
        graph_solutions[0].events[1]
    )
    for event in [nested_provider, nested_user]:
        event.parse_dynamic_control_events(
            {
                "X": {
                    "control_type": "LOOPCOUNT",
                    "provider": {
                        "EventType": nested_provider.event_id_tuple[0],
                        "occurenceId": nested_provider.event_id_tuple[1]
                    },
                    "user": {
                        "EventType": nested_user.event_id_tuple[0],
                        "occurenceId": nested_user.event_id_tuple[1]
                    }
                }
            }
        )
    graph.branch_points[2].parse_dynamic_control_events(
        {
            "X": {
                "control_type": "BRANCHCOUNT",
                "provider": {
                    "EventType": graph.branch_points[2].event_id_tuple[0],
                    "occurenceId": graph.branch_points[2].event_id_tuple[1],
                },
                "user": {
                    "EventType": graph.branch_points[2].event_id_tuple[0],
                    "occurenceId": graph.branch_points[2].event_id_tuple[1],
                }
            }
        }
    )
    return graph


@pytest.fixture
def graph_branch_nested_loop_prov_inside(
    graph_with_branch: GraphSolution,
    graph_with_loop: GraphSolution
) -> GraphSolution:
    """Pytest fixture providing a :class:`GraphSolution` containing a
    :class:`BranchEventSolution` containg a nested
    :class:`LoopEventSolution` within its sub :class:`GraphSolution`.
    The provider of the dynamic control for the nested
    :class:`LoopEventSolution` is inside of the top level
    :class:`BranchEventSolution`.

    :param graph_with_branch: Fixture providing :class:`GraphSolution`
    containing a :class:`BranchEventSolution`
    :type graph_with_branch: :class:`GraphSolution`
    :param graph_with_loop: Fixture providing :class:`GraphSolution`
    containing a single :class:`LoopEventSolution`
    :return: Returns the updated :class:`GraphSolution` with
    :class:`LoopEventSolution` nested in the :class:`BranchEventSolution`
    :rtype: :class:`GraphSolution`
    """
    graph = deepcopy(graph_with_branch)
    graph.branch_points[2].graph_solutions = [deepcopy(graph_with_loop)]
    events = list(graph.events.values()) + [
        event
        for branch_event in graph.branch_points.values()
        for graph_sol in branch_event.graph_solutions
        for event in graph_sol.events.values()
    ] + [
        event
        for branch_event in graph.branch_points.values()
        for graph_sol in branch_event.graph_solutions
        for loop_event in graph_sol.loop_events.values()
        for nested_graph_sol in loop_event.graph_solutions
        for event in nested_graph_sol.events.values()
    ]
    GraphSolution.update_event_type_counts(events)
    for event in events:
        event.event_id_tuple = (event.meta_data["EventType"], event.count)

    nested_provider = graph.branch_points[2].graph_solutions[0].events[1]
    nested_user = (
        graph.branch_points[2].graph_solutions[0].loop_events[2].
        graph_solutions[0].events[1]
    )
    for event in [nested_provider, nested_user]:
        event.parse_dynamic_control_events(
            {
                "X": {
                    "control_type": "LOOPCOUNT",
                    "provider": {
                        "EventType": nested_provider.event_id_tuple[0],
                        "occurenceId": nested_provider.event_id_tuple[1]
                    },
                    "user": {
                        "EventType": nested_user.event_id_tuple[0],
                        "occurenceId": nested_user.event_id_tuple[1]
                    }
                }
            }
        )
    graph.branch_points[2].parse_dynamic_control_events(
        {
            "X": {
                "control_type": "BRANCHCOUNT",
                "provider": {
                    "EventType": graph.branch_points[2].event_id_tuple[0],
                    "occurenceId": graph.branch_points[2].event_id_tuple[1],
                },
                "user": {
                    "EventType": graph.branch_points[2].event_id_tuple[0],
                    "occurenceId": graph.branch_points[2].event_id_tuple[1],
                }
            }
        }
    )
    return graph

"""
Tests for solutions.py
"""
from copy import deepcopy
import pytest

from test_event_generator.solutions import (
    EventSolution,
    GraphSolution,
    LoopEventSolution
)
from tests.utils import (
    check_length_attr,
    check_solution_correct,
    check_multiple_solutions_correct,
    add_event_type_suffix
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


class TestEventSolution:
    """Tests for :class:`EventSolution`
    """
    @staticmethod
    def test_add_prev_event(
        event_solution: EventSolution,
        prev_event_solution: EventSolution
    ) -> None:
        """Tests adding an :class:`EventSolution` instance to another
        :class:`EventSolution` instance's previous events. Tests
        :class:`EventSolution`.`add_prev_event`

        :param event_solution: :class:`EventSolution` to have another
        :class:`EventSolution` added to the previous event list
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: :class:`EventSolution` to be added
        to the previous event list of another :class:`EventSolution`
        :type prev_event_solution: :class:`EventSolution`
        """
        event_solution.add_prev_event(prev_event_solution)
        # prev_event_solution should have been added to the previous events of
        # event_solution
        assert event_solution.previous_events[0] == prev_event_solution

    @staticmethod
    def test_add_post_event(
        event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests adding an :class:`EventSolution` instance to another
        :class:`EventSolution` instance's post events. Tests
        :class:`EventSolution`.`add_post_event`

        :param event_solution: :class:`EventSolution` to have another
        :class:`EventSolution` added to the post event list
        :type event_solution: :class:`EventSolution`
        :param post_event_solution: :class:`EventSolution` to be added
        to the post event list of another :class:`EventSolution`
        :type post_event_solution: :class:`EventSolution`
        """
        event_solution.add_post_event(post_event_solution)
        # post_event_solution should have been added to the post events of
        # event_solution
        assert event_solution.post_events[0] == post_event_solution

    @staticmethod
    def test_add_to_previous_events(
        event_solution: EventSolution,
        prev_event_solution: EventSolution,
    ) -> None:
        """Tests adding an :class:`EventSolution` instance to another
        :class:`EventSolution` instance's previous events and updating
        its own post events with the other instance. Tests
        :class:`EventSolution`.`add_to_post_events`

        :param event_solution: :class:`EventSolution` to have another
        :class:`EventSolution` added to the previous event list
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: :class:`EventSolution` to be added
        to the previous event list of another :class:`EventSolution`
        :type prev_event_solution: :class:`EventSolution`
        """
        event_solution.add_prev_event(prev_event_solution)
        event_solution.add_to_previous_events()
        # the post events of the event added to the previous events of
        # event_solution should contain event_solution
        assert (
            event_solution.previous_events[0].post_events[0] == event_solution
        )

    @staticmethod
    def test_add_to_post_events(
        event_solution: EventSolution,
        post_event_solution: EventSolution,
    ) -> None:
        """Tests adding an :class:`EventSolution` instance to another
        :class:`EventSolution` instance's post events and updating
        its own previous events with the other instance. Tests
        :class:`EventSolution`.`add_to_post_events`

        :param event_solution: :class:`EventSolution` to have another
        :class:`EventSolution` added to the post event list
        :type event_solution: :class:`EventSolution`
        :param post_event_solution: :class:`EventSolution` to be added
        to the post event list of another :class:`EventSolution`
        :type post_event_solution: :class:`EventSolution`
        """
        event_solution.add_post_event(post_event_solution)
        event_solution.add_to_post_events()
        # the previous events of the event added to the post events of
        # event_solution should contain event_solution
        assert (
            event_solution.post_events[0].previous_events[0] == event_solution
        )

    @staticmethod
    def test_add_to_connected_events(
        event_solution: EventSolution,
        prev_event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests adding an :class:`EventSolution` to the post and previous
        event lists of :class:`EventSolution`'s in its previous and post
        events lists, respectively. Tests
        :class:`EventSolution`.`add_to_connected_events`

        :param event_solution: :class:`EventSolution` to have a
        :class:`EventSolution` added to the post event list and another
        :class:`EventSolution` added to the previous event list
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: :class:`EventSolution` to be added
        to the previous event list the :class:`EventSolution`
        :type prev_event_solution: :class:`EventSolution`
        :param post_event_solution: :class:`EventSolution` to be added
        to the post event list of the :class:`EventSolution`
        :type post_event_solution: :class:`EventSolution`
        """
        event_solution.add_prev_event(prev_event_solution)
        event_solution.add_post_event(post_event_solution)
        event_solution.add_to_connected_events()
        # the post events of the event added to the previous events of
        # event_solution should contain event_solution
        assert (
            event_solution.previous_events[0].post_events[0] == event_solution
        )
        # the previous events of the event added to the post events of
        # event_solution should contain event_solution
        assert (
            event_solution.post_events[0].previous_events[0] == event_solution
        )

    @staticmethod
    def test_is_start(
        event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests if an :class:`EventSolution` instance is correctly identified
        as a start event if it has another :class:`EventSolution` instance in
        its post events and none in its previous events

        :param event_solution: :class:`EventSolution` with the other
        :class:`EventSolution` added to its post event list
        :type event_solution: :class:`EventSolution`
        :param post_event_solution: :class:`EventSolution` added
        to the post event list of the other :class:`EventSolution`
        :type post_event_solution: :class:`EventSolution`
        """
        event_solution.add_post_event(post_event_solution)
        assert event_solution.is_start
        assert not event_solution.is_end

    @staticmethod
    def test_is_end(
        event_solution: EventSolution,
        prev_event_solution: EventSolution
    ) -> None:
        """Tests if an :class:`EventSolution` instance is correctly identified
        as an end event if it has another :class:`EventSolution` instance in
        its previous events and none in its post events

        :param event_solution: :class:`EventSolution` with the other
        :class:`EventSolution` added to its previous event list
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: :class:`EventSolution` added
        to the previous event list of the other :class:`EventSolution`
        :type prev_event_solution: :class:`EventSolution`
        """
        event_solution.add_prev_event(prev_event_solution)
        assert event_solution.is_end
        assert not event_solution.is_start

    @staticmethod
    def test_is_not_start_not_end(
        event_solution: EventSolution,
        prev_event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests if an :class:`EventSolution` instance is correctly identified
        as an end event if it has other :class:`EventSolution` instances in
        both its previous events post events

        :param event_solution: :class:`EventSolution` with the other
        :class:`EventSolution` added to its previous event list
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: :class:`EventSolution` added
        to the previous event list of the other :class:`EventSolution`
        :type prev_event_solution: :class:`EventSolution`
        :param post_event_solution: :class:`EventSolution` added
        to the post event list of the other :class:`EventSolution`
        :type post_event_solution: :class:`EventSolution`
        """
        event_solution.add_post_event(post_event_solution)
        event_solution.add_prev_event(prev_event_solution)
        assert not event_solution.is_end
        assert not event_solution.is_start

    @staticmethod
    def test_extend_branches_correct(
        event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests extending branches out from an :class:`EventSolution` with
        the method :class:`EventSolution`.`extend_branches`

        :param event_solution: :class:`EventSolution` that is the branch event
        :type event_solution: :class:`EventSolution`
        :param post_event_solution: :class:`EventSolution` that is duplicated
        to branch from the branch event. It is added to the bracnhed events
        post events
        :type post_event_solution: :class:`EventSolution`
        """
        event_solution.is_branch = True
        event_solution.add_post_event(post_event_solution)
        event_solution.add_to_post_events()
        # get branched events
        branched_events = event_solution.extend_branches(branch_count=8)
        # number of new events should be 7
        assert len(branched_events) == 7
        # number of post events of the branched event should equal the number
        # of branches
        assert len(event_solution.post_events) == 8
        # all the new branched events should have been added to the branch
        # event's post events
        assert all(
            event in event_solution.post_events
            for event in branched_events
        )
        # the branch event should be in all the branched events previous events
        assert all(
            event_solution in event.previous_events
            for event in branched_events
        )

    @staticmethod
    def test_extend_branches_not_branch(
        event_solution: EventSolution
    ) -> None:
        """Tests that if an :class:`EventSolution` is not identified as a
        branch event then a :class:`RuntimeError` is raised

        :param event_solution: The :class:`EventSolution` that is not a branch
        :type event_solution: :class:`EventSolution`
        """
        with pytest.raises(RuntimeError) as e_info:
            event_solution.extend_branches(2)
        assert e_info.value.args[0] == (
            "Method called but the Event is not a branching Event"
        )


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


class TestGraphSolution:
    """Grouping of tests to test :class:`GraphSolution` methods for adding
    :class:`EventSolution` instances and combining :class:`GraphSolution`
    instances.
    """
    @staticmethod
    def test_add_event_start(
        graph_solution: GraphSolution,
        event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests adding an :class:`EventSolution` that is a start event to the
        graph solution using the method :class:`GraphSolution`.`add_event`

        :param graph_solution: A pre instantiated empty :class:`GraphSolution`
        instance
        :type graph_solution: :class:`GraphSolution`
        :param event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type event_solution: :class:`EventSolution`
        :param post_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type post_event_solution: :class:`EventSolution`
        """
        event_solution.add_post_event(post_event_solution)
        graph_solution.add_event(event_solution)
        # there must be only one event added to the graph solution
        assert graph_solution.event_dict_count == 1
        # event_solution must be at key 1 in the graph solutions event
        # dictionary
        assert graph_solution.events[1] == event_solution
        # event_solution must be at key 1 in the graph solutions start event
        # dictionary
        assert graph_solution.start_events[1] == event_solution
        # there must be only 1 start event and only 1 event in the graph
        # solution
        assert check_length_attr(
            graph_solution,
            lens=[1, 1, 0, 0, 0, 0],
            attrs=[
                "start_events", "events",
                "end_events", "loop_events",
                "branch_points", "break_points"
            ]
        )

    @staticmethod
    def test_add_event_end(
        graph_solution: GraphSolution,
        event_solution: EventSolution,
        prev_event_solution: EventSolution
    ) -> None:
        """Tests adding an :class:`EventSolution` that is an end event to the
        graph solution using the method :class:`GraphSolution`.`add_event`

        :param graph_solution: A pre instantiated empty :class:`GraphSolution`
        instance
        :type graph_solution: :class:`GraphSolution`
        :param event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type prev_event_solution: :class:`EventSolution`
        """
        event_solution.add_prev_event(prev_event_solution)
        graph_solution.add_event(event_solution)
        assert graph_solution.event_dict_count == 1
        assert graph_solution.events[1] == event_solution
        assert graph_solution.end_events[1] == event_solution
        # there must be only one event added to the graph solution
        assert graph_solution.event_dict_count == 1
        # event_solution must be at key 1 in the graph solutions event
        # dictionary
        assert graph_solution.events[1] == event_solution
        # event_solution must be at key 1 in the graph solutions end event
        # dictionary
        assert graph_solution.end_events[1] == event_solution
        # there must be only 1 end event and only 1 event in the graph
        # solution
        assert check_length_attr(
            graph_solution,
            lens=[0, 1, 1, 0, 0, 0],
            attrs=[
                "start_events", "events",
                "end_events", "loop_events",
                "branch_points", "break_points"
            ]
        )

    @staticmethod
    def test_add_event_branch_point(
        graph_solution: GraphSolution,
        event_solution: EventSolution,
        prev_event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests adding an :class:`EventSolution` that is a branch point to the
        graph solution using the method :class:`GraphSolution`.`add_event`

        :param graph_solution: A pre instantiated empty :class:`GraphSolution`
        instance
        :type graph_solution: :class:`GraphSolution`
        :param event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type prev_event_solution: :class:`EventSolution`
        :param post_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type post_event_solution: :class:`EventSolution`
        """
        event_solution.is_branch = True
        event_solution.add_prev_event(prev_event_solution)
        event_solution.add_post_event(post_event_solution)
        graph_solution.add_event(event_solution)
        # there must be only one event added to the graph solution
        assert graph_solution.event_dict_count == 1
        # event_solution must be at key 1 in the graph solutions event
        # dictionary
        assert graph_solution.events[1] == event_solution
        # event_solution must be at key 1 in the graph solutions branch points
        # dictionary
        assert graph_solution.branch_points[1] == event_solution
        # there must be only 1 branch point and only 1 event in the graph
        # solution
        assert check_length_attr(
            graph_solution,
            lens=[0, 1, 0, 0, 1, 0],
            attrs=[
                "start_events", "events",
                "end_events", "loop_events",
                "branch_points", "break_points"
            ]
        )

    @staticmethod
    def test_add_event_break_point(
        graph_solution: GraphSolution,
        event_solution: EventSolution,
        prev_event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests adding an :class:`EventSolution` that is a break point to the
        graph solution using the method :class:`GraphSolution`.`add_event`

        :param graph_solution: A pre instantiated empty :class:`GraphSolution`
        instance
        :type graph_solution: :class:`GraphSolution`
        :param event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type prev_event_solution: :class:`EventSolution`
        :param post_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type post_event_solution: :class:`EventSolution`
        """
        event_solution.is_break_point = True
        event_solution.add_prev_event(prev_event_solution)
        event_solution.add_post_event(post_event_solution)
        graph_solution.add_event(event_solution)
        # there must be only one event added to the graph solution
        assert graph_solution.event_dict_count == 1
        # event_solution must be at key 1 in the graph solutions event
        # dictionary
        assert graph_solution.events[1] == event_solution
        # event_solution must be at key 1 in the graph solutions break points
        # dictionary
        assert graph_solution.break_points[1] == event_solution
        # there must be only 1 break point and only 1 event in the graph
        # solution
        assert check_length_attr(
            graph_solution,
            lens=[0, 1, 0, 0, 0, 1],
            attrs=[
                "start_events", "events",
                "end_events", "loop_events",
                "branch_points", "break_points"
            ]
        )

    @staticmethod
    def test_add_event_loop_event(
        graph_solution: GraphSolution,
        prev_event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests adding a :class:`LoopEventSolution` to the
        graph solution using the method :class:`GraphSolution`.`add_event`

        :param graph_solution: A pre instantiated empty :class:`GraphSolution`
        instance
        :type graph_solution: :class:`GraphSolution`
        :param prev_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type prev_event_solution: :class:`EventSolution`
        :param post_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type post_event_solution: :class:`EventSolution`
        """
        loop_event_solution = LoopEventSolution(
            graph_solutions=[GraphSolution()]
        )
        loop_event_solution.add_prev_event(prev_event_solution)
        loop_event_solution.add_post_event(post_event_solution)
        graph_solution.add_event(loop_event_solution)
        # there must be only one event added to the graph solution
        assert graph_solution.event_dict_count == 1
        # event_solution must be at key 1 in the graph solutions event
        # dictionary
        assert graph_solution.events[1] == loop_event_solution
        # event_solution must be at key 1 in the graph solutions loop events
        # dictionary
        assert graph_solution.loop_events[1] == loop_event_solution
        # there must be only 1 loop event and only 1 event in the graph
        # solution
        assert check_length_attr(
            graph_solution,
            lens=[0, 1, 0, 1, 0, 0],
            attrs=[
                "start_events", "events",
                "end_events", "loop_events",
                "branch_points", "break_points"
            ]
        )

    @staticmethod
    def test_parse_event_solutions(
        graph_solution: GraphSolution,
        event_solution: EventSolution,
        prev_event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> list[EventSolution]:
        """Tests parsing a list of :class:`EventSolution` that contain
        a start event, end event, break point, branch point, loop event and
        an event not fitting into those categories using the method
        :class:`GraphSolution`.`parse_event_solutions`.

        The events are all added in a simple sequence:

        (Start)->(Middle)->(Branch)->(Break)->(Loop)->(End)


        :param graph_solution: A pre instantiated empty :class:`GraphSolution`
        instance
        :type graph_solution: :class:`GraphSolution`
        :param event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type prev_event_solution: :class:`EventSolution`
        :param post_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type post_event_solution: :class:`EventSolution`
        :return: Returns a list of :class:`EventSolution` containing:
        start event, end event, branch point, break point, loop event and an
        event that does not fit into any of those categories.
        :rtype: list[:class:`EventSolution`]
        """
        # create branch, break and loop events
        branch_event_solution = EventSolution(is_branch=True)
        break_event_solution = EventSolution(is_break_point=True)
        loop_event_solution = LoopEventSolution(
            [GraphSolution()]
        )
        # sequence of events
        prev_event_solution.add_post_event(event_solution)
        event_solution.add_prev_event(prev_event_solution)
        event_solution.add_post_event(branch_event_solution)
        branch_event_solution.add_prev_event(event_solution)
        branch_event_solution.add_post_event(break_event_solution)
        break_event_solution.add_prev_event(branch_event_solution)
        break_event_solution.add_post_event(loop_event_solution)
        loop_event_solution.add_prev_event(break_event_solution)
        loop_event_solution.add_post_event(post_event_solution)
        post_event_solution.add_prev_event(loop_event_solution)
        list_of_events = [
            prev_event_solution, event_solution, branch_event_solution,
            break_event_solution, post_event_solution, loop_event_solution
        ]
        graph_solution.parse_event_solutions(list_of_events)
        # must be 6 events added
        assert graph_solution.event_dict_count == 6
        # all events in list of events must be in the GraphSolution events
        # dictionary
        assert all(
            event_sol in list(graph_solution.events.values())
            for event_sol in list_of_events
        )
        # all events should have been added to the correct dictionary
        assert graph_solution.start_events[1] == prev_event_solution
        assert graph_solution.branch_points[3] == branch_event_solution
        assert graph_solution.break_points[4] == break_event_solution
        assert graph_solution.end_events[5] == post_event_solution
        assert graph_solution.loop_events[6] == loop_event_solution
        # there should be 6 events in the GraphSolution in total and there
        # should be only one event in each of start_events, end_events,
        # branch_points, break_points and loop_events
        assert check_length_attr(
            graph_solution,
            lens=[1, 6, 1, 1, 1, 1],
            attrs=[
                "start_events", "events",
                "end_events", "loop_events",
                "branch_points", "break_points"
            ]
        )
        return list_of_events

    @staticmethod
    def test_remove_event(
        graph_solution: GraphSolution,
        event_solution: EventSolution,
        prev_event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests removing :class:`EventSolution`'s in succession from a
        :class:`GraphSolution` instance containing
        a start event, end event, break point, branch point, loop event and
        an event not fitting into those categories using the method
        :class:`GraphSolution`.`remove_event`.

        The events are all added in a simple sequence:

        (Start)->(Middle)->(Branch)->(Break)->(Loop)->(End)


        :param graph_solution: A pre instantiated empty :class:`GraphSolution`
        instance
        :type graph_solution: :class:`GraphSolution`
        :param event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type prev_event_solution: :class:`EventSolution`
        :param post_event_solution: A pre-instantiated :class:`EventSolution`
        instance
        :type post_event_solution: :class:`EventSolution`
        :return: Returns a list of :class:`EventSolution` containing:
        start event, end event, branch point, break point, loop event and an
        event that does not fit into any of those categories.
        :rtype: list[:class:`EventSolution`]
        """
        list_of_events = TestGraphSolution.test_parse_event_solutions(
            graph_solution=graph_solution,
            event_solution=event_solution,
            prev_event_solution=prev_event_solution,
            post_event_solution=post_event_solution
        )
        # starting attribut lengths
        attribute_lengths = [1, 6, 1, 1, 1, 1]
        # check that all events are removed correctly
        for i in range(1, 7, 1):
            graph_solution.remove_event(i)
            assert list_of_events[i - 1] not in list(
                graph_solution.events.values()
            )
            attribute_lengths[i - 1] -= 1
            if i != 2:
                attribute_lengths[1] -= 1
            assert check_length_attr(
                graph_solution,
                lens=attribute_lengths,
                attrs=[
                    "start_events", "events",
                    "branch_points", "break_points",
                    "end_events", "loop_events"
                ]
            )

    @staticmethod
    def test_combine_graphs_1_end_1_start(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the combination of two graphs 1 end to 1 start point
        :class:`GraphSolution`.`combine_graphs`. The left graph is

        (Start)->(Middle)->(End)

        the right graph is

        (Start_copy)->(Middle_copy)->(End_copy)

        The resulting combined graph should be

        (Start)->(Middle)->(End)->(Start_copy)->(Middle_copy)->(End_copy)

        :param graph_simple: Fixture representing a simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        """
        graph_simple_copy = deepcopy(graph_simple)
        for event in graph_simple_copy.events.values():
            event.meta_data["EventType"] = (
                event.meta_data["EventType"] + "_copy"
            )
        event_types = ["Start", "Middle", "End"]
        event_types += [event_type + "_copy" for event_type in event_types]
        combined_graph = GraphSolution.combine_graphs(
            left_graph=graph_simple,
            right_graph=graph_simple_copy
        )
        # check that there are 6 events and  1 start and 1 end
        assert check_length_attr(
            combined_graph,
            lens=[1, 6, 0, 0, 1, 0],
            attrs=[
                "start_events", "events",
                "branch_points", "break_points",
                "end_events", "loop_events"
            ]
        )
        # check that the solutions fits that mentioned in the docstring
        check_solution_correct(
            solution=combined_graph,
            event_types=event_types,
        )

    @staticmethod
    def test_combine_graphs_1_end_2_start(
        graph_simple: GraphSolution,
        graph_two_start_two_end: GraphSolution
    ) -> None:
        """Tests combining a graph with 1 end point to a graph with 2 start
        points :class:`GraphSolution`.`combine_graphs`. The left graph is

        (Start)->(Middle)->(End)

        The right graph is

        (Start)->(      )->(End)
                 (Middle)
        (Start)->(      )->(End)

        After combining them the new graph should be

                               )->(Start)->(      )>(End)
        (Start)->(Middle)->(End)           (Middle)
                               )->(Start)->(      )->(End)

        :param graph_simple: Fixture representing a simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        :param graph_two_start_two_end: Fixture representing a sequence with
        two start points and two end points
        :type graph_two_start_two_end: :class:`GraphSolution`
        """
        for event in graph_two_start_two_end.events.values():
            event.meta_data["EventType"] += "_right"
        event_types = [
            event.meta_data["EventType"]
            for event in graph_simple.events.values()
        ] + [
            event.meta_data["EventType"]
            for event in graph_two_start_two_end.events.values()
        ]
        combined_graph = GraphSolution.combine_graphs(
            left_graph=graph_simple,
            right_graph=graph_two_start_two_end
        )
        # check there are 8 events with 1 start point and 2 end points
        assert check_length_attr(
            combined_graph,
            lens=[1, 8, 0, 0, 2, 0],
            attrs=[
                "start_events", "events",
                "branch_points", "break_points",
                "end_events", "loop_events"
            ]
        )
        # check that the event types are correct
        for i in range(1, 9):
            event_solution = combined_graph.events[i]
            assert event_solution.meta_data["EventType"] == event_types[i - 1]
        # check that the intersection has been combined correctly with post
        # and previous events added correctly
        for i in [4, 5]:
            for j in [3]:
                assert combined_graph.events[j] in (
                    combined_graph.events[i].previous_events
                )
                assert combined_graph.events[i] in (
                    combined_graph.events[j].post_events
                )

    @staticmethod
    def test_combine_graphs_2_end_1_start(
        graph_simple: GraphSolution,
        graph_two_start_two_end: GraphSolution
    ) -> None:
        """Tests combining a graph with 2 end points to a graph with 1 start
        point :class:`GraphSolution`.`combine_graphs`. The left graph is

        (Start)->(      )->(End)
                 (Middle)
        (Start)->(      )->(End)


        The right graph is

        (Start)->(Middle)->(End)

        After combining them the new graph should be

        (Start)->(      )->(End)->(
                 (Middle)         (Start)-(Middle)-(End)
        (Start)->(      )->(End)->(

        :param graph_simple: Fixture representing a simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        :param graph_two_start_two_end: Fixture representing a sequence with
        two start points and two end points
        :type graph_two_start_two_end: :class:`GraphSolution`
        """
        for event in graph_simple.events.values():
            event.meta_data["EventType"] += "_right"
        event_types = [
            event.meta_data["EventType"]
            for event in graph_two_start_two_end.events.values()
        ] + [
            event.meta_data["EventType"]
            for event in graph_simple.events.values()
        ]
        combined_graph = GraphSolution.combine_graphs(
            right_graph=graph_simple,
            left_graph=graph_two_start_two_end
        )
        # check there are 8 events with 2 start points and 1 end point
        assert check_length_attr(
            combined_graph,
            lens=[2, 8, 0, 0, 1, 0],
            attrs=[
                "start_events", "events",
                "branch_points", "break_points",
                "end_events", "loop_events"
            ]
        )
        # check that the event types are correct
        for i in range(1, 9):
            event_solution = combined_graph.events[i]
            assert event_solution.meta_data["EventType"] == event_types[i - 1]
        # check that the intersection has been combined correctly with post
        # and previous events added correctly
        for i in [6]:
            for j in [4, 5]:
                assert combined_graph.events[j] in (
                    combined_graph.events[i].previous_events
                )
                assert combined_graph.events[i] in (
                    combined_graph.events[j].post_events
                )

    @staticmethod
    def test_combine_graphs_2_end_2_start(
        graph_two_start_two_end: GraphSolution
    ) -> None:
        """Tests combining a graph with 2 end points to a graph with 2 start
        points :class:`GraphSolution`.`combine_graphs`. The left graph is

        (Start)->(      )->(End)
                 (Middle)
        (Start)->(      )->(End)


        The right graph is

        (Start)->(      )->(End)
                 (Middle)
        (Start)->(      )->(End)

        After combining them the new graph should be

        (Start)->(      )->(End)->(Start)->(      )->(End)
                 (      )      |  ^        (      )
                 (      )       | |        (      )
                 (Middle)        |         (Middle)
                 (      )       | |        (      )
                 (      )      |  V        (      )
        (Start)->(      )->(End)->(Start)->(      )->(End)

        :param graph_simple: Fixture representing a simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        :param graph_two_start_two_end: Fixture representing a sequence with
        two start points and two end points
        :type graph_two_start_two_end: :class:`GraphSolution`
        """
        graph_right = deepcopy(graph_two_start_two_end)
        for event in graph_right.events.values():
            event.meta_data["EventType"] += "_right"
        event_types = [
            event.meta_data["EventType"]
            for event in graph_two_start_two_end.events.values()
        ] + [
            event.meta_data["EventType"]
            for event in graph_right.events.values()
        ]
        combined_graph = GraphSolution.combine_graphs(
            right_graph=graph_right,
            left_graph=graph_two_start_two_end
        )
        # check there are 10 events with 2 start points and 2 end points
        assert check_length_attr(
            combined_graph,
            lens=[2, 10, 0, 0, 2, 0],
            attrs=[
                "start_events", "events",
                "branch_points", "break_points",
                "end_events", "loop_events"
            ]
        )
        # check that the event types are correct
        for i in range(1, 11):
            event_solution = combined_graph.events[i]
            assert event_solution.meta_data["EventType"] == event_types[i - 1]
        # check that the intersection has been combined correctly with post
        # and previous events added correctly
        for i in [6, 7]:
            for j in [4, 5]:
                assert combined_graph.events[j] in (
                    combined_graph.events[i].previous_events
                )
                assert combined_graph.events[i] in (
                    combined_graph.events[j].post_events
                )

    @staticmethod
    def test_combine_graphs_break_point(
        graph_simple: GraphSolution,
    ) -> None:
        """Tests the combination of two graphs 1 end to 1 start point using
        :class:`GraphSolution`.`combine_graphs` method. The left graph has a
        break point. The left graph is

        (Start)->(Middle)->(End, is_break=True)

        the right graph is

        (Start)->(Middle)->(End)

        The resulting combined graph should be

        (Start)->(Middle)->(End, is_break=true)

        as having a break point on the left graph means only the left graph
        should be returned.


        :param graph_simple: Fixture representing a simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        """
        graph_right = deepcopy(graph_simple)
        graph_simple.events[3].is_break_point = True
        graph_simple.break_points[3] = graph_simple.events[3]
        combined_graph = GraphSolution.combine_graphs(
            left_graph=graph_simple,
            right_graph=graph_right
        )
        # check there are only three events in the combined graph
        assert len(combined_graph.events) == 3
        # check the event types match that of the left hand input graph
        check_solution_correct(
            solution=combined_graph,
            event_types=[
                event.meta_data["EventType"]
                for event in graph_simple.events.values()
            ]
        )

    @staticmethod
    def test_dunder_add_other_not_graph(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the dunder :class:`GraphSolution`.`__add__` method when the
        instance on the right hand of the addition operation is not
        :class:`GraphSolution`. For example

        (Start)->(Middle)->(End) + 12 = (Start)->(Middle)->(End)

        :param graph_simple: Fixture representing a simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        """
        added_graph = graph_simple + 12
        # check there are only three events in the combined graph
        assert len(added_graph.events) == 3
        # check the event types match that of the left hand input graph
        check_solution_correct(
            solution=added_graph,
            event_types=[
                event.meta_data["EventType"]
                for event in graph_simple.events.values()
            ]
        )

    @staticmethod
    def test_dunder_add(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the dunder :class:`GraphSolution`.`__add__` method when the
        instance on the right hand of the addition operation is
        :class:`GraphSolution`. For example

        (
            (Start)->(Middle)->(End) + (Start_copy)->(Middle_copy)->(End_copy)
        ) = (
           (Start)->(Middle)->(End)->(Start_copy)->(Middle_copy)->(End_copy)
        )

        :param graph_simple: Fixture representing a simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        """
        graph_simple_copy = deepcopy(graph_simple)
        for event in graph_simple_copy.events.values():
            event.meta_data["EventType"] = (
                event.meta_data["EventType"] + "_copy"
            )
        event_types = [
            event.meta_data["EventType"]
            for event in graph_simple.events.values()
        ] + [
            event.meta_data["EventType"]
            for event in graph_simple_copy.events.values()
        ]
        combined_graph = graph_simple + graph_simple_copy
        # check that there are 6 events and  1 start and 1 end
        assert check_length_attr(
            combined_graph,
            lens=[1, 6, 0, 0, 1, 0],
            attrs=[
                "start_events", "events",
                "branch_points", "break_points",
                "end_events", "loop_events"
            ]
        )
        # check that the solutions fits that mentioned in the docstring
        check_solution_correct(
            solution=combined_graph,
            event_types=event_types,
        )

    @staticmethod
    def test_dunder_radd_graphs_other_not_graph(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the dunder :class:`GraphSolution`.`__radd__` method when the
        instance on the left hand of the addition operation is not
        :class:`GraphSolution`. For example

        12 + (Start)->(Middle)->(End) = (Start)->(Middle)->(End)

        :param graph_simple: Fixture representing a simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        """
        added_graph = 12 + graph_simple
        # check there are only three events in the combined graph
        assert len(added_graph.events) == 3
        # check the event types match that of the right hand input graph
        check_solution_correct(
            solution=added_graph,
            event_types=[
                event.meta_data["EventType"]
                for event in graph_simple.events.values()
            ]
        )

    @staticmethod
    def test_dunder_radd(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the dunder :class:`GraphSolution`.`__radd__` method when the
        instance on the left hand of the addition operation is
        :class:`GraphSolution`. For example

        (
            (Start_copy)->(Middle_copy)->(End_copy) + (Start)->(Middle)->(End)
        ) = (
           (Start_copy)->(Middle_copy)->(End_copy)->(Start)->(Middle)->(End)
        )

        :param graph_simple: Fixture representing a simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        """
        graph_simple_copy = deepcopy(graph_simple)
        for event in graph_simple_copy.events.values():
            event.meta_data["EventType"] = (
                event.meta_data["EventType"] + "_copy"
            )
        event_types = [
            event.meta_data["EventType"]
            for event in graph_simple_copy.events.values()
        ] + [
            event.meta_data["EventType"]
            for event in graph_simple.events.values()
        ]
        combined_graph = graph_simple_copy + graph_simple
        # check that there are 6 events and  1 start and 1 end
        assert check_length_attr(
            combined_graph,
            lens=[1, 6, 0, 0, 1, 0],
            attrs=[
                "start_events", "events",
                "branch_points", "break_points",
                "end_events", "loop_events"
            ]
        )
        # check that the solutions fits that mentioned in the docstring
        check_solution_correct(
            solution=combined_graph,
            event_types=event_types,
        )


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
            graph_simple,
            deepcopy(graph_simple),
            graph_with_break
        ]
    )
    return loop_event


class TestLoopEventSolution:
    """Class to test :class:`LoopEventSolution`
    """
    @staticmethod
    @pytest.mark.parametrize(
        "num_solutions_break,num_solutions_no_break,num_repeats",
        [
            pytest.param(i, i, j, id=f"i={i},j={j}")
            for i in range(1, 3)
            for j in range(1, 5)
        ],
    )
    def test_get_solutions_with_break_after_n_repititions(
        num_solutions_break: int,
        num_solutions_no_break: int,
        num_repeats: int,
        graph_simple: GraphSolution,
    ) -> None:
        """Tests the method
        :class:`LoopEventSolution`.`get_solutions_with_break_after_n_repititions`.
        Runs through several parameterized tests for the following:

        |num_solutions_break|num_solutions_no_break|num_repeats|
        |-------------------|----------------------|-----------|
        |         1         |           1          |      1    |
        |         1         |           1          |      2    |
        |         1         |           1          |      3    |
        |         1         |           1          |      4    |
        |         2         |           2          |      1    |
        |         2         |           2          |      2    |
        |         2         |           2          |      3    |
        |         2         |           2          |      4    |

        :param num_solutions_break: _description_
        :type num_solutions_break: int
        :param num_solutions_no_break: _description_
        :type num_solutions_no_break: int
        :param num_repeats: _description_
        :type num_repeats: int
        :param graph_simple: _description_
        :type graph_simple: GraphSolution
        """
        graph_simple_copy = deepcopy(graph_simple)
        solutions_no_break = [graph_simple] + [
            deepcopy(graph_simple)
            for _ in range(num_solutions_no_break - 1)
        ]
        solutions_with_break = [graph_simple_copy] + [
            deepcopy(graph_simple_copy)
            for _ in range(num_solutions_break - 1)
        ]
        solution_combos = (
            LoopEventSolution.get_solutions_with_break_after_n_repititions(
                repeat=num_repeats,
                solutions_no_break=solutions_no_break,
                solutions_with_break=solutions_with_break
            )
        )
        # the number of combinations should be equal to
        # (num_solutions_no_break ^ num_repeats) x num_solutions_break
        assert len(solution_combos) == (
            num_solutions_break * num_solutions_no_break ** num_repeats
        )
        counter = 0
        num_of_no_break_combos = num_solutions_no_break ** num_repeats
        # check that the graph_solutions with a break are at the end of each
        # combination
        for graph_solution in solutions_with_break:
            for _ in range(num_of_no_break_combos):
                assert solution_combos[counter][num_repeats] == graph_solution
                counter += 1

    @staticmethod
    @pytest.mark.parametrize(
        "num_solutions_break,num_solutions_no_break,num_loops",
        [
            pytest.param(i, i, j, id=f"i={i},j={j}")
            for i in range(1, 3)
            for j in range(1, 5)
        ],
    )
    def test_solution_combinations_with_break(
        num_solutions_break: int,
        num_solutions_no_break: int,
        num_loops: int,
        graph_simple: GraphSolution,
    ) -> None:
        """Tests the method
        :class:`LoopEventSolution`.`solution_combinations_with_break`.
        Runs through several parameterized tests for the following:

        |num_solutions_break|num_solutions_no_break| num_loops |
        |-------------------|----------------------|-----------|
        |         1         |           1          |      1    |
        |         1         |           1          |      2    |
        |         1         |           1          |      3    |
        |         1         |           1          |      4    |
        |         2         |           2          |      1    |
        |         2         |           2          |      2    |
        |         2         |           2          |      3    |
        |         2         |           2          |      4    |

        The number of solution combinations should follow the rules:

        `num_solutions_no_break x sum_{i=0}^n(num_solutions_break^n)`
        where `n = num_loops - 1`

        :param num_solutions_break: _description_
        :type num_solutions_break: int
        :param num_solutions_no_break: _description_
        :type num_solutions_no_break: int
        :param num_loops: _description_
        :type num_repeats: int
        :param graph_simple: _description_
        :type graph_simple: GraphSolution
        """
        graph_simple_copy = deepcopy(graph_simple)
        solutions_no_break = [graph_simple] + [
            deepcopy(graph_simple)
            for _ in range(num_solutions_no_break - 1)
        ]
        solutions_with_break = [graph_simple_copy] + [
            deepcopy(graph_simple_copy)
            for _ in range(num_solutions_break - 1)
        ]
        solution_combos = LoopEventSolution.solution_combinations_with_break(
            loop_count=num_loops,
            solutions_no_break=solutions_no_break,
            solutions_with_break=solutions_with_break
        )
        # the number of solution combinations should be equal to the sum of
        # the number of combinations for each loop size up to the
        # number of loops - 1 without a break multiplied by the number of
        # solutions with a break
        assert len(solution_combos) == sum(
            num_solutions_break * num_solutions_no_break ** loop_num
            for loop_num in range(num_loops)
        )
        counter = 0
        # check that the graph_solutions with a break are at the end of each
        # combination
        for loop_num in range(num_loops):
            num_of_no_break_combos = num_solutions_no_break ** loop_num
            for graph_solution in solutions_with_break:
                for _ in range(num_of_no_break_combos):
                    assert solution_combos[counter][loop_num] == graph_solution
                    counter += 1

    @staticmethod
    def test_expanded_solutions_from_solutions_combo(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method
        :class:`LoopEventSolution`.`expanded_solutions_from_solutions_combo`.


        :param graph_simple: Simple 3 event sequence from fixture
        :type graph_simple: :class:`GraphSolution`
        """
        graph_combos = [
            tuple(deepcopy(graph_simple) for _ in range(3))
            for _ in range(2)
        ]
        event_types = []
        for i in range(2):
            event_types.append([])
            for j in range(3):
                for event in graph_combos[i][j].events.values():
                    event.meta_data["EventType"] += f"_{i}{j}"
                    event_types[i].append(event.meta_data["EventType"])
        expanded_solution_combos = (
            LoopEventSolution.expanded_solutions_from_solutions_combo(
                graph_combos
            )
        )
        # There should only be two solution combinations
        assert len(expanded_solution_combos) == 2
        # all of the instances in the list should be GraphSolution instances
        assert all(
            isinstance(graph_solution, GraphSolution)
            for graph_solution in expanded_solution_combos
        )
        # Checks that each GraphSolution instance has been created correctly
        for i in range(2):
            graph_solution = expanded_solution_combos[i]
            check_solution_correct(
                solution=graph_solution,
                event_types=event_types[i]
            )

    @staticmethod
    def test_expand_loops(
        loop_event_solution: LoopEventSolution
    ) -> None:
        """Tests the method :class:`LoopEventSolution`.`expand_loops`

        :param loop_event_solution: Fixture :class:`LoopEventSolution` holding
        three :class:`GraphSolution` instances, one with a break point.
        :type loop_event_solution: :class:`LoopEventSolution`
        """
        loop_event_solution.expand_loops(3)
        # check the loops have been expanded correctly
        TestLoopEventSolution.check_expanded_loops(loop_event_solution)

    @staticmethod
    def check_expanded_loops(loop_event: LoopEventSolution) -> None:
        """Helper function to check the correct expansion of a
        :class:`LoopEventSolution`

        :param loop_event_solution: Fixture :class:`LoopEventSolution` holding
        three :class:`GraphSolution` instances, one with a break point.
        This must be expanded already
        :type loop_event_solution: :class:`LoopEventSolution`
        """
        # After expansion the LoopEventSolution.expanded_solutions list should
        # exist
        assert loop_event.expanded_solutions is not None
        # the length of the expanded solutions list should be 15
        assert len(loop_event.expanded_solutions) == 15
        num_of_solutions_with_breaks = 0
        for solution in loop_event.expanded_solutions:
            if len(solution.break_points) > 0:
                num_of_solutions_with_breaks += 1
        # there should be 7 solutions with a break
        assert num_of_solutions_with_breaks == 7


@pytest.fixture()
def graph_simple_with_branch(
    graph_simple: GraphSolution
) -> GraphSolution:
    """Fixture to generate a :class:`GraphSolution` with a branch point. The
    sequence is

    (Start)->(Middle, is_branch=True)->(End)

    :param graph_simple: Fixture for simple 3 event
    sequence
    :type graph_simple: :class:`GraphSolution`
    :return: Returns the :class:`GraphSolution` with a branch point
    :rtype: :class:`GraphSolution`
    """
    graph = deepcopy(graph_simple)
    graph.events[2].is_branch = True
    graph.branch_points[2] = graph.events[2]
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
    for event in graph.events.values():
        event.meta_data["EventType"] += "_upper"
    nested_loop_graph = deepcopy(graph_with_loop)
    for event in nested_loop_graph.events.values():
        event.meta_data["EventType"] += "_nested"
    graph.loop_events[2].graph_solutions = [
        deepcopy(nested_loop_graph)
    ]
    return graph


class TestGraphSolutionsExpansions:
    """Tests of :class:`GraphSolution` for the expansion of loops and branch
    points.
    """
    @staticmethod
    def test_expand_loop_events(
        loop_event_solution: LoopEventSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`expand_loop_events`. Test
        for :class:`GraphSolution` with four :class:`LoopEventSolution`'s
        containing 3 :class:`GraphSolution` sub graph solutions, one which has
        a break point. Loops are set to have a length of 3.

        :param loop_event_solution: Fixture for :class:`LoopEventSolution`
        with 3 sub-graph solutions
        :type loop_event_solution: :class:`LoopEventSolution`
        """
        events = [deepcopy(loop_event_solution) for _ in range(4)]
        graph = GraphSolution()
        graph.parse_event_solutions(events=events)
        graph.expand_loop_events(3)
        # the loop events sub-graphs must have been expanded correctly
        for loop_event in graph.loop_events.values():
            TestLoopEventSolution.check_expanded_loops(loop_event)

    @staticmethod
    def test_expand_branch_events(
        graph_simple_with_branch: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`expand_branch_events`.
        Tests for a :class:`GraphSolution` with a simple 6 event sequence and
        two branch events. Tests for expanding the branches out by 2.
        The graph to be tested is

        (Start)->(Middle, is_branch=True)->(End)->(Start)->(
            Middle, is_branch=True
        )->(End)

        The resulting graph after expansion should look like (omitted
        is_branch=True on branch events)

                           ->(End)-|                 ->(End)
                          |        V                |
        (Start)->(Middle)-|        (Start)-(Middle)-|
                          |        ^                |
                           ->(End)-|                 ->(End)

        :param graph_simple_with_branch: Fixture of a :class:`GraphSolution`
        instance with branch points
        :type graph_simple_with_branch: :class:`GraphSolution`
        """
        graph_two_branches = (
            graph_simple_with_branch + graph_simple_with_branch
        )
        # there should be 6 events in the GraphSolution
        assert len(graph_two_branches.events) == 6
        graph_two_branches.expand_branch_events(
            2
        )
        # after expansion of branch points there should be 8 events
        assert len(graph_two_branches.events) == 8
        # There should be 2 post events for each of the branch points
        assert all(
            len(branch_event.post_events) == 2
            for branch_event in graph_two_branches.branch_points.values()
        )
        # check that the post events exist and are part of the GraphSolution
        assert all(
            branch_event.post_events[0] == graph_two_branches.events[3 * i + 3]
            and (
                branch_event.post_events[1]
            ) == (
                graph_two_branches.events[7 + i]
            )
            for i, branch_event in enumerate(
                graph_two_branches.branch_points.values()
            )
        )

    @staticmethod
    def test_expand_graph_solutions_nested_loop(
        graph_with_nested_loop: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`expand_graph_solutions`
        for a graph with a nested loop. Tests for expanding for loops of size
        2. This test should produce an expansion for the upper loop of

        (Start_nested)->(Middle_nested)->(End_nested)->(Start_nested)->(
            Middle_nested
        )->(End_nested)

        and for the nested loop

        (Middle)->(Middle)

        :param graph_with_nested_loop: Fixture of :class:`GraphSolution`
        containing a :class:`LoopEventSolution` with a sub graph that also
        contains a :class:`LoopEventSolution` that contains a sub-graph with a
        single event
        :type graph_with_nested_loop: :class:`GraphSolution`
        """
        graph_with_nested_loop.expand_graph_solutions(
            num_branches=1,
            num_loops=2
        )
        upper_loop_expanded_solutions = (
            graph_with_nested_loop.loop_events[2].expanded_solutions
        )
        # The legnth of the expanded solutions for the upper loop event must
        # be 1
        assert (
            len(upper_loop_expanded_solutions)
        ) == 1
        nested_loop_expanded_solutions = (
            upper_loop_expanded_solutions[0].loop_events[2].expanded_solutions
        )
        # The legnth of the expanded solutions for the nested loop event must
        # be 1
        assert (
            len(nested_loop_expanded_solutions)
        ) == 1
        upper_loop_expanded_solution = upper_loop_expanded_solutions[0]
        # There must be 6 events in the expanded loop
        assert len(upper_loop_expanded_solution.events) == 6
        # checks that the simple sequence of events is correct
        assert check_solution_correct(
            solution=upper_loop_expanded_solution,
            event_types=["Start_nested", "Loop_nested", "End_nested"] * 2
        )
        nested_loop_expanded_solution = nested_loop_expanded_solutions[0]
        # there must be two events in the expanded nested loop
        assert len(nested_loop_expanded_solution.events) == 2
        # checks that the simple sequence of events is correct
        assert check_solution_correct(
            solution=nested_loop_expanded_solution,
            event_types=["Middle"] * 2,
        )

    @staticmethod
    def test_expand_graph_solutions_branch_point(
        graph_simple_with_branch: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`expand_graph_solutions`
        for a graph with a branch point. Tests for expanding for branches of
        size 2. This test should produce an expansion for graph of

                          ->(End)
        (Start)->(Middle)-|
                          ->(End)

        :param graph_simple_with_branch: Fixture for a :class:`GraphSolution`
        with a branch point.
        :type graph_simple_with_branch: :class:`GraphSolution`
        """
        graph_simple_with_branch.expand_graph_solutions(
            num_branches=2,
            num_loops=1
        )
        # there should be 4 events
        assert len(graph_simple_with_branch.events) == 4
        # the number of events after the branch point should be 2
        assert len(graph_simple_with_branch.branch_points[2].post_events) == 2
        # the event type for the events after the branch point should be "End"
        assert (
            event.meta_data["EventType"] == "End"
            for event in graph_simple_with_branch.branch_points[2].post_events
        )

    @staticmethod
    def test_expand_graph_solutions_nested_loop_with_branch_point(
        graph_simple_with_branch: GraphSolution,
        graph_with_loop: GraphSolution
    ) -> None:
        """Tests method :class:`GraphSolution`.`expand_graph_solutions`.
        Expands a :class:`GraphSolution` with a loop event with a sub grpah
        solution with a branch point within that loop event. The graph is
        expanded for loops of size 2 and branches of size 2. The parent graph
        is

        (Start)->(Loop)->(End)

        the sub-graph is

        (Start)->(Middle, is_branch=True)->(End)

        The expanded loop with expanded branched should be (is_branch omitted)

                           ->(End)-|                 ->(End)
                          |        V                |
        (Start)->(Middle)-|        (Start)-(Middle)-|
                          |        ^                |
                           ->(End)-|                 ->(End)


        :param graph_simple_with_branch: Fixture for :class:`GraphSolution`
        with a branch point
        :type graph_simple_with_branch: :class:`GraphSolution`
        :param graph_with_loop: Fixture for :class:`GraphSolution` with a loop
        event
        :type graph_with_loop: :class:`GraphSolution`
        """
        loop_event = graph_with_loop.loop_events[2]
        loop_event.graph_solutions = [
            graph_simple_with_branch
        ]
        graph_with_loop.expand_graph_solutions(
            num_branches=2,
            num_loops=2
        )
        # the number of expanded solutions should be 1
        assert len(loop_event.expanded_solutions) == 1
        expanded_solution = loop_event.expanded_solutions[0]
        # the number of events in the expansions should be 8
        assert len(expanded_solution.events) == 8
        events = expanded_solution.events
        # check that post events are correct for branch points
        assert (
            events[2].post_events[0] == events[3]
        ) and events[2].post_events[1] == events[4]
        assert (
            events[6].post_events[0] == events[7]
        ) and events[6].post_events[1] == events[8]

    @staticmethod
    def test_handle_combine_start_events(
        graph_with_loop: GraphSolution,
        graph_two_start_two_end: GraphSolution
    ) -> None:
        """Test :class:`GraphSolution`.`handle_combine_start_events`. This
        tests the combining of start events from a sub-graph into the parent
        graph for a loop event

        :param graph_with_loop: Fixture representing a :class:`GraphSolution`
        with a loop
        :type graph_with_loop: :class:`GraphSolution`
        :param graph_two_start_two_end: Fixture representing a
        :class:`GraphSolution` with two start and two end points
        :type graph_two_start_two_end: :class:`GraphSolution`
        """
        previous_events = graph_with_loop.loop_events[2].previous_events
        GraphSolution.handle_combine_start_events(
            loop_solution_combination=graph_two_start_two_end,
            event=graph_with_loop.loop_events[2]
        )
        # check that the previous events of the start events are correct
        assert all(
            start_event.previous_events == previous_events
            for start_event in graph_two_start_two_end.start_events.values()
        )
        # check that the post events of the previous events are now the start
        # events
        assert all(
            event in previous_event.post_events
            for event in graph_two_start_two_end.start_events.values()
            for previous_event in previous_events
        )
        # check that the loop event is no longer in the previous events post
        # events
        assert all(
            graph_with_loop.loop_events[2] not in previous_event.post_events
            for previous_event in previous_events
        )

    @staticmethod
    def test_handle_combine_end_events(
        graph_with_loop: GraphSolution,
        graph_two_start_two_end: GraphSolution
    ) -> None:
        """Test :class:`GraphSolution`.`handle_combine_end_events`. This
        tests the combining of end events from a sub-graph into the parent
        graph for a loop event

        :param graph_with_loop: Fixture representing a :class:`GraphSolution`
        with a loop
        :type graph_with_loop: :class:`GraphSolution`
        :param graph_two_start_two_end: Fixture representing a
        :class:`GraphSolution` with two start and two end points
        :type graph_two_start_two_end: :class:`GraphSolution`
        """
        post_events = graph_with_loop.loop_events[2].post_events
        GraphSolution.handle_combine_end_events(
            loop_solution_combination=graph_two_start_two_end,
            event=graph_with_loop.loop_events[2]
        )
        # check that the post events of the end events are correct
        assert all(
            event.post_events == post_events
            for event in graph_two_start_two_end.end_events.values()
        )
        # check that the previous events of the post events are now the end
        # events
        assert all(
            event in post_event.previous_events
            for event in graph_two_start_two_end.end_events.values()
            for post_event in post_events
        )
        # check that the loop event is no longer in the post events previous
        # events
        assert all(
            graph_with_loop.loop_events[2] not in post_event.previous_events
            for post_event in post_events
        )

    @staticmethod
    def test_replace_loop_event_with_sub_graph_solution(
        graph_with_loop: GraphSolution,
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`replace_loop_event_with_sub_graph_solution`.
        Tests replacing a loop event with a simple 3 event sequence and
        updating the parent graph. The parent graph before replacement is

        (Start)->(Loop)->(End)

        The sub-graph is

        (Start)->(Middle)->(End)

        The resulting sequence after replacment should be

        (Start)->(Start)->(Middle)->(End)->(End)

        :param graph_with_loop: Fixture representing a :class:`GraphSolution`
        with a loop
        :type graph_with_loop: :class:`GraphSolution`
        :param graph_simple: Fixture representing a :class:`GraphSolution`
        with a simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        """
        loop_event = graph_with_loop.loop_events[2]
        GraphSolution.replace_loop_event_with_sub_graph_solution(
            solution=graph_with_loop,
            loop_solution_combination=graph_simple,
            event=loop_event,
            event_key=2
        )
        # the lenght of the resulting graph should be 5 events
        assert len(graph_with_loop.events) == 5
        # the loop event should not be in the event dictionary
        assert loop_event not in list(graph_with_loop.events.values())
        # the loop event should not be in the loop event dictionary
        assert loop_event not in list(graph_with_loop.loop_events.values())
        # all the events in the dictioanary should have no more than 1 event
        # in their previous or post events
        assert all(
            len(event.post_events) <= 1 and len(event.previous_events) <= 1
            for event in graph_with_loop.events.values()
        )
        # check that the grpah solution is correct
        check_solution_correct(
            solution=graph_with_loop,
            event_types=["Start", "Start", "Middle", "End", "End"]
        )

    @staticmethod
    def test_combine_nested_loop_solutions(
        graph_simple_with_branch: GraphSolution,
        graph_with_loop: GraphSolution,
        prev_event_solution: GraphSolution,
        post_event_solution: GraphSolution
    ) -> None:
        """tests the method
        :class:`GraphSolution`.`combine_nested_loop_solutions`. The structure
        of the graph solution to be tested is given below.

        The parent graph is:

        * (Start_upper)->(Loop_upper)->(End_upper)

        Loop_upper contains two graph solutions:

        * (Start_first_loop_with_loop)->(Loop_first_loop_with_loop)->(
           End_first_loop_with_loop
        )
        * (Start_first_loop_with_branch)->(
            Middle_first_loop_with_branch, is_branch=True
        )->(End_first_loop_with_branch)

        Loop_first_loop_with_branch contains a single event graph solution:

        * (Middle)

        :param graph_simple_with_branch: Fixture for :class:`GraphSolution`
        with a branch point
        :type graph_simple_with_branch: :class:`GraphSolution`
        :param graph_with_loop: Fixture for :class:`GraphSolution` with a loop
        event
        :type graph_with_loop: :class:`GraphSolution`
        :param prev_event_solution: Fixture Start :class:`EventSolution`
        :type prev_event_solution: :class:`EventSolution`
        :param post_event_solution: Fixture End :class:`EventSolution`
        :type post_event_solution: :class:`EventSolution`
        """

        upper_graph = GraphSolution()
        loop_event = LoopEventSolution(
            graph_solutions=[
                graph_with_loop,
                graph_simple_with_branch
            ],
            meta_data={"EventType": "Loop"}
        )
        loop_event.add_prev_event(prev_event_solution)
        loop_event.add_post_event(post_event_solution)
        loop_event.add_to_connected_events()
        upper_graph.parse_event_solutions(
            [prev_event_solution, loop_event, post_event_solution]
        )
        add_event_type_suffix(
            upper_graph.events.values(),
            "upper"
        )
        add_event_type_suffix(
            graph_simple_with_branch.events.values(),
            "first_loop_branch"
        )
        add_event_type_suffix(
            graph_with_loop.events.values(),
            "first_loop_with_loop"
        )
        add_event_type_suffix(
            graph_with_loop.loop_events[2].graph_solutions[0].events.values(),
            "nested_loop"
        )
        upper_graph.expand_graph_solutions(
            num_branches=2,
            num_loops=2
        )
        solutions = upper_graph.combine_nested_loop_solutions()
        # there should be 4 solutions
        assert len(solutions) == 4
        # first solution nested loop loops twice. The below represents the
        # flow from start event to last event
        first_sol = [
            "Start_upper", "Start_first_loop_with_loop", "Middle_nested_loop",
            "Middle_nested_loop", "End_first_loop_with_loop",
            "Start_first_loop_with_loop", "Middle_nested_loop",
            "Middle_nested_loop", "End_first_loop_with_loop", "End_upper"
        ]
        # second solution (one of each duplicated "Middle_first_loop_branch"
        # events are excluded)
        second_sol = [
            "Start_upper", "Start_first_loop_branch",
            "Middle_first_loop_branch", "End_first_loop_branch",
            "Start_first_loop_branch", "Middle_first_loop_branch",
            "End_first_loop_branch", "End_upper"
        ]
        # third solution (the duplicated "Middle_first_loop_branch"
        # event is excluded)
        third_sol = [
            "Start_upper", "Start_first_loop_with_loop", "Middle_nested_loop",
            "Middle_nested_loop", "End_first_loop_with_loop",
            "Start_first_loop_branch", "Middle_first_loop_branch",
            "End_first_loop_branch", "End_upper"
        ]
        # third solution (the duplicated "Middle_first_loop_branch"
        # event is excluded)
        fourth_sol = [
            "Start_upper", "Start_first_loop_branch",
            "Middle_first_loop_branch", "End_first_loop_branch",
            "Start_first_loop_with_loop", "Middle_nested_loop",
            "Middle_nested_loop", "End_first_loop_with_loop", "End_upper"
        ]
        event_type_sequences = [first_sol, second_sol, third_sol, fourth_sol]
        # check that the solution sequences are correct
        check_multiple_solutions_correct(
            solutions=solutions,
            event_types_sequences=event_type_sequences
        )

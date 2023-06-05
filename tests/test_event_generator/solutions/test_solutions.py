# pylint: disable=W605
"""
Tests for solutions.py
"""
from copy import deepcopy, copy
import re
from itertools import combinations_with_replacement

import pytest
import networkx as nx

from test_event_generator.solutions import (
    EventSolution,
    GraphSolution,
    LoopEventSolution,
    BranchEventSolution,
    DynamicControl,
    get_audit_event_jsons_and_templates,
    get_categorised_audit_event_jsons
)
from tests.utils import (
    check_length_attr,
    check_solution_correct,
    check_multiple_solutions_correct,
)


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

    @staticmethod
    def test_repr_0(
        event_solution: EventSolution
    ) -> None:
        """Tests that dunder :class:`EventSolution`.`__repr__` is accurately
        providing the correct return value when the attribute `count` is equal
        to 0.

        :param event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Middle"
        :type event_solution: :class:`EventSolution`
        """
        assert event_solution.count == 0
        assert str(event_solution) == "Middle"

    @staticmethod
    @pytest.mark.parametrize(
        "count",
        [
            pytest.param(i, id=f"count={i}")
            for i in range(1, 5)
        ],
    )
    def test_repr(
        count: int,
        event_solution: EventSolution
    ) -> None:
        """Tests that dunder :class:`EventSolution`.`__repr__` is accurately
        providing the correct return value when the attribute `count` is
        greater than 0.

        :param count: The integer to set the attribute `count` to
        :type count: `int`
        :param event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Middle"
        :type event_solution: :class:`EventSolution`
        """
        event_solution.count = count
        assert str(event_solution) == f"Middle{count}"

    @staticmethod
    def test_set_event_template_id_str(
        event_solution: EventSolution
    ) -> None:
        """Tests setting the property
        :class:`EventSolution`.`event_template_id` with a string

        :param event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Middle"
        :type event_solution: :class:`EventSolution`
        """
        event_solution.event_template_id = "event_1"
        assert event_solution.event_template_id == "event_1"

    @staticmethod
    def test_set_event_template_id_int(
        event_solution: EventSolution
    ) -> None:
        """Tests setting the property
        :class:`EventSolution`.`event_template_id` with an integer

        :param event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Middle"
        :type event_solution: :class:`EventSolution`
        """
        event_solution.event_template_id = 1
        assert event_solution.event_template_id == "1"

    @staticmethod
    def test_get_audit_event_json_start_event_no_app_name(
        event_solution: EventSolution
    ) -> None:
        """Tests :class:`EventSolution`.`get_audit_event_json` when
        the field "applicationName" is not provided in meta_data

        :param event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Middle"
        :type event_solution: :class:`EventSolution`
        """
        event_solution.event_template_id = "event_1"
        audit_event_json = event_solution.get_audit_event_json(
            job_id="1",
            time_stamp="2023-04-27T09:01:26Z",
            job_name="job name"
        )
        expected_audit_event_json = {
            "jobName": "job name",
            "jobId": "1",
            "eventType": "Middle",
            "eventId": "event_1",
            "timestamp": "2023-04-27T09:01:26Z",
            "applicationName": "default_application_name"
        }
        for field, value in audit_event_json.items():
            assert value == expected_audit_event_json[field]

    @staticmethod
    def test_get_audit_event_json_start_event_app_name(
        event_solution: EventSolution
    ) -> None:
        """Tests :class:`EventSolution`.`get_audit_event_json` when
        the field "applicationName" is provided in meta_data

        :param event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Middle"
        :type event_solution: :class:`EventSolution`
        """
        event_solution.event_template_id = "event_1"
        event_solution.meta_data["applicationName"] = "app name"
        audit_event_json = event_solution.get_audit_event_json(
            job_id="1",
            time_stamp="2023-04-27T09:01:26Z",
            job_name="job name"
        )
        expected_audit_event_json = {
            "jobName": "job name",
            "jobId": "1",
            "eventType": "Middle",
            "eventId": "event_1",
            "timestamp": "2023-04-27T09:01:26Z",
            "applicationName": "app name"
        }
        for field, value in audit_event_json.items():
            assert value == expected_audit_event_json[field]

    @staticmethod
    def test_get_audit_event_json(
        prev_event_solution: EventSolution,
        event_solution: EventSolution
    ) -> None:
        """Tests :class:`EventSolution`.`get_audit_event_json` when
        the field "applicationName" is provided in meta_data and there is
        a previous event to the :class:`EventSolution` instance

        :param prev_event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Start"
        :type prev_event_solution: :class:`EventSolution`
        :param event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Middle"
        :type event_solution: :class:`EventSolution`
        """
        event_solution.add_prev_event(prev_event_solution)
        prev_event_solution.event_template_id = "event_1"
        event_solution.event_template_id = "event_2"
        event_solution.meta_data["applicationName"] = "app name"
        audit_event_json = event_solution.get_audit_event_json(
            job_id="1",
            time_stamp="2023-04-27T09:01:26Z",
            job_name="job name"
        )
        expected_audit_event_json = {
            "jobName": "job name",
            "jobId": "1",
            "eventType": "Middle",
            "eventId": "event_2",
            "timestamp": "2023-04-27T09:01:26Z",
            "applicationName": "app name",
            "previousEventIds": "event_1"
        }
        for field, value in audit_event_json.items():
            assert value == expected_audit_event_json[field]

    @staticmethod
    def test_get_previous_event_ids_one_previous_event(
        event_solution: EventSolution,
        prev_event_solution: EventSolution
    ) -> None:
        """Tests :class:`EventSolution`.`get_previous_event_ids` when there is
        a previous event to the :class:`EventSolution` instance

        :param event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Middle"
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Start"
        :type prev_event_solution: :class:`EventSolution`
        """
        event_solution.add_prev_event(prev_event_solution)
        prev_event_solution.event_template_id = "event_1"
        event_solution.event_template_id = "event_2"
        previous_event_ids = event_solution.get_previous_event_ids()
        assert isinstance(previous_event_ids, str)
        assert previous_event_ids == "event_1"

    @staticmethod
    def test_get_previous_event_ids_multiple_previous_events(
        event_solution: EventSolution,
        prev_event_solution: EventSolution
    ) -> None:
        """Tests :class:`EventSolution`.`get_previous_event_ids` when there are
        multiple previous events to the :class:`EventSolution` instance

        :param event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Middle"
        :type event_solution: :class:`EventSolution`
        :param prev_event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Start"
        :type prev_event_solution: :class:`EventSolution`
        """
        prev_event_solution_2 = deepcopy(prev_event_solution)
        event_solution.add_prev_event(prev_event_solution)
        event_solution.add_prev_event(prev_event_solution_2)
        prev_event_solution.event_template_id = "event_1"
        prev_event_solution_2.event_template_id = "event_2"
        event_solution.event_template_id = "event_3"
        previous_event_ids = event_solution.get_previous_event_ids()
        assert isinstance(previous_event_ids, list)
        assert previous_event_ids[0] == "event_1"
        assert previous_event_ids[1] == "event_2"

    @staticmethod
    def test_get_post_event_edge_tuples(
        event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests :class:`EventSolution`.`get_post_event_edge_tuples` when
        there are multiple post events to the :class:`EventSolution` instance

        :param event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "Middle"
        :type event_solution: :class:`EventSolution`
        :param post_event_solution: fixture providing an instance of
        :class:`EventSolution` with EventType "End"
        :type post_event_solution: :class:`EventSolution`
        """
        post_event_solution_2 = deepcopy(post_event_solution)
        event_solution.add_post_event(post_event_solution)
        event_solution.add_post_event(post_event_solution_2)
        edge_tuples = event_solution.get_post_event_edge_tuples()
        for edge_tuple, post_event in zip(
            edge_tuples,
            [post_event_solution, post_event_solution_2]
        ):
            assert edge_tuple[0] == event_solution
            assert edge_tuple[1] == post_event


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
        prev_event_solution: EventSolution,
        post_event_solution: EventSolution
    ) -> None:
        """Tests adding a :class:`BranchEventSolution` to the
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
        branch_event_solution = BranchEventSolution(
            graph_solutions=[GraphSolution()]
        )
        branch_event_solution.add_prev_event(prev_event_solution)
        branch_event_solution.add_post_event(post_event_solution)
        graph_solution.add_event(branch_event_solution)
        # there must be only one event added to the graph solution
        assert graph_solution.event_dict_count == 1
        # event_solution must be at key 1 in the graph solutions event
        # dictionary
        assert graph_solution.events[1] == branch_event_solution
        # event_solution must be at key 1 in the graph solutions branch events
        # dictionary
        assert graph_solution.branch_points[1] == branch_event_solution
        # there must be only 1 loop event and only 1 event in the graph
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
        branch_event_solution = BranchEventSolution(
            [GraphSolution()],
            meta_data={
                "EventType": "Branch"
            }
        )
        break_event_solution = EventSolution(
            is_break_point=True,
            meta_data={
                "EventType": "Break"
            }
        )
        loop_event_solution = LoopEventSolution(
            [GraphSolution()],
            meta_data={
                "EventType": "Loop"
            }
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
        loop_event_solution.expand(3)
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


class TestBranchEventSolution:
    """Class to test methods of :class:`BranchEventSolution`
    """
    @staticmethod
    def test_expand(
        branch_event_solution: BranchEventSolution
    ) -> None:
        """Tests :class:`BranchEventSolution`.`expand`

        :param branch_event_solution: Fixture providing a
        :class:`BranchEventSolution`
        :type branch_event_solution: :class:`BranchEventSolution`
        """
        branch_event_solution.expand(
            num_expansion=2
        )
        TestBranchEventSolution.check_branch_point_expanded_solutions(
            branch_event_solution
        )

    @staticmethod
    def check_branch_point_expanded_solutions(
        branch_point: BranchEventSolution
    ) -> None:
        """Method to check that the given test :class:`BranchEventSolution`
        has been expanded correctly

        :param branch_point: The :class:`BranchEventSolution`
        :type branch_point: :class:`BranchEventSolution`
        """
        # solutions should have been expanded
        assert branch_point.expanded_solutions
        # there should be 4 combinations
        assert len(branch_point.expanded_solutions) == 3
        results_all = []
        # checks that the 4 combinations are distinct
        for solution in branch_point.expanded_solutions:
            # each solution should have a length of 2
            assert len(solution) == 2
            results = []
            for i in range(2):
                for j in range(2):
                    if (
                        solution[0] == branch_point.graph_solutions[i]
                        and solution[1] == branch_point.graph_solutions[j]
                    ):
                        results.append((i, j))
            results_all.extend(results)
        assert len(results_all) == 3
        assert all(
            results_all[i] != results_all[j]
            for i in range(3)
            for j in range(3)
            if i != j
        )


class TestGraphSolutionsExpansions:
    """Tests of :class:`GraphSolution` for the expansion of loops and branch
    points.
    """
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
            combination=graph_simple,
            event_key=2
        )
        TestGraphSolutionsExpansions.check_loop_replacement(
            graph_with_loop=graph_with_loop,
            loop_event=loop_event
        )

    @staticmethod
    def check_loop_replacement(
        graph_with_loop: GraphSolution,
        loop_event: LoopEventSolution
    ) -> None:
        """Method to check that the given recombined loop solution are correct

        :param graph_with_loop: The :class:`GraphSolution` that the loop sub
        :class:`GraphSolution` has been recombined with
        :type graph_with_loop: :class:`GraphSolution`
        :param loop_event: The :class:`LoopEventSolution` that has been
        replaced in the parent :class:`GraphSolution`
        :type loop_event: :class:`LoopEventSolution`
        """
        # check attributes are correct
        assert check_length_attr(
            graph_with_loop,
            lens=[1, 5, 0, 0, 1, 0],
            attrs=[
                "start_events", "events",
                "branch_points", "break_points",
                "end_events", "loop_events"
            ]
        )
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
    def test_input_branch_graph_solutions(
        graph_with_branch: GraphSolution,
        graph_simple: GraphSolution,
        graph_single_event: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`input_branch_graph_solutions` for the
        following setup:

        (Start)->(Branch)->(End)

        The sub-graph solution combination of the Branch event is

        (Start)->(Middle)->(End)

        (Middle)

        The resulting sequence after branch expansion should be

                          ->(Middle)-----------------|
        (Start)->(Branch)-|                          |->(End)
                          ->(Start)->(Middle)->(End)-|

        :param graph_with_branch: Fixture providing a :class:`GraphSolution`
        containing a :class:`BranchEventSolution`
        :type graph_with_branch: :class:`GraphSolution`
        :param graph_simple: Fixture providing a :class:`GraphSolution` of a
        simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        :param graph_single_event: Fixture providing a :class:`GraphSolution`
        with a single :class:`EventSolution`
        :type graph_single_event: :class:`GraphSolution`
        """
        event_key = 2
        event = graph_with_branch.events[2]
        post_event = graph_with_branch.events[3]
        combination = (
            graph_simple,
            graph_single_event
        )
        GraphSolution.input_branch_graph_solutions(
            solution=graph_with_branch,
            combination=combination,
            event_key=event_key
        )
        # check attributes are correct
        assert check_length_attr(
            graph_with_branch,
            lens=[1, 7, 1, 0, 1, 0],
            attrs=[
                "start_events", "events",
                "branch_points", "break_points",
                "end_events", "loop_events"
            ]
        )
        # check that the branch event and its previously following event have
        # been disconnected
        assert event not in post_event.previous_events
        assert post_event not in event.post_events
        # check start events of branch combinations are correct
        assert graph_simple.events[1] in event.post_events
        assert graph_single_event.events[1] in event.post_events
        assert event in graph_simple.events[1].previous_events
        assert event in graph_single_event.events[1].previous_events
        # check end event of branch combinations are correct
        assert graph_simple.events[3] in post_event.previous_events
        assert graph_single_event.events[1] in post_event.previous_events
        assert post_event in graph_simple.events[3].post_events
        assert post_event in graph_single_event.events[1].post_events
        # check one path
        assert check_solution_correct(
            solution=graph_with_branch,
            event_types=[
                "Start", "Branch", "Start", "Middle", "End", "End"
            ]
        )
        # check the other path by reversing the branch events post events list
        event.post_events = list(reversed(event.post_events))
        assert check_solution_correct(
            solution=graph_with_branch,
            event_types=[
                "Start", "Branch", "Middle", "End"
            ]
        )

    @staticmethod
    def test_expand_nested_sub_graph_event_solution_loop_no_nesting(
        loop_event_solution: LoopEventSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`expand_nested_subgraph_event_solutions` for a
        :class:`LoopEventSolution` when the sub :class:`GraphSolution`'s
        contain no :class:`SubGraphEventSolution`'s

        :param loop_event_solution: Fixture prvoding a
        :class:`LoopEventSolution`
        :type loop_event_solution: :class:`LoopEventSolution`
        """
        TestGraphSolutionsExpansions.check_events_no_nesting(
            loop_event_solution
        )

    @staticmethod
    def test_expand_nested_sub_graph_event_solution_branch_no_nesting(
        branch_event_solution: BranchEventSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`expand_nested_subgraph_event_solutions` for a
        :class:`BranchEventSolution` when the sub :class:`GraphSolution`'s
        contain no :class:`SubGraphEventSolution`'s

        :param branch_event_solution: Fixture prvoding a
        :class:`BranchEventSolution`
        :type branch_event_solution: :class:`BranchEventSolution`
        """
        TestGraphSolutionsExpansions.check_events_no_nesting(
            branch_event_solution
        )

    @staticmethod
    def check_events_no_nesting(
        event: BranchEventSolution | LoopEventSolution
    ) -> None:
        """Method to check the method
        :class:`GraphSolution`.`expand_nested_subgraph_event_solutions` is not
        affecting the given :class:`SubGraphEventSolution`'s when it has no
        nested :class:`SubGraphEventSolution`'s

        :param event: The :class:`SubGraphEventSolution` to test
        :type event: :class:`BranchEventSolution` | :class:`LoopEventSolution`
        """
        sub_graph_solutions = event.graph_solutions
        GraphSolution.expand_nested_subgraph_event_solution(
            event=event,
            num_loops=3,
            num_branches=2
        )
        expanded_sub_graph_solutions = event.graph_solutions
        assert all(
            before_expansion == after_expansion
            for before_expansion, after_expansion in zip(
                sub_graph_solutions, expanded_sub_graph_solutions
            )
        )

    @staticmethod
    def test_apply_sub_graph_event_solution_sub_graph_loop(
        graph_with_loop: GraphSolution,
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`apply_sub_graph_event_solution_sub_graph`
        for a :class:`GraphSolution` with a :class:`LoopEventSolution` by
        applying a simple 3 sequence :class:`GraphSolution` in its place using
        :class:`GraphSolution`.`replace_loop_event_with_sub_graph_solution` as
        the application function.

        The parent sequence is:

        (Start)->(Loop)->(End)

        The sequence to replace the loop event and combine into the parent
        sequence is:

        (Start)->(Middle)->(End)

        The resulting sequence after application
        should be

        (Start)->(Start)->(Middle)->(End)->(End)

        :param graph_with_loop: Fixture providing a :class:`GraphSolution`
        containing a :class:`LoopEventSolution`
        :type graph_with_loop: :class:`GraphSolution`
        :param graph_simple: Fixture providing a simple 3
        :class:`EventSolution` sequence :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        graph_replaced = (
            GraphSolution.apply_sub_graph_event_solution_sub_graph(
                solution=graph_with_loop,
                combination=graph_simple,
                event_key=2,
                application_function=(
                    GraphSolution.replace_loop_event_with_sub_graph_solution
                )
            )
        )
        # check that the grpah solution is correct
        check_solution_correct(
            solution=graph_replaced,
            event_types=["Start", "Start", "Middle", "End", "End"]
        )
        # check attributes are correct
        assert check_length_attr(
            graph_replaced,
            lens=[1, 5, 0, 0, 1, 0],
            attrs=[
                "start_events", "events",
                "branch_points", "break_points",
                "end_events", "loop_events"
            ]
        )

    @staticmethod
    def test_apply_sub_graph_event_solution_sub_graph_branch(
        graph_with_branch: GraphSolution,
        graph_simple: GraphSolution,
        graph_single_event: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`apply_sub_graph_event_solution_sub_graph`
        for a :class:`GraphSolution` with a :class:`BranchEventSolution` by
        applying a simple 3 event sequence :class:`GraphSolution` and single
        event sequence :class:`GraphSolution` using
        :class:`GraphSolution`.`input_branch_graph_solutions` as
        the application function.

        The parent sequence is:

        (Start)->(Branch)->(End)

        The sub-graph solution combination of the Branch event is

        (Start)->(Middle)->(End)

        (Middle)

        The resulting sequence after application should be

                          ->(Middle)-----------------|
        (Start)->(Branch)-|                          |->(End)
                          ->(Start)->(Middle)->(End)-|

        :param graph_with_branch: Fixture providing a :class:`GraphSolution`
        containing a :class:`BranchEventSolution`
        :type graph_with_branch: :class:`GraphSolution`
        :param graph_simple: Fixture providing a :class:`GraphSolution` of a
        simple 3 event sequence
        :type graph_simple: :class:`GraphSolution`
        :param graph_single_event: Fixture providing a :class:`GraphSolution`
        with a single :class:`EventSolution`
        :type graph_single_event: :class:`GraphSolution`
        """
        graph_replaced = (
            GraphSolution.apply_sub_graph_event_solution_sub_graph(
                solution=graph_with_branch,
                combination=(
                    graph_simple,
                    graph_single_event
                ),
                event_key=2,
                application_function=(
                    GraphSolution.input_branch_graph_solutions
                )
            )
        )
        # check attributes are correct
        assert check_length_attr(
            graph_replaced,
            lens=[1, 7, 1, 0, 1, 0],
            attrs=[
                "start_events", "events",
                "branch_points", "break_points",
                "end_events", "loop_events"
            ]
        )

        # check one path
        assert check_solution_correct(
            solution=graph_replaced,
            event_types=[
                "Start", "Branch", "Start", "Middle", "End", "End"
            ]
        )
        # check the other path by reversing the branch events post events list
        graph_replaced.events[2].post_events = list(
            reversed(graph_replaced.events[2].post_events)
        )
        assert check_solution_correct(
            solution=graph_replaced,
            event_types=[
                "Start", "Branch", "Middle", "End"
            ]
        )

    @staticmethod
    def test_get_temp_combined_graph_solutions_loop(
        graph_with_loop: GraphSolution,
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`get_temp_combined_graph_solutions` by
        replacing an expanded :class:`LoopEventSolution`
        in its parent :class:`GraphSolution` with combinations of loops for a
        number of loops equal to 2

        The parent sequence is:

        (Start)->(Loop)->(End)

        The sequences to replace the loop event and combine into the parent
        sequence are:

        (Middle)->(Middle)

        (Middle)->(Start)->(Middle)->(End)

        (Start)->(Middle)->(End)->(Start)->(Middle)->(End)

        Start)->(Middle)->(End)->(Middle)

        The resulting sequences after recombination should be

        (Start)->(Middle)->(Middle)->(End)

        (Start)->(Middle)->(Start)->(Middle)->(End)->(End)

        (Start)->(Start)->(Middle)->(End)->(Start)->(Middle)->(End)->(End)

        (Start)->Start)->(Middle)->(End)->(Middle)->(End)



        :param graph_with_loop: Fixture providing a :class:`GraphSolution`
        containing a :class:`LoopEventSolution`
        :type graph_with_loop: :class:`GraphSolution`
        :param graph_simple: Fixture providing a simple 3
        :class:`EventSolution` sequence :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        loop_event = graph_with_loop.loop_events[2]
        loop_event.graph_solutions.append(graph_simple)
        loop_event.expand(2)
        combined_graphs = GraphSolution.get_temp_combined_graph_solutions(
            combined_graph_solutions=[graph_with_loop],
            event=loop_event,
            event_key=2,
            application_function=(
                GraphSolution.replace_loop_event_with_sub_graph_solution
            )
        )
        TestGraphSolutionsExpansions.check_loop_expansion_and_recombination(
            combined_graphs=combined_graphs
        )

    @staticmethod
    def check_loop_expansion_and_recombination(
        combined_graphs: list[GraphSolution]
    ) -> None:
        """Method to check that the tests reconbination of expanded loop
        :class:`GraphSolution`'s is correct

        :param combined_graphs: The list of recombined :class:`GraphSolution`
        :type combined_graphs: `list`[:class:`GraphSolution`]
        """
        assert len(combined_graphs) == 4
        assert all(
            2 not in graph_sol.events
            for graph_sol in combined_graphs
        )
        # first solution
        first_sol = [
            "Start", "Middle", "Middle", "End"
        ]
        # second solution
        second_sol = [
            "Start", "Middle", "Start", "Middle", "End", "End"
        ]
        # third solution
        third_sol = [
            "Start", "Start", "Middle", "End", "Start", "Middle", "End", "End"
        ]
        # fourth solution
        fourth_sol = [
            "Start", "Start", "Middle", "End", "Middle", "End"
        ]
        event_type_sequences = [first_sol, second_sol, third_sol, fourth_sol]
        # check that the solution sequences are correct
        check_multiple_solutions_correct(
            solutions=combined_graphs,
            event_types_sequences=event_type_sequences
        )

    @staticmethod
    def test_get_temp_combined_graph_solutions_branch(
        graph_with_branch: GraphSolution,
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`get_temp_combined_graph_solutions` by
        replacing an expanded :class:`BranchEventSolution`
        in its parent :class:`GraphSolution` with number of branches equal to
        2.

        The parent sequence is:

        (Start)->(Branch)->(End)

        The sub-graph solution combinations of the Branch event are

        ((Start)->(Middle)->(End), (Middle))
        ((Middle), (Middle))
        ((Start)->(Middle)->(End), (Start)->(Middle)->(End))

        The resulting sequences after combining with the parent sequence are

                          ->(Middle)-----------------|
        (Start)->(Branch)-|                          |->(End)
                          ->(Start)->(Middle)->(End)-|

                          ->(Middle)-|
        (Start)->(Branch)-|          |->(End)
                          ->(Middle)-|

                          ->(Start)->(Middle)->(End)-|
        (Start)->(Branch)-|                          |->(End)
                          ->(Start)->(Middle)->(End)-|

        :param graph_with_branch: Fixture providing a :class:`GraphSolution`
        containing a :class:`BranchEventSolution`
        :type graph_with_branch: :class:`GraphSolution`
        """
        branch_event = graph_with_branch.branch_points[2]
        branch_event.expand(2)
        combined_graphs = GraphSolution.get_temp_combined_graph_solutions(
            combined_graph_solutions=[graph_with_branch],
            event=branch_event,
            event_key=2,
            application_function=(
                GraphSolution.input_branch_graph_solutions
            )
        )
        TestGraphSolutionsExpansions.check_branch_expansion_and_recombination(
            combined_graphs=combined_graphs
        )

    @staticmethod
    def check_branch_expansion_and_recombination(
        combined_graphs: list[GraphSolution]
    ) -> None:
        """Method to check that the tests recombination of expanded branch
        :class:`GraphSolution`'s is correct

        :param combined_graphs: The list of recombined :class:`GraphSolution`
        :type combined_graphs: `list`[:class:`GraphSolution`]
        """
        assert len(combined_graphs) == 3
        # check the first branches
        # first possibilities
        possibilities = [
            ["Start", "Branch", "Start", "Middle", "End", "End"],
            ["Start", "Branch", "Middle", "End"]
        ]
        combinations = combinations_with_replacement(possibilities, r=2)
        all_is_sol = []
        for combination in combinations:
            is_sol = []
            for graph_sol in combined_graphs:
                graph_sol_copy = copy(graph_sol)
                branch_1 = check_solution_correct(
                    graph_sol_copy,
                    combination[0]
                )
                graph_sol_copy.events[2].post_events = list(
                    reversed(graph_sol_copy.events[2].post_events)
                )
                branch_2 = check_solution_correct(
                    graph_sol_copy,
                    combination[1]
                )
                if branch_1 and branch_2:
                    is_sol.append(True)
            all_is_sol.append(is_sol)
        assert all(
            len(is_sol) == 1
            for is_sol in all_is_sol
        )

    @staticmethod
    def test_combine_nested_solutions_no_nesting(
        graph_with_branch: GraphSolution,
        graph_with_loop: GraphSolution,
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`combine_nested_solutions`
        when there are no nested :class:`SubGraphEventSolution`'s

        The parent sequence is

        (Start)->(Branch)->(End)->(Start)->(Loop)->(End)

        The sub-graph solution combinations of the Branch event are

        ((Start)->(Middle)->(End), (Middle))
        ((Middle), (Middle))
        ((Start)->(Middle)->(End), (Start)->(Middle)->(End))

        The sequences to replace the loop event and combine into the parent
        sequence are:

        (Middle)->(Middle)

        (Middle)->(Start)->(Middle)->(End)

        (Start)->(Middle)->(End)->(Start)->(Middle)->(End)

        Start)->(Middle)->(End)->(Middle)

        The resulting sequence are too large to show here but are product
        combination of the following branch and then loop sequences added
        together end to start. The branch sequences are:



                          ->(Middle)-----------------|
        (Start)->(Branch)-|                          |->(End)
                          ->(Start)->(Middle)->(End)-|

                          ->(Middle)-|
        (Start)->(Branch)-|          |->(End)
                          ->(Middle)-|

                          ->(Start)->(Middle)->(End)-|
        (Start)->(Branch)-|                          |->(End)
                          ->(Start)->(Middle)->(End)-|

        The loop sequences are

        (Start)->(Middle)->(Middle)->(End)

        (Start)->(Middle)->(Start)->(Middle)->(End)->(End)

        (Start)->(Start)->(Middle)->(End)->(Start)->(Middle)->(End)->(End)

        (Start)->Start)->(Middle)->(End)->(Middle)->(End)


        :param graph_with_branch: Fixture providing a :class:`GraphSolution`
        containing a :class:`BranchEventSolution`
        :type graph_with_branch: :class:`GraphSolution`
        :param graph_with_loop: Fixture providing a :class:`GraphSolution`
        containing a :class:`LoopEventSolution`
        :type graph_with_loop: :class:`GraphSolution`
        :param graph_simple: Fixture providing a simple 3
        :class:`EventSolution` sequence :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        loop_event = graph_with_loop.loop_events[2]
        loop_event.graph_solutions.append(graph_simple)
        graph = graph_with_branch + graph_with_loop
        combined_solutions = graph.combine_nested_solutions(
            num_loops=2,
            num_branches=2
        )
        assert len(combined_solutions) == 12
        # solutions for loop graph
        # first solution
        first_sol = [
            "Start", "Middle", "Middle", "End"
        ]
        # second solution
        second_sol = [
            "Start", "Middle", "Start", "Middle", "End", "End"
        ]
        # third solution
        third_sol = [
            "Start", "Start", "Middle", "End", "Start", "Middle", "End", "End"
        ]
        # fourth solution
        fourth_sol = [
            "Start", "Start", "Middle", "End", "Middle", "End"
        ]
        event_type_sequences = [first_sol, second_sol, third_sol, fourth_sol]
        # possibilities for branch graph
        possibilities = [
            ["Start", "Branch", "Start", "Middle", "End", "End"],
            ["Start", "Branch", "Middle", "End"]
        ]
        branch_combinations = combinations_with_replacement(possibilities, r=2)
        all_is_sol = []
        # loop over all combinations of branches and loops
        for loop_graph_sol in event_type_sequences:
            for branch_combination in branch_combinations:
                combo_0 = branch_combination[0] + loop_graph_sol
                combo_1 = branch_combination[1] + loop_graph_sol
                is_sol = []
                for graph_sol in combined_solutions:
                    graph_sol_copy = copy(graph_sol)
                    branch_1 = check_solution_correct(
                        graph_sol_copy,
                        combo_0
                    )
                    graph_sol_copy.events[2].post_events = list(
                        reversed(graph_sol_copy.events[2].post_events)
                    )
                    branch_2 = check_solution_correct(
                        graph_sol_copy,
                        combo_1
                    )
                    if branch_1 and branch_2:
                        is_sol.append(True)
                all_is_sol.append(is_sol)
        # prove that only one graph sol has the same sequence as each
        # combination
        assert all(
            len(is_sol) == 1
            for is_sol in all_is_sol
        )

    @staticmethod
    def test_expand_nested_subgraph_event_solutions_loop_nested_loop(
        graph_with_nested_loop: GraphSolution,
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`expand_nested_subgraph_event_solutions` to see
        if the nested loop within the loop is expanded correctly

        :param graph_with_nested_loop: Fixture providing a
        :class:`GraphSolution` with a nested loop
        :type graph_with_nested_loop: :class:`GraphSolution`
        :param graph_simple: Fixture providing a simple 3
        :class:`EventSolution` sequence :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        loop_event = graph_with_nested_loop.loop_events[2]
        loop_event.graph_solutions[0].loop_events[2].graph_solutions.append(
            graph_simple
        )
        GraphSolution.expand_nested_subgraph_event_solution(
            event=loop_event,
            num_loops=2,
            num_branches=2
        )
        TestGraphSolutionsExpansions.check_loop_expansion_and_recombination(
            combined_graphs=loop_event.graph_solutions
        )

    @staticmethod
    def test_expand_nested_subgraph_event_solutions_loop_nested_branch(
        graph_with_nested_loop: GraphSolution,
        graph_with_branch: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`expand_nested_subgraph_event_solutions` to see
        if the nested branch within the loop is expanded correctly

        :param graph_with_nested_loop: Fixture providing a
        :class:`GraphSolution` with a nested loop
        :type graph_with_nested_loop: :class:`GraphSolution`
        :param graph_with_branch: Fixture providing a :class:`GraphSolution`
        containing a :class:`BranchEventSolution`
        :type graph_with_branch: :class:`GraphSolution`
        """
        loop_event = graph_with_nested_loop.loop_events[2]
        loop_event.graph_solutions = [graph_with_branch]
        GraphSolution.expand_nested_subgraph_event_solution(
            event=loop_event,
            num_loops=2,
            num_branches=2
        )
        TestGraphSolutionsExpansions.check_branch_expansion_and_recombination(
            combined_graphs=loop_event.graph_solutions
        )

    @staticmethod
    def test_expand_nested_subgraph_event_solution_branch_nested_loop(
        graph_with_branch: GraphSolution,
        graph_with_loop: GraphSolution,
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`expand_nested_subgraph_event_solutions` to see
        if the nested loop within the branch is expanded correctly

        :param graph_with_branch: Fixture providing a :class:`GraphSolution`
        containing a :class:`BranchEventSolution`
        :type graph_with_branch: :class:`GraphSolution`
        :param graph_with_loop: Fixture providing a :class:`GraphSolution`
        containing a :class:`LoopEventSolution`
        :type graph_with_loop: :class:`GraphSolution`
        :param graph_simple: Fixture providing a simple 3
        :class:`EventSolution` sequence :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        branch_event = graph_with_branch.branch_points[2]
        graph_with_loop.loop_events[2].graph_solutions.append(graph_simple)
        branch_event.graph_solutions = [graph_with_loop]
        GraphSolution.expand_nested_subgraph_event_solution(
            event=branch_event,
            num_loops=2,
            num_branches=2
        )
        TestGraphSolutionsExpansions.check_loop_expansion_and_recombination(
            combined_graphs=branch_event.graph_solutions
        )

    @staticmethod
    def test_expand_nested_subgraph_event_solution_branch_nested_branch(
        graph_with_branch: GraphSolution,
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`expand_nested_subgraph_event_solutions` to see
        if the nested branch within the branch is expanded correctly

        :param graph_with_branch: Fixture providing a :class:`GraphSolution`
        containing a :class:`BranchEventSolution`
        :type graph_with_branch: :class:`GraphSolution`
        """
        branch_event = graph_with_branch.branch_points[2]
        graph_with_branch_copy = deepcopy(graph_with_branch)
        branch_event.graph_solutions = [graph_with_branch_copy]
        GraphSolution.expand_nested_subgraph_event_solution(
            event=branch_event,
            num_loops=2,
            num_branches=2
        )
        TestGraphSolutionsExpansions.check_branch_expansion_and_recombination(
            combined_graphs=branch_event.graph_solutions
        )

    @staticmethod
    def test_combine_nested_solutions_nesting(
        graph_with_nested_loop: GraphSolution,
        graph_with_branch: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`combine_nested_solutions`
        for a situation of a :class:`GraphSolution` with a branch event
        containing a sub :class:`GraphSolution` containing a nested branch and
        also with a loop event containing a sub :class:`GraphSolution`
        containing a nested loop.

        :param graph_with_nested_loop: Fixture providing a
        :class:`GraphSolution` with a nested loop
        :type graph_with_nested_loop: :class:`GraphSolution`
        :param graph_with_branch: Fixture providing a :class:`GraphSolution`
        containing a :class:`BranchEventSolution`
        """
        graph_with_branch = deepcopy(graph_with_branch)
        branch_event = graph_with_branch.branch_points[2]
        graph_with_branch_copy = deepcopy(graph_with_branch)
        branch_event.graph_solutions = [graph_with_branch_copy]
        graph = graph_with_nested_loop + graph_with_branch
        combined_graphs = graph.combine_nested_solutions(
            num_loops=2,
            num_branches=2
        )
        assert len(combined_graphs) == 6
        loop_graph_sequence = [
            "Start", "Start", "Middle", "Middle", "End",
            "Start", "Middle", "Middle", "End", "End"
        ]
        sequences = [
            [
                "Start", "Branch", "Start", "Branch", "Middle", "End", "End"
            ],
            [
                "Start", "Branch", "Start", "Branch", "Start", "Middle", "End",
                "End", "End"
            ]
        ]
        # add loop graph sequence to start of sequences
        sequences = [
            loop_graph_sequence + sequence
            for sequence in sequences
        ]
        sequence_appearance_count = {
            0: 0,
            1: 0
        }
        # check that both sequence path possibilities appear 12 times
        for combined_graph in combined_graphs:
            copied_graph_0 = deepcopy(combined_graph)
            copied_graph_1 = deepcopy(combined_graph)
            copied_graph_1.branch_points[5].post_events = list(
                reversed(
                    copied_graph_1.branch_points[5].post_events
                )
            )
            copied_graph_2 = deepcopy(copied_graph_0)
            copied_graph_3 = deepcopy(copied_graph_1)

            for copied_graph in [copied_graph_2, copied_graph_3]:
                for branch_point in list(
                    copied_graph.branch_points.values()
                )[1:]:
                    branch_point.post_events = list(
                        reversed(
                            branch_point.post_events
                        )
                    )
            for copied_graph in [
                copied_graph_0, copied_graph_1, copied_graph_2, copied_graph_3
            ]:
                for i, sequence in enumerate(sequences):
                    if check_solution_correct(
                        copied_graph,
                        sequence
                    ):
                        sequence_appearance_count[i] += 1
        assert all(
            count == 12
            for count in sequence_appearance_count.values()
        )


class TestGraphSolutionGenerateAuditEvents:
    """Grouping of tests for generating audit event sequence jsons.
    """
    @staticmethod
    def test_update_events_event_template_id_template(
        graph_two_start_two_end: GraphSolution
    ) -> None:
        """Tests :class:`GraphSolution`.`update_events_event_template_id` when
        the keyword argument `is_template` is equal to `True`

        :param graph_two_start_two_end: Fixture providing a
        :class:`GraphSolution` with two start and two end points
        :type graph_two_start_two_end: :class:`GraphSolution`
        """
        graph_two_start_two_end.update_events_event_template_id(
            is_template=True
        )
        for event_key, event in graph_two_start_two_end.events.items():
            assert event.event_template_id == str(event_key)

    @staticmethod
    def test_update_events_event_template_id_uids(
        graph_two_start_two_end: GraphSolution
    ) -> None:
        """Tests :class:`GraphSolution`.`update_events_event_template_id` when
        the keyword argument `is_template` is equal to `False`. Checks if the
        id follows the correct format

        :param graph_two_start_two_end: Fixture providing a
        :class:`GraphSolution` with two start and two end points
        :type graph_two_start_two_end: :class:`GraphSolution`
        """
        uuid4hex = re.compile(
            '[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}\\Z', re.I
        )
        graph_two_start_two_end.update_events_event_template_id(
            is_template=False
        )
        for event_key, event in graph_two_start_two_end.events.items():
            assert event.event_template_id != str(event_key)
            assert bool(
                uuid4hex.match(event.event_template_id.replace("-", ""))
            )

    @staticmethod
    def test_create_graph_edge_list_of_events(
        graph_simple: GraphSolution
    ) -> None:
        """Tests creation of an edge list from an iterable of event using
        :class:`GraphSolution`.`create_graph_edge_list`

        :param graph_simple: Fixture providing a simple :class:`GraphSolution`
        sequence
        :type graph_simple: :class:`GraphSolution`
        """
        edges = GraphSolution.create_graph_edge_list(
            nodes=graph_simple.events.values(),
            link_func=lambda x: x.get_post_event_edge_tuples()
        )
        assert len(edges) == 2
        assert (
            edges[0][0] == graph_simple.events[1]
            and edges[0][1] == graph_simple.events[2]
        )
        assert (
            edges[1][0] == graph_simple.events[2]
            and edges[1][1] == graph_simple.events[3]
        )

    @staticmethod
    def test_create_networkx_graph_from_nodes_list_of_events(
        graph_simple: GraphSolution
    ) -> None:
        """Tests creation of an edge list from an iterable of
        :class:`EventSolution`'s

        :param graph_simple: Fixture providing a simple :class:`GraphSolution`
        sequence
        :type graph_simple: :class:`GraphSolution`
        """
        nx_graph = GraphSolution.create_networkx_graph_from_nodes(
            nodes=graph_simple.events.values(),
            link_func=lambda x: x.get_post_event_edge_tuples()
        )
        assert isinstance(nx_graph, nx.DiGraph)
        assert all(
            node in list(graph_simple.events.values())
            for node in nx_graph
        )

    @staticmethod
    def test_get_topologically_sorted_event_sequence(
        graph_two_start_two_end: GraphSolution
    ) -> None:
        """Tests
        :class:`GraphSolution`.`get_topologically_sorted_event_sequence`
        for :class:`GraphSolution` with two start and two end points


        :param graph_two_start_two_end: Fixture providing a
        :class:`GraphSolution` with two start and two end points
        :type graph_two_start_two_end: :class:`GraphSolution`
        """

        events = list(graph_two_start_two_end.events.values())
        shuffled_events = events[3:5] + events[2:3] + events[:2]
        ordered_events = GraphSolution.get_topologically_sorted_event_sequence(
            events=shuffled_events
        )
        for ordered_event, event in zip(
            ordered_events,
            events
        ):
            assert ordered_event == event

    @staticmethod
    def test_get_audit_event_lists_template(
        graph_simple: GraphSolution
    ) -> None:
        """Tests :class:`GraphSolution`.`get_audit_event_lists` when
        `is_template` is set to `True`

        :param graph_simple: Fixture providing a simple :class:`GraphSolution`
        sequence
        :type graph_simple: :class:`GraphSolution`
        """
        graph_simple.update_events_event_template_id(
            is_template=True
        )
        audit_event_data = GraphSolution.get_audit_event_lists(
            events=graph_simple.events.values()
        )
        TestGraphSolutionGenerateAuditEvents.check_audit_events_template(
            audit_event_data=audit_event_data
        )

    @staticmethod
    def check_audit_events_template(
        audit_event_data: tuple[list[dict], list[str]]
    ) -> None:
        """Helper function to check the output from
        :class:`GraphSolution`.`get_audit_event_lists` for the fixture
        `graph_simple` when the job is a considered a template

        :param audit_event_data: A tuple providing a list of json audit events
        and a list of the audit event ids present
        :type audit_event_data: `tuple`[`list`[`dict`], `list`[`str`]]
        """
        expected_audit_event_list = [
            {
                "jobName": "default_job_name",
                "jobId": "jobID",
                "eventType": "Start",
                "eventId": "1",
                "applicationName": "default_application_name"
            },
            {
                "jobName": "default_job_name",
                "jobId": "jobID",
                "eventType": "Middle",
                "eventId": "2",
                "applicationName": "default_application_name",
                "previousEventIds": "1"
            },
            {
                "jobName": "default_job_name",
                "jobId": "jobID",
                "eventType": "End",
                "eventId": "3",
                "applicationName": "default_application_name",
                "previousEventIds": "2"
            }
        ]
        timestamp = re.compile(
            '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\\Z',
            re.I
        )
        for audit_event, expected_audit_event in zip(
            audit_event_data[0],
            expected_audit_event_list
        ):
            for field, value in expected_audit_event.items():
                assert audit_event[field] == value
            assert bool(timestamp.match(audit_event["timestamp"]))
        assert len(audit_event_data[1]) == 3
        assert all(
            audit_event["eventId"] in audit_event_data[1]
            for audit_event in audit_event_data[0]
        )

    @staticmethod
    def test_get_audit_event_lists_example(
        graph_simple: GraphSolution
    ) -> None:
        """Tests :class:`GraphSolution`.`get_audit_event_lists` when
        `is_template` is set to `False`

        :param graph_simple: Fixture providing a simple :class:`GraphSolution`
        sequence
        :type graph_simple: :class:`GraphSolution`
        """
        for event in graph_simple.events.values():
            event.meta_data["applicationName"] = "application name"
        graph_simple.update_events_event_template_id(
            is_template=False
        )
        audit_event_data = GraphSolution.get_audit_event_lists(
            events=graph_simple.events.values(),
            is_template=False,
            job_name="job name"
        )
        TestGraphSolutionGenerateAuditEvents.check_audit_events_not_template(
            audit_event_data=audit_event_data
        )

    @staticmethod
    def check_audit_events_not_template(
        audit_event_data
    ) -> None:
        """Helper function to check the output from
        :class:`GraphSolution`.`get_audit_event_lists` for the fixture
        `graph_simple` when the job is a considered not a template

        :param audit_event_data: A tuple providing a list of json audit events
        and a list of the audit event ids present
        :type audit_event_data: `tuple`[`list`[`dict`], `list`[`str`]]
        """
        uuid4hex = re.compile(
            '[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}\\Z', re.I
        )
        timestamp = re.compile(
            '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\\Z',
            re.I
        )
        expected_audit_event_list = [
            {
                "jobName": "job name",
                "eventType": "Start",
                "applicationName": "application name"
            },
            {
                "jobName": "job name",
                "eventType": "Middle",
                "applicationName": "application name",
            },
            {
                "jobName": "job name",
                "eventType": "End",
                "applicationName": "application name",
            }
        ]
        previous_event_id = ""
        for audit_event, expected_audit_event in zip(
            audit_event_data[0],
            expected_audit_event_list,
        ):
            for field, value in expected_audit_event.items():
                assert audit_event[field] == value
            assert bool(timestamp.match(audit_event["timestamp"]))
            assert bool(
                uuid4hex.match(audit_event["jobId"].replace("-", ""))
            )
            assert bool(
                uuid4hex.match(audit_event["eventId"].replace("-", ""))
            )
            if "previousEventIds" in audit_event:
                previous_event_id == audit_event["eventId"]
            previous_event_id = audit_event["eventId"]
        assert len(audit_event_data[1]) == 3
        assert all(
            audit_event["eventId"] in audit_event_data[1]
            for audit_event in audit_event_data[0]
        )

    @staticmethod
    def test_create_audit_event_jsons_template(
        graph_simple: GraphSolution
    ) -> None:
        """Tests :class:`GraphSolution`.`get_create_audit_event_jsons` when
        `is_template` is set to `True`

        :param graph_simple: Fixture providing a simple :class:`GraphSolution`
        sequence
        :type graph_simple: :class:`GraphSolution`
        """
        audit_event_data = graph_simple.create_audit_event_jsons()
        TestGraphSolutionGenerateAuditEvents.check_audit_events_template(
            audit_event_data=audit_event_data
        )

    @staticmethod
    def test_create_audit_event_jsons_no_template(
        graph_simple: GraphSolution
    ) -> None:
        """Tests :class:`GraphSolution`.`get_create_audit_event_jsons` when
        `is_template` is set to `False` and a job name is provided

        :param graph_simple: Fixture providing a simple :class:`GraphSolution`
        sequence
        :type graph_simple: :class:`GraphSolution`
        """
        for event in graph_simple.events.values():
            event.meta_data["applicationName"] = "application name"
        audit_event_data_with_plot = graph_simple.create_audit_event_jsons(
            is_template=False,
            job_name="job name"
        )
        TestGraphSolutionGenerateAuditEvents.check_audit_events_not_template(
            audit_event_data=audit_event_data_with_plot[:2]
        )
        assert audit_event_data_with_plot[2] is None


def test_get_audit_event_jsons_and_templates_templates(
    graph_simple: GraphSolution
) -> list[GraphSolution]:
    """Tests `get_create_audit_event_jsons_and_templates` when
    `is_template` is set to `True`

    :param graph_simple: Fixture providing a simple :class:`GraphSolution`
    sequence
    :type graph_simple: :class:`GraphSolution`
    :return: Returns a list of :class:`GraphSolution`'s
    :rtype: `list`[:class:`GraphSolution`]
    """
    graph_solutions = [
        graph_simple,
        deepcopy(graph_simple)
    ]
    audit_events_data_tuples = get_audit_event_jsons_and_templates(
        graph_solutions=graph_solutions
    )
    for audit_events_data_tuple in audit_events_data_tuples:
        TestGraphSolutionGenerateAuditEvents.check_audit_events_template(
            audit_event_data=audit_events_data_tuple[:2]
        )
        assert audit_events_data_tuple[2] is None
    return graph_solutions


def test_get_audit_event_jsons_and_templates_no_template(
    graph_simple: GraphSolution
) -> None:
    """Tests `get_create_audit_event_jsons_and_templates` when
    `is_template` is set to `False` and a job name is provided

    :param graph_simple: Fixture providing a simple :class:`GraphSolution`
    sequence
    :type graph_simple: :class:`GraphSolution`
    """
    for event in graph_simple.events.values():
        event.meta_data["applicationName"] = "application name"
    graph_solutions = [
        graph_simple,
        deepcopy(graph_simple)
    ]
    audit_events_data_tuples = get_audit_event_jsons_and_templates(
        graph_solutions=graph_solutions,
        is_template=False,
        job_name="job name"
    )
    for audit_events_data_tuple in audit_events_data_tuples:
        TestGraphSolutionGenerateAuditEvents.check_audit_events_not_template(
            audit_event_data=audit_events_data_tuple[:2]
        )
        assert audit_events_data_tuple[2] is None


def test_get_categorised_audit_event_jsons(
    graph_simple: GraphSolution
) -> None:
    """Tests `get_categorised_audit_event_jsons`

    :param graph_simple: Fixture providing a simple :class:`GraphSolution`
    sequence
    :type graph_simple: :class:`GraphSolution`
    """
    graph_solutions = test_get_audit_event_jsons_and_templates_templates(
        graph_simple=graph_simple
    )
    categorised_graph_solutions = {
        "category1": (
            graph_solutions,
            True
        ),
        "category2": (
            graph_solutions,
            False
        )
    }
    categorised_audit_event_data = get_categorised_audit_event_jsons(
        categorised_graph_solutions
    )
    assert "category1" in categorised_audit_event_data
    assert "category2" in categorised_audit_event_data
    assert categorised_audit_event_data["category1"][1]
    assert not categorised_audit_event_data["category2"][1]
    for audit_event_data_category in categorised_audit_event_data.values():
        for audit_event_data in audit_event_data_category[0]:
            TestGraphSolutionGenerateAuditEvents.check_audit_events_template(
                audit_event_data=audit_event_data
            )


class TestEventSolutionDynamicControl:
    """Tests for usage of :class:`DynamicControl` in :class:`EventSolution`
    """
    @staticmethod
    def test_parse_dynamic_control_events(
        graph_branch_event_id_tuple: GraphSolution
    ) -> GraphSolution:
        """Tests the method
        :class:`GraphSolution`.`parse_dynamic_control_events`

        :param graph_branch_event_id_tuple: Fixture providing a
        :class:`GraphSolution` with a :class:`BranchEventSolution`.
        :type graph_branch_event_id_tuple: :class:`GraphSolution`
        :return: Returns the :class:`GraphSolution` with the
        :class:`BranchEventSolution` updated with a :class:`DynamicControl`
        :rtype: :class:`GraphSolution`
        """
        for event in graph_branch_event_id_tuple.branch_points.values():
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
            assert len(event.dynamic_control_events) == 1
            assert "X" in event.dynamic_control_events
            assert isinstance(
                event.dynamic_control_events["X"],
                DynamicControl
            )
            assert (
                event.event_id_tuple
            ) == event.dynamic_control_events["X"].user
            assert (
                event.event_id_tuple
            ) == event.dynamic_control_events["X"].provider
        return graph_branch_event_id_tuple

    @staticmethod
    def test_create_dynamic_control_audit_event_data() -> None:
        event = (
            TestGraphSolutionDynamicControl.test_filter_user_dynamic_controls()
        )
        dyanamic_control_providers = (
            event.create_dynamic_control_audit_event_data()
        )
        assert len(dyanamic_control_providers) == 1
        assert "X" in dyanamic_control_providers
        assert dyanamic_control_providers["X"]["dataItemType"] == "BRANCHCOUNT"
        assert dyanamic_control_providers["X"]["value"] == 0

    @staticmethod
    def test_get_audit_event_json_dynamic_controls():
        event = (
            TestGraphSolutionDynamicControl.test_filter_user_dynamic_controls()
        )
        audit_event_json = event.get_audit_event_json(
            job_id="1",
            time_stamp="00:00:00",
        )
        assert "X" in audit_event_json
        assert all(
            name not in audit_event_json
            for name in ["Y", "Z"]
        )
        assert audit_event_json["X"]["dataItemType"] == "BRANCHCOUNT"
        assert audit_event_json["X"]["value"] == 0


class TestGraphSolutionDynamicControl:
    """Tests functionality of :class:`GraphSolution`
    counting :class:`DynamicControl` providers and users
    """
    @staticmethod
    def test_filter_user_dynamic_controls() -> EventSolution:
        """Tests :class:`GraphSolution`.`filter_user_dynamic_controls`

        :return: Returns :class:`EventSolution` with dynamic controls
        :rtype: :class:`EventSolution`
        """
        event = EventSolution(
            meta_data={
                "EventType": "Event"
            },
            event_id_tuple=("Event", 0)
        )
        event.parse_dynamic_control_events(
            {
                "X": {
                    "control_type": "BRANCHCOUNT",
                    "provider": {
                        "EventType": "Event",
                        "occurenceId": 0
                    },
                    "user": {
                        "EventType": "Other_Event",
                        "occurenceId": 0
                    }
                },
                "Y": {
                    "control_type": "LOOPCOUNT",
                    "provider": {
                        "EventType": "Other_Event",
                        "occurenceId": 0
                    },
                    "user": {
                        "EventType": "Event",
                        "occurenceId": 0
                    }
                },
                "Z": {
                    "control_type": "BRANCHCOUNT",
                    "provider": {
                        "EventType": "Other_Event",
                        "occurenceId": 0
                    },
                    "user": {
                        "EventType": "Event",
                        "occurenceId": 0
                    }
                }
            }
        )
        # filter user DynamicControl's
        filtered_dynamic_controls = GraphSolution.filter_user_dynamic_controls(
            event=event
        )
        # The two user Dynamic controls must have been filtered out
        assert len(filtered_dynamic_controls) == 1
        # The DynamicControl filtered out has name X
        assert "X" in filtered_dynamic_controls
        return event

    @staticmethod
    def test_count_dynamic_controls_branches_single_branch_event(
        graph_branch_event_id_tuple: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`count_dynamic_controls`
        for a :class:`GraphSolution` with a single :class:`BranchEventSolution`

        :param graph_branch_event_id_tuple: Fixture providing a
        :class:`GraphSolution` containing a single :class:`BranchEventSolution`
        :type graph_branch_event_id_tuple: :class:`GraphSolution`
        """
        graph = (
            TestEventSolutionDynamicControl.test_parse_dynamic_control_events(
                graph_branch_event_id_tuple=graph_branch_event_id_tuple
            )
        )
        graph_solutions = graph.combine_nested_solutions(
            num_loops=2,
            num_branches=10
        )
        for graph_sol in graph_solutions:
            GraphSolution.count_dynamic_controls(
                graph_sol.events[2],
                graph_sol.events[2].dynamic_control_events
            )
            assert graph_sol.events[2].dynamic_control_events["X"].count == 10

    @staticmethod
    def test_count_dynamic_controls_branches_multiple_branch_events(
        graph_multiple_branches: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`count_dynamic_controls`
        for a :class:`GraphSolution` with multiple un-nested
        :class:`BranchEventSolution`'s

        :param graph_multiple_branches: Fixture providing a
        :class:`GraphSolution` with multiple un-nested
        :class:`BranchEventSolution`'s
        :type graph_multiple_branches: :class:`GraphSolution`
        """
        graph = (
            TestEventSolutionDynamicControl.test_parse_dynamic_control_events(
                graph_branch_event_id_tuple=graph_multiple_branches
            )
        )
        graph_solutions = graph.combine_nested_solutions(
            num_loops=2,
            num_branches=10
        )
        for graph_sol in graph_solutions:
            for key in [2, 5]:
                GraphSolution.count_dynamic_controls(
                    graph_sol.events[key],
                    graph_sol.events[key].dynamic_control_events
                )
                assert (
                    graph_sol.events[key].dynamic_control_events["X"].count
                ) == 10

    @staticmethod
    def test_count_dynamic_controls_loops_single_loop_event(
        graph_loop_event_count_id_tuple: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`count_dynamic_controls`
        for a :class:`GraphSolution` with a single :class:`LoopEventSolution`
        with a provider and user of a :class:`DynamicControl` LCNT added

        :param graph_loop_event_count_id_tuple: Fixture providing a
        :class:`GraphSolution` with a :class:`LoopEventSolution` with a
        :class:`DynamicControl` LCNT
        :type graph_loop_event_count_id_tuple: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_loop_event_count_id_tuple.combine_nested_solutions(
                num_loops=10,
                num_branches=2
            )
        )
        GraphSolution.count_dynamic_controls(
            graph_solutions[0].events[1],
            graph_solutions[0].events[1].dynamic_control_events
        )
        assert (
            graph_solutions[0].events[1].dynamic_control_events["X"].count
        ) == 10

    @staticmethod
    def test_count_dynamic_controls_loops_multiple_loop_events(
        graph_multiple_loop_events: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`count_dynamic_controls`
        for a :class:`GraphSolution` with multiple :class:`LoopEventSolution`'s
        with providers and users of a :class:`DynamicControl` LCNT added

        :param graph_multiple_loop_events: Fixture providing a
        :class:`GraphSolution` containing multiple :class:`LoopEventSolution`'s
        :type graph_multiple_loop_events: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_multiple_loop_events.combine_nested_solutions(
                num_loops=10,
                num_branches=2
            )
        )
        for provider_event_key in [1, 4]:
            GraphSolution.count_dynamic_controls(
                graph_solutions[0].events[provider_event_key],
                graph_solutions[0].events[
                    provider_event_key
                ].dynamic_control_events
            )
            assert (
                graph_solutions[0].events[
                    provider_event_key
                ].dynamic_control_events["X"].count
            ) == 10

    @staticmethod
    def test_count_dynamic_controls_branches_nested_branch_prov_inside(
        graph_branch_nested_branch: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`count_dynamic_controls`
        for a :class:`GraphSolution` with a single :class:`BranchEventSolution`
        containing a nested :class:`BranchEventSolution`. The provider of the
        :class:`DynamicControl` is inside the top level
        :class:`BranchEventSolution`

        :param graph_branch_nested_branch: Fixture providing a
        :class:`GraphSolution` containing a :class:`BranchEventSolution` with
        a nested :class:`BranchEventSolution` with provider inside top level
        :class:`BranchEventSolution`
        :type graph_branch_nested_branch: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_branch_nested_branch.combine_nested_solutions(
                num_loops=2,
                num_branches=4
            )
        )
        for graph_sol in graph_solutions:
            assert len(graph_sol.branch_points) == 5
            for branch_event in graph_sol.branch_points.values():
                GraphSolution.count_dynamic_controls(
                    branch_event,
                    branch_event.dynamic_control_events
                )
                assert (
                    branch_event.dynamic_control_events["X"].count
                ) == 4

    @staticmethod
    def test_count_dynamic_controls_branches_nested_branch_prov_outside(
        graph_branch_nested_branch_prov_outside: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`count_dynamic_controls`
        for a :class:`GraphSolution` with a single :class:`BranchEventSolution`
        containing a nested :class:`BranchEventSolution`. The provider of the
        :class:`DynamicControl` is outside the top level
        :class:`BranchEventSolution`

        :param graph_branch_nested_branch_prov_outside: Fixture providing a
        :class:`GraphSolution` containing a :class:`BranchEventSolution` with
        a nested :class:`BranchEventSolution` with provider outside the top
        level :class:`BranchEventSolution`
        :type graph_branch_nested_branch_prov_outside: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_branch_nested_branch_prov_outside.combine_nested_solutions(
                num_loops=2,
                num_branches=4
            )
        )
        for graph_sol in graph_solutions:
            assert len(graph_sol.branch_points) == 5
            # first branch (both user and provider)
            branch_event_1 = graph_sol.branch_points[2]
            GraphSolution.count_dynamic_controls(
                branch_event_1,
                branch_event_1.dynamic_control_events
            )
            assert (
                branch_event_1.dynamic_control_events["X"].count
            ) == 4
            # second branch provider before first branch and user within first
            # branch
            provider_event = graph_sol.events[1]
            GraphSolution.count_dynamic_controls(
                provider_event,
                provider_event.dynamic_control_events
            )
            # the count should be 16 as the branch user is within another
            # branch
            assert (
                provider_event.dynamic_control_events["X"].count
            ) == 16

    @staticmethod
    def test_count_dynamic_controls_branches_nested_loop_prov_outside(
        graph_branch_nested_loop_prov_outside: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`count_dynamic_controls`
        for a :class:`GraphSolution` with a single :class:`BranchEventSolution`
        containing a nested :class:`LoopEventSolution`. The provider of the
        :class:`DynamicControl` is outside the top level
        :class:`BranchEventSolution`

        :param graph_branch_nested_loop_prov_outside: Fixture providing a
        :class:`GraphSolution` containing a :class:`BranchEventSolution` with
        a nested :class:`LoopEventSolution` with provider outside the top
        level :class:`BranchEventSolution`
        :type graph_branch_nested_loop_prov_outside: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_branch_nested_loop_prov_outside.combine_nested_solutions(
                num_loops=2,
                num_branches=2
            )
        )
        assert len(graph_solutions) == 1
        provider_event = graph_solutions[0].events[1]
        GraphSolution.count_dynamic_controls(
            provider_event,
            provider_event.dynamic_control_events
        )
        assert (
            provider_event.dynamic_control_events["X"].count
        ) == 4
        branch_event_1 = graph_solutions[0].branch_points[2]
        GraphSolution.count_dynamic_controls(
            branch_event_1,
            branch_event_1.dynamic_control_events
        )
        assert (
            branch_event_1.dynamic_control_events["X"].count
        ) == 2

    @staticmethod
    def test_count_dynamic_controls_branches_nested_loop_prov_inside(
        graph_branch_nested_loop_prov_inside: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`count_dynamic_controls`
        for a :class:`GraphSolution` with a single :class:`BranchEventSolution`
        containing a nested :class:`LoopEventSolution`. The provider of the
        :class:`DynamicControl` is inside the top level
        :class:`BranchEventSolution`

        :param graph_branch_nested_loop_prov_inside: Fixture providing a
        :class:`GraphSolution` containing a :class:`BranchEventSolution` with
        a nested :class:`LoopEventSolution` with provider inside the top
        level :class:`BranchEventSolution`
        :type graph_branch_nested_loop_prov_inside: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_branch_nested_loop_prov_inside.combine_nested_solutions(
                num_loops=4,
                num_branches=4
            )
        )
        assert len(graph_solutions) == 1
        for post_event in graph_solutions[0].branch_points[2].post_events:
            GraphSolution.count_dynamic_controls(
                post_event,
                post_event.dynamic_control_events
            )
            assert (
                post_event.dynamic_control_events["X"].count
            ) == 4
        branch_event_1 = graph_solutions[0].branch_points[2]
        GraphSolution.count_dynamic_controls(
            branch_event_1,
            branch_event_1.dynamic_control_events
        )
        assert (
            branch_event_1.dynamic_control_events["X"].count
        ) == 4

    @staticmethod
    def test_update_control_event_counts_branches_single_branch_event(
        graph_branch_event_id_tuple: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`update_control_event_counts`
        for a :class:`GraphSolution` with a single :class:`BranchEventSolution`

        :param graph_branch_event_id_tuple: Fixture providing a
        :class:`GraphSolution` containing a single :class:`BranchEventSolution`
        :type graph_branch_event_id_tuple: :class:`GraphSolution`
        """
        graph = (
            TestEventSolutionDynamicControl.test_parse_dynamic_control_events(
                graph_branch_event_id_tuple=graph_branch_event_id_tuple
            )
        )
        graph_solutions = graph.combine_nested_solutions(
            num_loops=2,
            num_branches=10
        )
        for graph_sol in graph_solutions:
            graph_sol.update_control_event_counts()
            assert graph_sol.events[2].dynamic_control_events["X"].count == 10

    @staticmethod
    def test_update_control_event_counts_branches_multiple_branch_events(
        graph_multiple_branches: GraphSolution
    ) -> None:
        """Tests the method :class:`GraphSolution`.`count_dynamic_controls`
        for a :class:`GraphSolution` with multiple un-nested
        :class:`BranchEventSolution`'s

        :param graph_multiple_branches: Fixture providing a
        :class:`GraphSolution` with multiple un-nested
        :class:`BranchEventSolution`'s
        :type graph_multiple_branches: :class:`GraphSolution`
        """
        graph = (
            TestEventSolutionDynamicControl.test_parse_dynamic_control_events(
                graph_branch_event_id_tuple=graph_multiple_branches
            )
        )
        graph_solutions = graph.combine_nested_solutions(
            num_loops=2,
            num_branches=10
        )
        for graph_sol in graph_solutions:
            graph_sol.update_control_event_counts()
            for key in [2, 5]:
                assert (
                    graph_sol.events[key].dynamic_control_events["X"].count
                ) == 10

    @staticmethod
    def test_update_control_event_counts_loops_single_loop_event(
        graph_loop_event_count_id_tuple: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`update_control_event_counts`
        for a :class:`GraphSolution` with a single :class:`LoopEventSolution`
        with a provider and user of a :class:`DynamicControl` LCNT added

        :param graph_loop_event_count_id_tuple: Fixture providing a
        :class:`GraphSolution` with a :class:`LoopEventSolution` with a
        :class:`DynamicControl` LCNT
        :type graph_loop_event_count_id_tuple: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_loop_event_count_id_tuple.combine_nested_solutions(
                num_loops=10,
                num_branches=2
            )
        )
        graph_solutions[0].update_control_event_counts()
        assert (
            graph_solutions[0].events[1].dynamic_control_events["X"].count
        ) == 10

    @staticmethod
    def test_update_control_event_counts_loops_multiple_loop_events(
        graph_multiple_loop_events: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`update_control_event_counts`
        for a :class:`GraphSolution` with multiple :class:`LoopEventSolution`'s
        with providers and users of a :class:`DynamicControl` LCNT added

        :param graph_multiple_loop_events: Fixture providing a
        :class:`GraphSolution` containing multiple :class:`LoopEventSolution`'s
        :type graph_multiple_loop_events: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_multiple_loop_events.combine_nested_solutions(
                num_loops=10,
                num_branches=2
            )
        )
        graph_solutions[0].update_control_event_counts()
        for provider_event_key in [1, 4]:
            assert (
                graph_solutions[0].events[
                    provider_event_key
                ].dynamic_control_events["X"].count
            ) == 10

    @staticmethod
    def test_update_control_event_counts_branches_nested_branch_prov_inside(
        graph_branch_nested_branch: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`update_control_event_counts`
        for a :class:`GraphSolution` with a single :class:`BranchEventSolution`
        containing a nested :class:`BranchEventSolution`. The provider of the
        :class:`DynamicControl` is inside the top level
        :class:`BranchEventSolution`

        :param graph_branch_nested_branch: Fixture providing a
        :class:`GraphSolution` containing a :class:`BranchEventSolution` with
        a nested :class:`BranchEventSolution` with provider inside top level
        :class:`BranchEventSolution`
        :type graph_branch_nested_branch: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_branch_nested_branch.combine_nested_solutions(
                num_loops=2,
                num_branches=4
            )
        )
        for graph_sol in graph_solutions:
            assert len(graph_sol.branch_points) == 5
            graph_sol.update_control_event_counts()
            for branch_event in graph_sol.branch_points.values():
                assert (
                    branch_event.dynamic_control_events["X"].count
                ) == 4

    @staticmethod
    def test_update_control_event_counts_branches_nested_branch_prov_outside(
        graph_branch_nested_branch_prov_outside: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`update_control_event_counts`
        for a :class:`GraphSolution` with a single :class:`BranchEventSolution`
        containing a nested :class:`BranchEventSolution`. The provider of the
        :class:`DynamicControl` is outside the top level
        :class:`BranchEventSolution`

        :param graph_branch_nested_branch_prov_outside: Fixture providing a
        :class:`GraphSolution` containing a :class:`BranchEventSolution` with
        a nested :class:`BranchEventSolution` with provider outside the top
        level :class:`BranchEventSolution`
        :type graph_branch_nested_branch_prov_outside: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_branch_nested_branch_prov_outside.combine_nested_solutions(
                num_loops=2,
                num_branches=4
            )
        )
        for graph_sol in graph_solutions:
            graph_sol.update_control_event_counts()
            assert len(graph_sol.branch_points) == 5
            # first branch (both user and provider)
            branch_event_1 = graph_sol.branch_points[2]
            assert (
                branch_event_1.dynamic_control_events["X"].count
            ) == 4
            # second branch provider before first branch and user within first
            # branch
            provider_event = graph_sol.events[1]
            # the count should be 16 as the branch user is within another
            # branch
            assert (
                provider_event.dynamic_control_events["X"].count
            ) == 16

    @staticmethod
    def test_update_control_event_counts_branches_nested_loop_prov_outside(
        graph_branch_nested_loop_prov_outside: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`update_control_event_counts`
        for a :class:`GraphSolution` with a single :class:`BranchEventSolution`
        containing a nested :class:`LoopEventSolution`. The provider of the
        :class:`DynamicControl` is outside the top level
        :class:`BranchEventSolution`

        :param graph_branch_nested_loop_prov_outside: Fixture providing a
        :class:`GraphSolution` containing a :class:`BranchEventSolution` with
        a nested :class:`LoopEventSolution` with provider outside the top
        level :class:`BranchEventSolution`
        :type graph_branch_nested_loop_prov_outside: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_branch_nested_loop_prov_outside.combine_nested_solutions(
                num_loops=2,
                num_branches=2
            )
        )
        assert len(graph_solutions) == 1
        graph_solutions[0].update_control_event_counts()
        provider_event = graph_solutions[0].events[1]
        assert (
            provider_event.dynamic_control_events["X"].count
        ) == 4
        branch_event_1 = graph_solutions[0].branch_points[2]
        assert (
            branch_event_1.dynamic_control_events["X"].count
        ) == 2

    @staticmethod
    def test_update_control_event_counts_branches_nested_loop_prov_inside(
        graph_branch_nested_loop_prov_inside: GraphSolution
    ) -> None:
        """Tests the method
        :class:`GraphSolution`.`update_control_event_counts`
        for a :class:`GraphSolution` with a single :class:`BranchEventSolution`
        containing a nested :class:`LoopEventSolution`. The provider of the
        :class:`DynamicControl` is inside the top level
        :class:`BranchEventSolution`

        :param graph_branch_nested_loop_prov_inside: Fixture providing a
        :class:`GraphSolution` containing a :class:`BranchEventSolution` with
        a nested :class:`LoopEventSolution` with provider inside the top
        level :class:`BranchEventSolution`
        :type graph_branch_nested_loop_prov_inside: :class:`GraphSolution`
        """
        graph_solutions = (
            graph_branch_nested_loop_prov_inside.combine_nested_solutions(
                num_loops=4,
                num_branches=4
            )
        )
        assert len(graph_solutions) == 1
        graph_solutions[0].update_control_event_counts()
        for post_event in graph_solutions[0].branch_points[2].post_events:
            assert (
                post_event.dynamic_control_events["X"].count
            ) == 4
        branch_event_1 = graph_solutions[0].branch_points[2]
        assert (
            branch_event_1.dynamic_control_events["X"].count
        ) == 4

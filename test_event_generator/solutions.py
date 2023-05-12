# pylint: disable=R0904
# pylint: disable=R0902
# pylint: disable=C0302
"""
Classes and methods to process and combine solutions
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self, Optional, Iterable, Callable
from copy import copy, deepcopy
from itertools import product, combinations_with_replacement
import random
import datetime
import uuid

import networkx as nx
import matplotlib.pyplot as plt


class EventSolution:
    """Class to hold info and links to other events (previous or post) for a
    particular graph solution

    :param is_branch: Boolean indicating if the Event is a branch point,
    defaults to `False`
    :type is_branch: `bool`, optional
    :param is_break_point: Boolean indicating if the Event is a break point,
    defaults to `False`
    :type is_break_point: `bool`, optional
    :param meta_data: Optional meta data to include with the event, defaults
    to `None`
    :type meta_data: :class:`Optional`[`dict`], optional
    """
    def __init__(
        self,
        is_branch: bool = False,
        is_break_point: bool = False,
        meta_data: Optional[dict] = None,
        event_id_tuple: Optional[tuple[str, int]] = None,
        **kwargs
    ) -> None:
        """Constructor method
        """
        self.is_branch = is_branch
        self.is_break_point = is_break_point
        self.meta_data = meta_data
        self.event_id_tuple = event_id_tuple
        self.previous_events: list[EventSolution] = []
        self.post_events: list[EventSolution] = []
        self.dynamic_control_events: dict[str, DynamicControl] = {}
        self.event_template_id: str = ""
        _ = kwargs
        self.count = 0
        # parse meta data
        self.parse_meta_data(meta_data)

    def __repr__(self) -> str:
        """Dunder method to return a string representation of the object

        :return: Returns the EventType and count number (if over zero)
        :rtype: `str`
        """
        if self.count == 0:
            return self.meta_data["EventType"]
        return f'{self.meta_data["EventType"]}{self.count}'

    def add_prev_event(self, event_solution: Self) -> None:
        """Method to add an :class:`EventSolution` to the list of previous
        events of the instance.

        :param event_solution: :class:`EventSolution` to add to the list of
        previous events.
        :type event_solution: `Self`
        """
        self.previous_events.append(event_solution)

    def add_post_event(self, event_solution: Self) -> None:
        """Method to add an :class:`EventSolution` to the list of post
        events of the instance.

        :param event_solution: :class:`EventSolution` to add to the list of
        post events.
        :type event_solution: `Self`
        """
        self.post_events.append(event_solution)

    def extend_branches(
        self,
        branch_count: int
    ) -> list[EventSolution]:
        """Method to expand branch events for a given number of branches from
        the event

        :param branch_count: Number of branches extending from the Event
        :type branch_count: `int`
        :raises RuntimeError: Raises an Exception if the instance is note a
        branch point.
        :raises RuntimeError: Raises an Exception if the instance has no post
        events.
        :return: Returns a list of newly instantiated :class:`EventSolution`'s
        created from a random choice (with replacement) of the instance post
        events.
        :rtype: `list`[:class:`EventSolution`]
        """
        if not self.is_branch:
            raise RuntimeError(
                "Method called but the Event is not a branching Event"
            )
        if len(self.post_events) == 0:
            raise RuntimeError(
                "There are no post events to create duplicates of."
            )
        # choose events randomly from post_event_uids with replacement
        # subract the number of pose events from the branch count as that
        # number of branch events already exists
        events: list[EventSolution] = random.choices(
            self.post_events,
            k=branch_count - len(self.post_events)
        )
        # loop over choices and copy event updating
        # previous and post events with new event
        new_events = []
        for event in events:
            new_event = copy(event)
            new_event.add_to_connected_events()
            new_events.append(new_event)
        return new_events

    def add_to_previous_events(self) -> None:
        """Method to add the instance to the list of post events for all the
        :class:`EventSolution`'s in the instances previous events list.
        """
        for event in self.previous_events:
            event.add_post_event(self)

    def add_to_post_events(self) -> None:
        """Method to add the instance to the list of previous events for all
        the :class:`EventSolution`'s in the instances post events list.
        """
        for event in self.post_events:
            event.add_prev_event(self)

    def add_to_connected_events(self) -> None:
        """Method to add the instance to it previous and post events list of
        post and previous events, respectively.
        """
        self.add_to_post_events()
        self.add_to_previous_events()

    @property
    def is_start(self) -> bool:
        """Property defining if the instance is a start event.

        :return: Boolean indicating if the instance is a start event.
        :rtype: `bool`
        """
        return len(self.previous_events) == 0

    @property
    def is_end(self) -> bool:
        """Property defining if the instance is an end event.

        :return: Boolean indicating if the instance is an end event.
        :rtype: `bool`
        """
        return len(self.post_events) == 0

    @property
    def event_template_id(self) -> str:
        """Getter for property event_template_id

        :return: Returns the value for event_template_id
        :rtype: `str`
        """
        return self._event_template_id

    @event_template_id.setter
    def event_template_id(self, template_id: str | int) -> None:
        """Setter for property event_template_id

        :param template_id: The value to set event_template_id
        :type template_id: `str` | `int`
        """
        if isinstance(template_id, int):
            template_id = str(template_id)
        self._event_template_id = template_id

    def get_audit_event_json(
        self,
        job_id: str,
        time_stamp: str,
        job_name: str = "default_job_name"
    ) -> dict:
        """Method to generate an audit event json for the instance with a
        given number in a timestamp seq.

        :param job_id: Unique id of the job the event is part of.
        :type job_id: `str`
        :param time_stamp: Timestamp string
        :type time_stamp: `str`
        :param job_name: The name of the job definition the event is part of,
        defaults to "default_job_name"
        :type job_name: `str`, optional
        :return: Returns a dictionary representing a JSON template for the
        audit event
        :rtype: `dict`
        """
        audit_json = {
            "jobName": job_name,
            "jobId": job_id,
            "eventType": self.meta_data["EventType"],
            "eventId": self.event_template_id,
            "timestamp": time_stamp,
            "applicationName": (
                self.meta_data["applicationName"]
                if "applicationName" in self.meta_data
                else "default_application_name"
            )
        }
        # add dynamic control data if there is any
        if self.dynamic_control_events:
            dynamic_control_providers = (
                self.create_dynamic_control_audit_event_data()
            )
            if dynamic_control_providers:
                audit_json = {
                    **audit_json,
                    **self.create_dynamic_control_audit_event_data()
                }
        if not self.is_start:
            audit_json["previousEventIds"] = self.get_previous_event_ids()
        return audit_json

    def get_previous_event_ids(self) -> str | list[str]:
        """Method to get the previous event ids of the
        :class:`EventSolution`'s in the previous_event list.

        :return: Returns a single string of the event_template_id if the
        previous_event list is of length 1, other wise returns a list of the
        event_template_id's for each event in the previous_event list.
        :rtype: `str` | `list`[`str`]
        """
        prev_event_ids = [
            prev_event.event_template_id
            for prev_event in self.previous_events
        ]
        if len(prev_event_ids) == 1:
            return prev_event_ids[0]
        return prev_event_ids

    def get_post_event_edge_tuples(
        self
    ) -> list[tuple[EventSolution, EventSolution]]:
        """Method to return a list of the directed edge tuples between the
        instance and its post events

        :return: Returns the list of directed edge tuples
        :rtype: `list`[`tuple`[:class:`EventSolution`, :class:`EventSolution`]]
        """
        if self.is_end:
            return []

        return [
            (self, event)
            for event in self.post_events
        ]

    def parse_meta_data(
        self,
        meta_data: dict
    ) -> None:
        """Method to parse meta data into the instance

        :param meta_data: Dictionary containing arbitrary meta data
        :type meta_data: `dict`
        """
        if not meta_data:
            return
        if "dynamic_control_events" in meta_data:
            self.parse_dynamic_control_events(
                meta_data["dynamic_control_events"]
            )
        self.parse_event_id_tuple(meta_data)

    def parse_event_id_tuple(
        self,
        meta_data: dict[str, str | int]
    ) -> None:
        """Method to parse event_id_tuple if both EventType and occurenceId
        fields are in the input meta_data dictionary

        :param meta_data: Input meta data dictionary
        :type meta_data: `dict`[`str`, `str`  |  `int`]
        """
        if "EventType" in meta_data and "occurenceId" in meta_data:
            self.event_id_tuple = (
                meta_data["EventType"],
                int(meta_data["occurenceId"])
            )

    def parse_dynamic_control_events(
        self,
        dynamic_control_events: dict[str, dict]
    ) -> None:
        """Method to parse dyanamic control data into the instance from a
        dictionary

        :param dynamic_control_events: Dictionary containing the dynamic
        control data must contain the following key in the sub dictionary:
        * `control_type`
        * `provider`
        * `user`
        :type dynamic_control_events: `dict`[`str`, `dict`]
        """
        for name, dynamic_control_event in dynamic_control_events.items():
            self.dynamic_control_events[
                name
            ] = DynamicControl(
                control_type=dynamic_control_event["control_type"],
                name=name,
                provider=(
                    dynamic_control_event["provider"]["EventType"],
                    int(dynamic_control_event["provider"]["occurenceId"])
                ),
                user=(
                    dynamic_control_event["user"]["EventType"],
                    int(dynamic_control_event["user"]["occurenceId"])
                )
            )

    def create_dynamic_control_audit_event_data(
        self
    ) -> dict[str, dict]:
        """Method to create dynamic control provider audit event data

        :return: Returns the dynamic control event data
        :rtype: `dict`[`str`, `dict`]
        """
        return {
            name: {
                "dataItemType": dynamic_control.control_type,
                "value": dynamic_control.count
            }
            for name, dynamic_control in self.dynamic_control_events.items()
            if self.event_id_tuple == dynamic_control.provider
        }


class SubGraphEventSolution(EventSolution, ABC):
    """Sub class of :class:`EventSolution` to act as a base abstract class
    for :class:`LoopEventSolution` and :class:`BranchEvent Solution`

    :param graph_solutions: List of sub :class:`GraphSolution`'s
    :type graph_solutions: `list`[:class:`GraphSolution`]
    :param meta_data: Optional meta-data to include with the
    :class:`EventSolution`, defaults to `None`
    :type meta_data: :class:`Optional`[`dict`], optional
    """
    def __init__(
        self,
        graph_solutions: list[GraphSolution],
        meta_data: Optional[dict] = None,
        **kwargs
    ) -> None:
        """Constructor method
        """
        super().__init__(
            meta_data=meta_data,
            **kwargs
        )
        self.graph_solutions = graph_solutions
        self.expanded_solutions: list[GraphSolution] = []

    @abstractmethod
    def expand(self, num_expansion: int) -> None:
        """Abstract method to expand the instance :class:`GraphSolution`'s

        :param num_expansion: The number to expand by
        :type num_expansion: `int`
        """
        # replace with method for subclasses

    @classmethod
    def make_new(
        cls,
        graph_solutions: list[GraphSolution],
        meta_data: Optional[dict] = None,
        **kwargs
    ) -> SubGraphEventSolution:
        """Class method to provide a new instance of the class of the instance

        :param graph_solutions: List of sub :class:`GraphSolution`'s
        :type graph_solutions: `list`[:class:`GraphSolution`]
        :param meta_data: Optional meta-data to include with the
        :class:`EventSolution`, defaults to `None`
        :type meta_data: :class:`Optional`[`dict`], optional
        :return: Returns an instance of the instance class
        :rtype: :class:`SubGraphEventSolution`
        """
        return cls(
            graph_solutions=graph_solutions,
            meta_data=meta_data,
            **kwargs
        )

    def __copy__(self) -> SubGraphEventSolution:
        """Copy dunder method

        :return: Returns a new instance of the class containing the identical
        graph_solutions, meta_data and expanded_solutions attributes of the
        instance
        :rtype: SubGraphEventSolution
        """
        # graph solutions must be the same (in memory) as the instance
        copied_sub_graph_event_solution = self.make_new(
            graph_solutions=self.graph_solutions,
            meta_data=self.meta_data
        )
        # make sure expanded solutions are the same (in memory) as the instance
        copied_sub_graph_event_solution.expanded_solutions = (
            self.expanded_solutions
        )
        return copied_sub_graph_event_solution


class LoopEventSolution(SubGraphEventSolution):
    """Sub-class of :class:`EventSolution` adding extra functionality to
    handle an :class:`EventSolution` that has sub graph solutions within it.

    :param graph_solutions: A list of :class:`GraphSolution` that the instance
    contains.
    :type graph_solutions: `list`[:class:`GraphSolution`]
    :param meta_data: Optional meta data to include with the event,
    defaults to `None`
    :type meta_data: :class:`Optional`[`dict`], optional
    """
    def __init__(
        self,
        graph_solutions: list[GraphSolution],
        meta_data: Optional[dict] = None,
        **kwargs
    ) -> None:
        """Constructor method
        """
        super().__init__(
            graph_solutions=graph_solutions,
            meta_data=meta_data,
            **kwargs
        )

    def expand(self, num_expansion: int) -> None:
        """Method to expand the loop

        :param num_expansion: The number of iterations of the loop
        :type num_expansion: `int`
        """
        # if the loop has already been expanded do nothing
        if self.expanded_solutions:
            return
        # split solutions into those with and without breaks
        solutions_no_break = []
        solutions_with_break = []
        for graph_solution in self.graph_solutions:
            if len(graph_solution.break_points) > 0:
                solutions_with_break.append(graph_solution)
            else:
                solutions_no_break.append(graph_solution)
        # get all possible solutions where a break has not occurred
        solutions_no_break_combos = list(
            product(
                solutions_no_break, repeat=num_expansion
            )
        )
        # setup list for all combinations of solutions with a break.
        # Initialised with the possible solutions with a break
        solutions_with_break_combos = self.solution_combinations_with_break(
            loop_count=num_expansion,
            solutions_no_break=solutions_no_break,
            solutions_with_break=solutions_with_break
        )
        # get all combinations of solutions by adding combination with no
        # break and combinations with a break
        solutions_combos = (
            solutions_no_break_combos + solutions_with_break_combos
        )
        # expand the solutions by summing the Graph solutions that are in a
        # combination tuple.
        self.expanded_solutions = self.expanded_solutions_from_solutions_combo(
            solutions_combos=solutions_combos
        )

    @staticmethod
    def get_solutions_with_break_after_n_repititions(
        repeat: int,
        solutions_no_break: list[GraphSolution],
        solutions_with_break: list[GraphSolution]
    ) -> list[tuple[GraphSolution, ...]]:
        """Method to obtain all the possible solution combinations of the loop
        that involve a break after a given number of repitions the loop is
        supposed to iterate for.

        :param repeat: The number of itertions the loop is supposed to
        complete without a break.
        :type repeat: `int`
        :param solutions_no_break: A list of :class:`GraphSolutions` for the
        solutions of the loop sub graph that do not contain a break point
        :type solutions_no_break: `list`[:class:`GraphSolution`]
        :param solutions_with_break: A list of :class:`GraphSolutions` for the
        solutions of the loop sub graph that do contain a break point
        :type solutions_with_break: `list`[`tuple`[:class:`GraphSolution`]]
        :return: Returns a list of combinations in tuples of
        :class:`GraphSolution`'s.
        :rtype: `list`[`tuple`[:class:`GraphSolution`, `...`]]
        """
        # get combinations before break solution
        sub_solutions_combos = list(
            product(
                solutions_no_break, repeat=repeat
            )
        )
        # create list of solutions by adding solutions with a break on top of
        # combinations of solutions without a break
        solutions_with_break_combos = [
            sub_solutions_no_break_combo + (solution_with_break, )
            for solution_with_break in solutions_with_break
            for sub_solutions_no_break_combo in sub_solutions_combos
        ]
        return solutions_with_break_combos

    @staticmethod
    def solution_combinations_with_break(
        loop_count: int,
        solutions_no_break: list[GraphSolution],
        solutions_with_break: list[GraphSolution]
    ) -> list[tuple[GraphSolution, ...]]:
        """Method to find all the possible combinations of loops with breaks

        :param loop_count: The number of iterations that should occur for the
        loop
        :type loop_count: `int`
        :param solutions_no_break: List of loop graph solutions that contain
        no breaks
        :type solutions_no_break: `list`[:class:`GraphSolution`]
        :param solutions_with_break: List of loop graph solutions that contain
        a break
        :type solutions_with_break: `list`[`tuple`[:class:`GraphSolution`]]
        :return: Returns a list of combinations in tuples of
        :class:`GraphSolution`'s.
        :rtype: `list`[`tuple`[:class:`GraphSolution`, `...`]]
        """
        solutions_with_break_combos = [
            (solution, )
            for solution in solutions_with_break
        ]
        for i in range(1, loop_count):
            solutions_with_break_combos.extend(
                LoopEventSolution.get_solutions_with_break_after_n_repititions(
                    repeat=i,
                    solutions_no_break=solutions_no_break,
                    solutions_with_break=solutions_with_break
                )
            )
        return solutions_with_break_combos

    @staticmethod
    def expanded_solutions_from_solutions_combo(
        solutions_combos: list[tuple[GraphSolution, ...]]
    ) -> list[GraphSolution]:
        """Method to expand the solutions from lists of solution combinations

        :param solutions_combos: List of solutions combinations in tuples of
        :class:`GraphSolution`'s
        :type solutions_combos: list[tuple[GraphSolution, ...]]
        :return: The list of exapnded combinations of :class:`GraphSolution`'s.
        :rtype: list[GraphSolution]
        """
        return [
            sum(solutions_combo)
            for solutions_combo in solutions_combos
        ]


class BranchEventSolution(SubGraphEventSolution):
    """Sub-class of :class:`EventSolution` adding extra functionality to
    handle an :class:`EventSolution` that has sub graph solutions within it.

    :param graph_solutions: A list of :class:`GraphSolution` that the instance
    contains.
    :type graph_solutions: `list`[:class:`GraphSolution`]
    :param meta_data: Optional meta data to include with the event,
    defaults to `None`
    :type meta_data: :class:`Optional`[`dict`], optional
    """
    def __init__(
        self,
        graph_solutions: list[GraphSolution],
        meta_data: Optional[dict] = None,
        **kwargs
    ) -> None:
        """Constructor method
        """
        super().__init__(
            graph_solutions=graph_solutions,
            meta_data=meta_data,
            **kwargs
        )

    def expand(self, num_expansion: int) -> None:
        """Method to find all combinations of branches

        :param num_expansion: Number of branches from branch event
        :type num_expansion: `int`
        """
        if self.expanded_solutions:
            return
        solutions_combos = list(
            combinations_with_replacement(
                self.graph_solutions, r=num_expansion
            )
        )
        self.expanded_solutions = solutions_combos


class GraphSolution:
    """Class that holds a sequence of :class:`EventSolution`'s that are
    held in an event dictionary at a unique key. :class:`EventSolution`'s may
    be sub-categorised - given information in the attributes - into:

    * start_events
    * end_events
    * loop_events
    * branch_points
    * break_points

    Within these dictionaries the :class:`EventSolution` holds the same key as
    in the events dictionary.

    An example of a sequence of :class:`EventSolution` that may be held is:

    (Start)->(Middle)->(End)

    Here:
    * the post event of (Start) is (Middle)
    * the previous event of (Middle) is (Start) and the post event is (End)
    * the previous event of (End) is (Middle)

    """
    def __init__(
        self,
    ) -> None:
        """Constructor method
        """
        self.start_events: dict[str, EventSolution] = {}
        self.end_events: dict[str, EventSolution] = {}
        self.loop_events: dict[str, LoopEventSolution] = {}
        self.branch_points: dict[str, BranchEventSolution] = {}
        self.break_points: dict[str, EventSolution] = {}
        self.events: dict[str, EventSolution] = {}
        self.event_dict_count: int = 0

    def parse_event_solutions(self, events: list[EventSolution]) -> None:
        """Method to parse a list of :class:`EventSolution` into the specific
        dictionaries of the instance.

        :param events: List of :class:`EventSolution`'s to be parsed
        :type events: `list`[:class:`EventSolution`]
        """
        for event in events:
            self.add_event(event)

    def _add_start_event(self, event: EventSolution) -> None:
        """Private method to add an :class:`EventSolution` instance to the
        dictionary of start events using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`EventSolution` to be added
        :type event: :class:`EventSolution`
        """
        self.start_events[self.event_dict_count] = event

    def _add_end_event(self, event: EventSolution) -> None:
        """Private method to add an :class:`EventSolution` instance to the
        dictionary of end events using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`EventSolution` to be added
        :type event: :class:`EventSolution`
        """
        self.end_events[self.event_dict_count] = event

    def _add_loop_event(self, event: LoopEventSolution) -> None:
        """Private method to add an :class:`LoopEventSolution` instance to the
        dictionary of loop events using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`LoopEventSolution` to be added
        :type event: :class:`LoopEventSolution`
        """
        self.loop_events[self.event_dict_count] = event

    def _add_branch_point(self, event: BranchEventSolution) -> None:
        """Private method to add an :class:`BranchEventSolution` instance to
        the dictionary of branch points using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`BranchEventSolution` to be added
        :type event: :class:`BranchEventSolution`
        """
        self.branch_points[self.event_dict_count] = event

    def _add_break_point(self, event: EventSolution) -> None:
        """Private method to add an :class:`EventSolution` instance to the
        dictionary of break points using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`EventSolution` to be added
        :type event: :class:`EventSolution`
        """
        self.break_points[self.event_dict_count] = event

    def add_event(self, event: EventSolution) -> None:
        """Private method to add an :class:`EventSolution` instance to the
        dictionary of events and updating the `event_dict_count` attribute by
        1 and using the new value `event_dict_count` as a key. Add the event
        to other instance dictionaries if the :class:`EventSolution` satisifes
        the criteria.

        :param event: :class:`EventSolution` to be added
        :type event: :class:`EventSolution`
        """
        self.event_dict_count += 1
        self.events[self.event_dict_count] = event
        if event.is_start:
            self._add_start_event(event)
        if event.is_end:
            self._add_end_event(event)
        if event.is_break_point:
            self._add_break_point(event)
        if isinstance(event, BranchEventSolution):
            self._add_branch_point(event)
        if isinstance(event, LoopEventSolution):
            self._add_loop_event(event)

    def remove_event(
        self,
        event_dict_key: int,
    ) -> None:
        """Remove an event from all of the instance dictionaries if they
        contain the given key.

        :param event_dict_key: The key which is used to remove the
        :class:`EventSolution` from the dictionaries.
        :type event_dict_key: `int`
        """
        for attr in [
            "events", "start_events", "end_events",
            "loop_events", "branch_points", "break_points"
        ]:
            attribute: dict[str, EventSolution] = getattr(self, attr)
            if event_dict_key in attribute:
                attribute.pop(event_dict_key)

    def __add__(self, other: GraphSolution) -> GraphSolution:
        """Dunder method to add instance to another :class:`GraphSolution`'s
        on the right of the addition sign.

        :param other: Right :class:`GraphSolution`
        :type other: :class:`GraphSolution`
        :return: Combined :class:`GraphSolution`
        :rtype: :class:`GraphSolution`
        """
        if not isinstance(other, GraphSolution):
            return deepcopy(self)
        return self.combine_graphs(self, other)

    def __radd__(self, other: GraphSolution) -> GraphSolution:
        """Dunder method to add instance to another :class:`GraphSolution`'s
        on the left of the addition sign.

        :param other: Left :class:`GraphSolution`
        :type other: :class:`GraphSolution`
        :return: Combined :class:`GraphSolution`
        :rtype: :class:`GraphSolution`
        """
        if not isinstance(other, GraphSolution):
            return deepcopy(self)
        return self.combine_graphs(other, self)

    @classmethod
    def combine_graphs(
        cls,
        left_graph: GraphSolution,
        right_graph: GraphSolution
    ) -> GraphSolution:
        """Method to combine two :class:`GraphSolution`'s together.

        :param left_graph: The :class:`GraphSolutions` where the events occure
        first.
        :type left_graph: :class:`GraphSolution`
        :param right_graph: The :class:`GraphSolutions` where the events occure
        first
        :type right_graph: :class:`GraphSolution`
        :return: The combined :class:`GraphSolution`
        :rtype: :class:`GraphSolution`
        """
        # copy graphs
        left_graph_copy = deepcopy(left_graph)
        if left_graph.break_points:
            return left_graph_copy
        right_graph_copy = deepcopy(right_graph)
        # instantiate combined graph
        combined_graph = cls()
        # update left graph end events post events with right graph start
        # events and vice versa
        for left_event in left_graph_copy.end_events.values():
            for right_event in right_graph_copy.start_events.values():
                left_event.add_post_event(right_event)
                right_event.add_prev_event(left_event)
        # parse events back into graph
        combined_graph.parse_event_solutions(
            list(left_graph_copy.events.values())
            + list(right_graph_copy.events.values())
        )
        return combined_graph

    def combine_nested_solutions(
        self,
        num_loops: int,
        num_branches: int
    ) -> list[GraphSolution]:
        """Method to expand and combine all nested sub graph solutions
        together recuresively with the parent graph solution returning all
        possible combinations.

        :param num_loops: The number of loops to expand
        :class:`LoopEventSolution`'s by.
        :type num_loops: `int`
        :param num_branches: The number of branches to expand
        :class:`BranchEventSolution`'s by.
        :type num_branches: `int`
        :return: The list of all possible combinations as completely expanded
        :class:`GraphSolution`'s
        :rtype: `list`[:class:`GraphSolution`]
        """
        combined_graph_solutions = [self]
        # loop through all loop event solutions
        # 1. expand all nested subgraphs and combine them together
        # 2. expand the loop itself
        # 3. combine the expanded and precombined subgraphs with the instance
        # solution
        for event_key, event in self.loop_events.items():
            GraphSolution.expand_nested_subgraph_event_solutions(
                event=event,
                num_loops=num_loops,
                num_branches=num_branches
            )
            event.expand(num_loops)
            combined_graph_solutions_temp = (
                GraphSolution.get_temp_combined_graph_solutions(
                    combined_graph_solutions=combined_graph_solutions,
                    event=event,
                    event_key=event_key,
                    application_function=(
                        self.replace_loop_event_with_sub_graph_solution
                    )
                )
            )
            combined_graph_solutions = combined_graph_solutions_temp

        # loop through all branch event solutions
        # 1. expand all nested subgraphs and combine them together
        # 2. expand the branch itself
        # 3. combine the expanded and precombined subgraphs with the instance
        # solution
        for event_key, event in self.branch_points.items():
            GraphSolution.expand_nested_subgraph_event_solutions(
                event=event,
                num_loops=num_loops,
                num_branches=num_branches
            )
            event.expand(num_branches)
            combined_graph_solutions_temp = (
                GraphSolution.get_temp_combined_graph_solutions(
                    combined_graph_solutions=combined_graph_solutions,
                    event=event,
                    event_key=event_key,
                    application_function=(
                        self.input_branch_graph_solutions
                    )
                )
            )
            combined_graph_solutions = combined_graph_solutions_temp
        return combined_graph_solutions

    @staticmethod
    def get_temp_combined_graph_solutions(
        combined_graph_solutions: list[GraphSolution],
        event: SubGraphEventSolution,
        event_key: int,
        application_function: Callable
    ) -> list[GraphSolution]:
        """Method to combine a list of expanded solutions to a list of graph
        solutions by either:
        * replacing a loop event with the expanded sub graph solutions
        * branching off a branch event with sub graph solutions and
        recombining to its following events
        TODO: Make more efficient

        :param combined_graph_solutions: List of :class:`GraphSolution`'s to
        combine expanded solutions with
        :type combined_graph_solutions: `list`[:class:`GraphSolution`]
        :param event: The :class:`SubGraphEventSolution` instance that holds
        the sub graph solutions.
        :type event: :class:`SubGraphEventSolution`
        :param event_key: The key value of the event in the
        :class:`GraphSolution`'s in the list of combined graph solutions
        :type event_key: `int`
        :param application_function: The application function used to apply
        the sub graph solutions to the parent graph solutions
        :type application_function: :class:`Callable`
        :return: Returns a list of the combined :class:`GraphSolution`'s
        :rtype: `list`[:class:`GraphSolution`]
        """
        combined_graph_solutions_temp: list[GraphSolution] = []
        for solution in combined_graph_solutions:
            for combination in event.expanded_solutions:
                solution_combined = (
                    GraphSolution.apply_sub_graph_event_solution_sub_graph(
                        solution=solution,
                        combination=combination,
                        event_key=event_key,
                        application_function=application_function
                    )
                )
                combined_graph_solutions_temp.append(solution_combined)
        return combined_graph_solutions_temp

    @staticmethod
    def apply_sub_graph_event_solution_sub_graph(
        solution: GraphSolution,
        combination: GraphSolution | tuple[GraphSolution],
        event_key: int,
        application_function: Callable
    ) -> "GraphSolution":
        """Method to apply sub graph solutions of an event solution to a
        parent :class:`GraphSolution`

        :param solution: The parent :class:`GraphSolution`
        :type solution: :class:`GraphSolution`
        :param combination: The sub graph solution combination to apply to the
        parent :class:`GraphSolution`
        :type combination: :class:`GraphSolution` |
        `tuple`[:class:`GraphSolution`]
        :param event_key: The key of the :class:`EventSolution` in the parent
        :class:`GraphSolution`
        :type event_key: `int`
        :param application_function: The application function used to apply
        the sub graph solutions to the parent graph solutions
        :type application_function: :class:`Callable`
        :return: Returns the combined :class:`GraphSolution`
        :rtype: :class:`GraphSolution`
        """
        solution_copy = deepcopy(solution)
        if isinstance(combination, tuple):
            combination_copy = tuple(
                deepcopy(graph_sol)
                for graph_sol in combination
            )
        else:
            combination_copy = deepcopy(
                combination
            )
        application_function(
            solution=solution_copy,
            combination=combination_copy,
            event_key=event_key
        )
        return solution_copy

    @staticmethod
    def expand_nested_subgraph_event_solutions(
        event: SubGraphEventSolution,
        num_loops: int,
        num_branches: int
    ) -> None:
        """MEthod to expand the sub graph within a
        :class:`SubGraphEventSolution`

        :param event: The :class:`SubGraphEventSolution`
        :type event: :class:`SubGraphEventSolution`
        :param num_loops: The number of loops to expand loops by
        :type num_loops: `int`
        :param num_branches: The number of branches to expand branches by
        :type num_branches: `int`
        """
        if event.expanded_solutions:
            return
        expanded_nested_solutions = []
        for graph_sol in event.graph_solutions:
            if graph_sol.loop_events or graph_sol.branch_points:
                expanded_nested_solutions.extend(
                    graph_sol.combine_nested_solutions(
                        num_loops=num_loops,
                        num_branches=num_branches
                    )
                )
            else:
                expanded_nested_solutions.append(graph_sol)
        event.graph_solutions = expanded_nested_solutions

    @staticmethod
    def input_branch_graph_solutions(
        solution: GraphSolution,
        combination: tuple[GraphSolution],
        event_key: int
    ) -> None:
        """Method to input the sub graph solutions of a
        :class:`BranchEventSolution` into a parent :class:`GraphSolution`

        :param solution: Parent :class:`GraphSolution`
        :type solution: :class:`GraphSolution`
        :param combination: The combination of :class:`GraphSolution`'s
        :type combination: `tuple`[:class:`GraphSolution`]
        :param event_key: The key within the parent :class:`GraphSolution`
        with which to identify the :class:`BranchEventSolution` by
        :type event_key: `int`
        """
        event = solution.events[event_key]
        post_events = copy(event.post_events)
        for post_event in post_events:
            post_event.previous_events.remove(event)
            event.post_events.remove(post_event)
        for graph_sol in combination:
            for end_event in graph_sol.end_events.values():
                end_event.post_events = post_events
                end_event.add_to_post_events()
            for start_event in graph_sol.start_events.values():
                start_event.add_prev_event(event)
                start_event.add_to_previous_events()
            solution.parse_event_solutions(
                list(graph_sol.events.values())
            )

    @staticmethod
    def replace_loop_event_with_sub_graph_solution(
        solution: GraphSolution,
        combination: GraphSolution,
        event_key: int
    ) -> None:
        """Method to replace a loop event in a :class:`GraphSolution` with a
        valid combination of the loop.

        :param solution: :class:`GraphSolution` containing the
        :class:`LoopEventSolution`
        :type solution: :class:`GraphSolution`
        :param loop_solution_combination: :class:`GraphSolution` that will
        replace :class:`LoopEventSolution`
        :type loop_solution_combination: :class:`GraphSolution`
        :param event_key: The event key for the :class:`LoopEventSolution` for
        lookup.
        :type event_key: `int`
        """
        event = solution.events[event_key]
        GraphSolution.handle_combine_start_events(
            loop_solution_combination=combination,
            event=event,
        )
        GraphSolution.handle_combine_end_events(
            loop_solution_combination=combination,
            event=event,
        )
        solution.remove_event(event_key)
        solution.parse_event_solutions(
            list(combination.events.values())
        )

    @staticmethod
    def handle_combine_start_events(
        loop_solution_combination: GraphSolution,
        event: LoopEventSolution,
    ) -> None:
        """Method to handle the combining of start events to the parent
        :class:`GraphSolution`

        :param loop_solution_combination: :class:`GraphSolution` of one of the
        solutions of the loop sub graph
        :type loop_solution_combination: :class:`GraphSolution`
        :param event: The :class:`LoopEventSolution` to be replaced.
        :type event: :class:`LoopEventSolution`
        """
        for start_event in (
            loop_solution_combination.start_events.values()
        ):
            start_event.previous_events = (
                event.previous_events
            )
            start_event.add_to_previous_events()
        for prev_event in event.previous_events:
            prev_event.post_events.remove(event)

    @staticmethod
    def handle_combine_end_events(
        loop_solution_combination: GraphSolution,
        event: EventSolution,
    ) -> None:
        """Method to handle the combining of end events to the parent
        :class:`GraphSolution`

        :param loop_solution_combination: :class:`GraphSolution` of one of the
        solutions of the loop sub graph
        :type loop_solution_combination: :class:`GraphSolution`
        :param event: The :class:`LoopEventSolution` to be replaced.
        :type event: :class:`LoopEventSolution`
        """
        for end_event in (
            loop_solution_combination.end_events.values()
        ):
            end_event.post_events = event.post_events
            end_event.add_to_post_events()
        for post_event in event.post_events:
            post_event.previous_events.remove(event)

    def create_audit_event_jsons(
        self,
        is_template: bool = True,
        job_name: str = "default_job_name",
        return_plot: bool = False
    ) -> tuple[list[dict], list[str], plt.Figure | None]:
        """Method to create the audit event jsons for the instance. Updates
        the event_templateid's for each :class:`EventSolution` first and
        uses a topological sort (Kahn's algotrithm) to order the events.
        Provides a timestamp to each of the events 1 second after the next
        event in the list. Returns the list of audit event jsons as well as a
        list of the audit event event_template_id's.

        :param is_template: Boolean indicating if job is a template
        job or unique ids should be provided for events and the job,
        defaults to `True`
        :type is_template: `bool`, optional
        :param job_name: The job definition name, defaults to
        "default_job_name"
        :type job_name: `str`, optional
        :param return_plot: Boolean indicating if a figure object of the
        topologically sorted graph should be returned or not, defaults to
        `False`
        :type return_plot: `bool`, optional
        :return: Returns a tuple of:
        * a list of the audit event jsons
        * a list of the event template ids
        * A figure object of topologically sorted graph or `None`
        :rtype: `tuple`[`list`[`dict`], `list`[`str`], :class:`plt.Figure` |
        `None`]
        """
        self.update_events_event_template_id(is_template)
        ordered_events = self.get_topologically_sorted_event_sequence(
            self.events.values()
        )
        (
            audit_event_sequence,
            audit_event_template_ids
        ) = self.get_audit_event_lists(
            events=ordered_events,
            is_template=is_template,
            job_name=job_name
        )
        fig = None
        if return_plot:
            fig = self.get_sequence_plot(
                ordered_events
            )

        return audit_event_sequence, audit_event_template_ids, fig

    def update_events_event_template_id(
        self,
        is_template=True
    ) -> None:
        """Method to update the event_template_id's of the
        :class:`EventSolution` instances with the events dictionary. Uses the
        event_key as the value.

        :param is_template: Boolean indicating if the job is a template job or
        not, defaults to `True`
        :type is_template: `bool`, optional
        """
        for event_key, event in self.events.items():
            event.event_template_id = (
                event_key if is_template else str(uuid.uuid4())
            )

    @staticmethod
    def get_topologically_sorted_event_sequence(
        events: Iterable[EventSolution]
    ) -> list[EventSolution]:
        """Takes an iterable of :class:`EventSolution` and topologically sorts
        them based on the Directed Acyclic Graph (DAG) that they represent

        :param events: Iterable of the :class:`EventSolution`'s to sort
        :type events: :class:`Iterable`[:class:`EventSolution`]
        :return: Returns a list of the :class:`EventSolution`'s sorted
        topologically
        :rtype: `list`[:class:`EventSolution`]
        """
        nx_graph = GraphSolution.create_networkx_graph_from_nodes(
            nodes=events,
            link_func=lambda x: x.get_post_event_edge_tuples()
        )
        ordered_events = list(nx.topological_sort(nx_graph))
        return ordered_events

    @staticmethod
    def create_networkx_graph_from_nodes(
        nodes: Iterable[object],
        link_func: Callable
    ) -> nx.DiGraph:
        """Method to create a networkx Directed Graph from an :class:`Iterable`
        of arbitrary :class:`object`'s. Uses an input function to create the
        links between nodes

        :param nodes: An :class:`Iterable` of :class:`objects` that will be
        used as nodes
        :type nodes: :class:`Iterable`[:class:`object`]
        :param link_func: Function to call to link nodes
        :type link_func: :class:`Callable`
        :return: Returns a networkx :class:`DiGraph`
        :rtype: :class:`nx.DiGraph`
        """
        edges = GraphSolution.create_graph_edge_list(
            nodes=nodes,
            link_func=link_func
        )
        nx_graph = nx.from_edgelist(edges, create_using=nx.DiGraph)
        return nx_graph

    @staticmethod
    def create_graph_edge_list(
        nodes: Iterable[object],
        link_func: Callable
    ) -> list:
        """Creates a list of edges from an :class:`Iterable` of nodes

        :param nodes: :class:`Iterable` of nodes to link
        :type nodes: :class:`Iterable`[:class:`object`]
        :param link_func: Function to call on the :class:`object`'s  to link
        nodes
        :type link_func: :class:`Callable`
        :return: Returns a list of edges
        :rtype: `list`
        """
        edges = []
        for node in nodes:
            edges.extend(link_func(node))
        return edges

    @staticmethod
    def get_audit_event_lists(
        events: Iterable[EventSolution],
        is_template: bool = True,
        job_name: str = "default_job_name"
    ) -> tuple[list[dict], list[str]]:
        """Method to generate a sequence of audit event jsons from a sequence
        of :class:`EventSolution` along with a timestamp that is 1 second
        after the previous event in the sequence. Also generates a list of the
        unique eventId templates.

        :param events: Iterable of :class:`EventSolution`
        :type events: :class:`Iterable`[:class:`EventSolution`]
        :param is_template: Boolean indicating if job is a template
        job or unique ids should be provided for events and the job,
        defaults to `True`
        :type is_template: `bool`, optional
        :param job_name: The job definition name, defaults to
        "default_job_name"
        :type job_name: `str`, optional
        :return: Returns a tuple with the first entry the list of audit event
        jsons and the second entry the list of unique eventId templates
        :rtype: `tuple`[`list`[`dict`], `list`[`str`]]
        """
        audit_event_sequence = []
        audit_event_template_ids = []
        # set job id depending on template or not
        job_id = "jobID" if is_template else str(uuid.uuid4())
        # get current time
        event_time = datetime.datetime.now()
        for event in events:
            audit_event_sequence.append(
                event.get_audit_event_json(
                    job_id=job_id,
                    time_stamp=event_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    job_name=job_name
                )
            )
            audit_event_template_ids.append(event.event_template_id)
            # update time to 1 second after previous event
            event_time += datetime.timedelta(seconds=1)

        return audit_event_sequence, audit_event_template_ids

    @staticmethod
    def get_sequence_plot(
        ordered_events: Iterable[EventSolution]
    ) -> plt.Figure:
        """Method to obtain a sequence plot from an :class:`Iterable` of
        :class:`EventSolution`

        :param ordered_events: The :class:`EventSolution`'s to create the plot
        for.
        :type ordered_events: :class:`Iterable`[:class:`EventSolution`]
        :return: Figure object of the plot
        :rtype: :class:`plt.Figure`
        """
        GraphSolution.update_event_type_counts(ordered_events)
        nx_graph = GraphSolution.create_networkx_graph_from_nodes(
            nodes=ordered_events,
            link_func=lambda x: [
                tuple(str(node) for node in node_link)
                for node_link in x.get_post_event_edge_tuples()
            ]
        )
        fig = GraphSolution.get_graphviz_plot(nx_graph)
        return fig

    @staticmethod
    def update_event_type_counts(events: Iterable[EventSolution]) -> None:
        """Method to update the event type counts for an :class:`Iterable` of
        :class:`EventSolution`'s

        :param events: Iterable of :class:`EventSolution` to update counts for.
        :type events: Iterable[EventSolution]
        """
        event_type_count = {}
        for event in events:
            event_type = event.meta_data["EventType"]
            if event_type in event_type_count:
                event_type_count[event_type] += 1
            else:
                event_type_count[event_type] = 1
            event.count = event_type_count[event_type]

    @staticmethod
    def get_graphviz_plot(
        nx_graph: nx.DiGraph
    ) -> plt.Figure:
        """Creates a :class:`plt.Figure` object containing the plot of the
        input graph

        :param nx_graph: the networkx Directed Graph to plot
        :type nx_graph: :class:`nx.DiGraph`
        :return: Returns a :class:`plt.Figure` objects containing the plot
        :rtype: :class:`plt.Figure`
        """
        pos = nx.nx_agraph.graphviz_layout(nx_graph, prog="dot")
        fig, axis = plt.subplots()
        nx.draw(
            nx_graph,
            pos,
            ax=axis,
            with_labels=True,
            arrows=True,
            node_size=1000,
            font_size=16
        )
        return fig

    def update_control_event_counts(self) -> None:
        """Method to update the counts on provider control events
        """
        for event in self.events.values():
            dynamic_controls = GraphSolution.filter_user_dynamic_controls(
                event
            )
            if not dynamic_controls:
                continue
            self.count_dynamic_controls(
                event=event,
                dynamic_controls=dynamic_controls
            )

    @staticmethod
    def filter_user_dynamic_controls(
        event: EventSolution
    ) -> dict[str, DynamicControl]:
        """Method to filter out user dynamic controls from the input
        :class:`EventSolution`'s `dynamic_control_events` attribute

        :param event: Input :class:`EventSolution`
        :type event: :class:`EventSolution`
        :return: Returns a filtered dict with only provider dynamic controls
        :rtype: `dict`[`str`, :class:`DynamicControl`]
        """
        return {
            name: dynamic_control
            for name, dynamic_control
            in event.dynamic_control_events.items()
            if dynamic_control.provider == event.event_id_tuple
        }

    @staticmethod
    def count_dynamic_controls(
        event: EventSolution,
        dynamic_controls: dict[str, DynamicControl],
        seen_events: set = None
    ) -> None:
        """Method to count the dynamic controls of a provider event.
        Recursively checks all paths and finds the required control events and
        updates

        :param event: The input :class:`EventSolution`
        :type event: :class:`EventSolution`
        :param dynamic_controls: Dictionary of :class:`DynamicControl`'s to
        search for and update
        :type dynamic_controls: `dict`[`str`, :class:`DynamicControl`]
        :param seen_events: `set` of events whose forward paths have already
        been traversed, defaults to `None`
        :type seen_events: `set`, optional
        """
        if not seen_events:
            seen_events = set()
        if not dynamic_controls:
            return
        for post_event in event.post_events:
            if post_event in seen_events:
                continue
            seen_events.add(post_event)
            for dynamic_control in dynamic_controls.values():
                dynamic_control.handle_update(post_event=post_event)
            GraphSolution.count_dynamic_controls(
                event=post_event,
                dynamic_controls=dynamic_controls,
                seen_events=seen_events
            )

    @staticmethod
    def get_graph_solutions_updated_control_counts(
        graph_solutions: Iterable[GraphSolution]
    ) -> None:
        """Method to update the control counts for an :class:`Iterable` of
        :class:`GraphSolution`'s

        :param graph_solutions: :class:`Iterable` of :class:`GraphSolution`'s
        :type graph_solutions: :class:`Iterable`[:class:`GraphSolution`]
        """
        # count all dynamic controls
        for graph_sol in graph_solutions:
            graph_sol.update_control_event_counts()


def get_audit_event_jsons_and_templates(
    graph_solutions: list[GraphSolution],
    is_template: bool = True,
    job_name: str = "default_job_name",
    return_plots=False
) -> list[tuple[list[dict], list[str], plt.Figure | None]]:
    """Function create a list of audit event sequence and audit eventId
    template pairs for a list of :class:`GraphSolution`'s

    :param graph_solutions: List of :class:`GraphSolution`'s
    :type graph_solutions: `list`[:class:`GraphSolution`]
    :param is_template: Boolean indicating if the jobs are template
    jobs or unique ids should be provided for events and the jobs,
    defaults to `True`
    :type is_template: `bool`, optional
    :param job_name: The job definition name, defaults to
    "default_job_name"
    :type job_name: `str`, optional
    :param return_plot: Boolean indicating if figure objects of the
    topologically sorted graphs should be returned or not, defaults to
    `False`
    :type return_plot: `bool`, optional
    :return: Returns the list of audit event sequence and audit eventId
    template pairs
    :rtype: `list`[`tuple`[`list`[`dict`], `list`[`str`],
    :class:`plt.Figure` | `None`]]
    """
    return [
        graph_solution.create_audit_event_jsons(
            is_template=is_template,
            job_name=job_name,
            return_plot=return_plots
        )
        for graph_solution in graph_solutions
    ]


def get_categorised_audit_event_jsons(
    categorised_graph_solutions: dict[str, tuple[list[GraphSolution], bool]],
) -> dict[str, tuple[list[tuple[list[dict], list[str]]], bool]]:
    """Method to get categorised audit event jsons from a dictionary of a list
    of `:class:GraphSolution`'s and valid/invalid boolean pair

    :param categorised_graph_solutions: Dictionary with key as category and
    values a `tuple` with first entry a list of the :class:`GraphSolution`
    instances in that category and second entry a boolean indicating whether
    the category holds valid or invalid :class:`GraphSolution` sequences,
    respectively.
    :type categorised_graph_solutions: `dict`[`str`,
    `tuple`[`list`[:class:`GraphSolution`], `bool`]]
    :return: Returns a dictionary with key as category and
    values a `tuple` with first entry a list of `tuple`'s with first entry the
    list of audit event jsons and second entry a list of the audit event ids.
    The second entry in the highest level tuple is a boolean indicating whether
    the category holds valid or invalid :class:`GraphSolution` sequences,
    respectively.
    :rtype: `dict`[`str`, `tuple`[`list`[`tuple`[`list`[`dict`],
    `list`[`str`]]], `bool`]]
    """
    return {
        category: (get_audit_event_jsons_and_templates(
            graph_sol_valid_bool_pair[0]
        ), graph_sol_valid_bool_pair[1])
        for category, graph_sol_valid_bool_pair
        in categorised_graph_solutions.items()
    }


class DynamicControl:
    """Class to hold dynamic control data

    :param control_type: The type of control either LOOPCOUNT or BRANCHCOUNT
    :type control_type: `str`
    :param name: The name of the dynamic control
    :type name: `str`
    :param provider: The provider tuple identifying the event and its
    occurence id
    :type provider: `tuple`[`str`, `int`]
    :param user: The user tuple identifying the event and its
    occurence id
    :type user: `tuple`[`str`, `int`]
    """
    def __init__(
        self,
        control_type: str,
        name: str,
        provider: tuple[str, int],
        user: tuple[str, int]
    ) -> None:
        """Constructor method
        """
        self.control_type = control_type
        self.name = name
        self.provider = provider
        self.user = user
        self.count = 0

    @property
    def count(self) -> int:
        """Property `count` getter for the count

        :return: Returns the count
        :rtype: `int`
        """
        return self._count

    @count.setter
    def count(self, update_val: int) -> None:
        """Property `count` setter for the count

        :param update_val: The value with which to update the property
        :type update_val: `int`
        """
        self._count = update_val

    def update_count(self) -> None:
        """Method to update the count by 1
        """
        self.count += 1

    def handle_update(
        self,
        post_event: EventSolution
    ) -> None:
        """Method to handle and update for a given
        :class:`EventSolution`

        :param post_event: The :class:`EventSolution` with which to update the
        count
        :type post_event: :class:`EventSolution`
        """
        if self.control_type == "LOOPCOUNT":
            self.handle_loop_update(post_event)
        elif self.control_type == "BRANCHCOUNT":
            self.handle_branch_update(post_event)

    def handle_loop_update(
        self,
        post_event: EventSolution
    ) -> None:
        """Method to handle and update for a loop for a given
        :class:`EventSolution`

        :param post_event: The :class:`EventSolution` with which to update the
        count
        :type post_event: :class:`EventSolution`
        """
        if self.user == post_event.event_id_tuple:
            self.update_count()

    def handle_branch_update(
        self,
        post_event: EventSolution
    ) -> None:
        """Method to handle and update for a branch for a given
        :class:`EventSolution`

        :param post_event: The :class:`EventSolution` with which to update the
        count
        :type post_event: :class:`EventSolution`
        """
        for prev_event in post_event.previous_events:
            if self.user == prev_event.event_id_tuple:
                self.update_count()

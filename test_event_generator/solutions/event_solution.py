# pylint: disable=R0904
# pylint: disable=R0902
# pylint: disable=C0302
"""
Classes and methods to process and combine solutions
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self, Optional, TYPE_CHECKING
from copy import copy
from itertools import product, combinations_with_replacement
import random

if TYPE_CHECKING:
    from .graph_solution import GraphSolution


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
    :param event_id_tuple: Tuple containing the EventType and occurenceId of
    the event, defaults to `None`
    :type event_id_tuple: :class:`Optional`[`tuple`[`str`, `int`]], optional
    :param is_kill: Boolean indicating if the Event is a kill point,
    defaults to `False`
    :type is_kill: `bool`, optional
    """
    def __init__(
        self,
        is_branch: bool = False,
        is_break_point: bool = False,
        meta_data: Optional[dict] = None,
        event_id_tuple: Optional[tuple[str, int]] = None,
        is_kill: bool = False,
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
        self.dynamic_control_events: dict[str, "DynamicControl"] = {}
        self.event_template_id: str = ""
        _ = kwargs
        self.count = 0
        self.is_kill = is_kill
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
        return len(self.post_events) == 0 and not self.is_kill

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
        if "isBreak" in meta_data:
            self.is_break_point = meta_data["isBreak"]
        if "isKill" in meta_data:
            self.is_kill = meta_data["isKill"]
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

    def __copy__(self) -> None:
        """Copy dunder method
        """
        copied_event = EventSolution(
            is_break_point=self.is_break_point,
            meta_data=self.meta_data,
            event_id_tuple=self.event_id_tuple,
            is_kill=self.is_kill
        )
        copied_event.previous_events = copy(self.previous_events)
        copied_event.post_events = copy(self.post_events)
        copied_event.dynamic_control_events = {
            name: copy(dynamic_control)
            for name, dynamic_control in self.dynamic_control_events.items()
        }
        copied_event.event_template_id = self.event_template_id
        return copied_event


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
        graph_solutions: list["GraphSolution"],
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
        self.expanded_solutions: list["GraphSolution"] = []

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
        graph_solutions: list["GraphSolution"],
        meta_data: Optional[dict] = None,
        event_id_tuple: Optional[tuple[str, int]] = None,
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
            event_id_tuple=event_id_tuple,
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
            meta_data=self.meta_data,
            event_id_tuple=self.event_id_tuple
        )
        # make sure expanded solutions are the same (in memory) as the instance
        copied_sub_graph_event_solution.expanded_solutions = (
            self.expanded_solutions
        )
        # option copy all atributes
        copied_sub_graph_event_solution.post_events = copy(self.post_events)
        copied_sub_graph_event_solution.previous_events = copy(
            self.previous_events
        )
        # copy all dynamic control objects
        copied_sub_graph_event_solution.dynamic_control_events = {
            name: copy(dynamic_control)
            for name, dynamic_control in self.dynamic_control_events.items()
        }
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
        graph_solutions: list["GraphSolution"],
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
        self.expanded_solutions.extend(
            self.expanded_solutions_from_solutions_combo(
                solutions_combos=solutions_combos
            )
        )

    @staticmethod
    def get_solutions_with_break_after_n_repititions(
        repeat: int,
        solutions_no_break: list["GraphSolution"],
        solutions_with_break: list["GraphSolution"]
    ) -> list[tuple["GraphSolution", ...]]:
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
        solutions_no_break: list["GraphSolution"],
        solutions_with_break: list["GraphSolution"]
    ) -> list[tuple["GraphSolution", ...]]:
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
        solutions_combos: list[tuple["GraphSolution", ...]]
    ) -> list["GraphSolution"]:
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
        graph_solutions: list["GraphSolution"],
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
        self.expanded_solutions.extend(solutions_combos)


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
        post_event: "EventSolution"
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
        post_event: "EventSolution"
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
        post_event: "EventSolution"
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

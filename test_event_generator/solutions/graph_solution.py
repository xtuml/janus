# pylint: disable=R0904
# pylint: disable=R0913
# pylint: disable=R0902
# pylint: disable=C0302
"""
Classes and methods to process and combine solutions
"""
from __future__ import annotations
from typing import Iterable, Callable, Optional, Generator
from copy import copy, deepcopy
from itertools import chain
import datetime
import uuid

import networkx as nx
import matplotlib.pyplot as plt

from test_event_generator.solutions.event_solution import (
    EventSolution,
    BranchEventSolution,
    LoopEventSolution,
    SubGraphEventSolution,
    DynamicControl
)


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
        self.start_events: dict[str, "EventSolution"] = {}
        self.end_events: dict[str, "EventSolution"] = {}
        self.loop_events: dict[str, "LoopEventSolution"] = {}
        self.branch_points: dict[str, "BranchEventSolution"] = {}
        self.break_points: dict[str, "EventSolution"] = {}
        self.events: dict[str, "EventSolution"] = {}
        self.event_dict_count: int = 0
        self.missing_events: list["EventSolution"] = []

    def parse_event_solutions(
        self,
        events: list["EventSolution"],
        keys: Optional[Iterable[int]] = None
    ) -> None:
        """Method to parse a list of :class:`EventSolution` into the specific
        dictionaries of the instance.

        :param events: List of :class:`EventSolution`'s to be parsed
        :type events: `list`[:class:`EventSolution`]
        """
        if keys:
            for event, key in zip(events, keys):
                self.add_event(event, key)
        else:
            for event in events:
                self.add_event(event)

    def _add_start_event(self, event: "EventSolution") -> None:
        """Private method to add an :class:`EventSolution` instance to the
        dictionary of start events using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`EventSolution` to be added
        :type event: :class:`EventSolution`
        """
        self.start_events[self.event_dict_count] = event

    def _add_end_event(self, event: "EventSolution") -> None:
        """Private method to add an :class:`EventSolution` instance to the
        dictionary of end events using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`EventSolution` to be added
        :type event: :class:`EventSolution`
        """
        self.end_events[self.event_dict_count] = event

    def _add_loop_event(self, event: "LoopEventSolution") -> None:
        """Private method to add an :class:`LoopEventSolution` instance to the
        dictionary of loop events using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`LoopEventSolution` to be added
        :type event: :class:`LoopEventSolution`
        """
        self.loop_events[self.event_dict_count] = event

    def _add_branch_point(self, event: "BranchEventSolution") -> None:
        """Private method to add an :class:`BranchEventSolution` instance to
        the dictionary of branch points using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`BranchEventSolution` to be added
        :type event: :class:`BranchEventSolution`
        """
        self.branch_points[self.event_dict_count] = event

    def _add_break_point(self, event: "EventSolution") -> None:
        """Private method to add an :class:`EventSolution` instance to the
        dictionary of break points using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`EventSolution` to be added
        :type event: :class:`EventSolution`
        """
        self.break_points[self.event_dict_count] = event

    def add_event(
        self,
        event: "EventSolution",
        key: Optional[int] = None
    ) -> None:
        """Private method to add an :class:`EventSolution` instance to the
        dictionary of events and updating the `event_dict_count` attribute by
        1 and using the new value `event_dict_count` as a key. Add the event
        to other instance dictionaries if the :class:`EventSolution` satisifes
        the criteria.

        :param event: :class:`EventSolution` to be added
        :type event: :class:`EventSolution`
        """
        if key:
            self.event_dict_count = key
        else:
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

    def add_to_missing_events(
        self,
        event_dict_key: int
    ) -> None:
        """Method to add an event to the missing events list by key

        :param event_dict_key: The key which to add the event
        :type event_dict_key: `int`
        """
        self.missing_events.append(self.events[event_dict_key])

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
            attribute: dict[str, "EventSolution"] = getattr(self, attr)
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

    def __copy__(self) -> None:
        """Copy dunder method
        """
        copied_graph = GraphSolution()
        copied_graph.start_events = copy(self.start_events)
        copied_graph.end_events = copy(self.end_events)
        copied_graph.loop_events = copy(self.loop_events)
        copied_graph.branch_points = copy(self.branch_points)
        copied_graph.break_points = copy(self.break_points)
        copied_graph.events = copy(self.events)
        copied_graph.event_dict_count = self.event_dict_count
        return copied_graph

    def __deepcopy__(self, memo) -> None:
        memo = {
            id(event): copy(event)
            for event in self.events.values()
        }
        for event in self.events.values():
            copied_event = memo[id(event)]
            if isinstance(copied_event, SubGraphEventSolution):
                copied_event.expanded_solutions = copy(
                    event.expanded_solutions
                )
            copied_event.post_events = [
                memo[id(post_event)]
                for post_event in event.post_events
            ]
            copied_event.previous_events = [
                memo[id(previous_event)]
                for previous_event in event.previous_events
            ]
        copied_graph = GraphSolution()

        copied_graph.parse_event_solutions(
            events=memo.values(),
            keys=self.events.keys()
        )
        return copied_graph

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
        chained_sub_graph_event_solutions = chain(
            self.loop_events.values(),
            self.branch_points.values()
        )
        # expand nested sub graph event solutions
        GraphSolution.expand_nested_sub_graph_event_solutions(
            sub_graph_event_solutions=chained_sub_graph_event_solutions,
            num_loops=num_loops,
            num_branches=num_branches
        )
        combined_graph_solutions = (
            self.combine_sub_graph_event_solutions_expanded_solutions()
        )
        return combined_graph_solutions

    @staticmethod
    def expand_nested_sub_graph_event_solutions(
        sub_graph_event_solutions: Iterable[SubGraphEventSolution],
        num_loops: int,
        num_branches: int
    ) -> None:
        """Method to expand :class:`SubGraphEventSolution`'s

        :param sub_graph_event_solutions: An iterable of
        :class:`SubGraphEventSolution`'s to expand
        :type sub_graph_event_solutions:
        :class:`Iterable`[:class:`SubGraphEventSolution`]
        :param num_loops: The number of loops with which to expand
        :type num_loops: `int`
        :param num_branches: The number of branches to expand
        :type num_branches: `int`
        """
        for event in sub_graph_event_solutions:
            GraphSolution.expand_nested_subgraph_event_solution(
                event=event,
                num_loops=num_loops,
                num_branches=num_branches
            )
            num_expansion = (
                num_branches if isinstance(event, BranchEventSolution)
                else num_loops
            )
            event.expand(num_expansion)

    def combine_sub_graph_event_solutions_expanded_solutions(
        self
    ) -> list[GraphSolution]:
        """Method to get all combined :class:`GraphSolution`'s from a list of
        :class:`GraphSolution`'s

        :return: Returns a list of fully expanded :class:`GraphSolution`'s
        :rtype: `list`[:class:`GraphSolution`]
        """
        combined_graph_solutions = [self]
        # loop through all loop event solutions
        # 1. expand all nested subgraphs and combine them together
        # 2. expand the loop itself
        # 3. combine the expanded and precombined subgraphs with the instance
        # solution
        for event_key, event in self.loop_events.items():
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
        event: "SubGraphEventSolution",
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
    def expand_nested_subgraph_event_solution(
        event: "SubGraphEventSolution",
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
        event: "LoopEventSolution",
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
        loop_solution_combination: "GraphSolution",
        event: "EventSolution",
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
        start_time: Optional[datetime.datetime] = None,
        job_id: Optional[str] = None,
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
        :param start_time: The :class:`datetime.datetime` at which to start
        the audit events, defaults to `None`
        :type start_time: :class:`Optional`[:class:`datetime.datetime`],
        optional
        :param job_id: The job id to give to the audit events, defaults to
        "jobID"
        :type job_id: `str`, optional
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
            job_name=job_name,
            start_time=start_time,
            job_id=job_id,
            missing_events=self.missing_events
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
        events: Iterable["EventSolution"]
    ) -> list["EventSolution"]:
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
        events: Iterable["EventSolution"],
        is_template: bool = True,
        job_name: str = "default_job_name",
        job_id: Optional[str] = None,
        start_time: Optional[datetime.datetime] = None,
        missing_events: list["EventSolution"] = None
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
        :param job_id: The job id to give to the audit events, defaults to
        "jobID"
        :type job_id: `str`, optional
        :param start_time: The :class:`datetime.datetime` at which to start
        the audit events, defaults to `None`
        :type start_time: :class:`Optional`[:class:`datetime.datetime`],
        :return: Returns a tuple with the first entry the list of audit event
        jsons and the second entry the list of unique eventId templates
        :rtype: `tuple`[`list`[`dict`], `list`[`str`]]
        """
        if missing_events is None:
            missing_events = []
        audit_event_sequence = []
        audit_event_template_ids = []
        # set job id depending on template or not
        if not job_id and not is_template:
            job_id = str(uuid.uuid4())
        elif not job_id and is_template:
            job_id = "jobID"
        # get current time
        if start_time:
            event_time = start_time
        else:
            event_time = datetime.datetime.now()
        for event in events:
            if event not in missing_events:
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
        ordered_events: Iterable["EventSolution"]
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
    def update_event_type_counts(events: Iterable["EventSolution"]) -> None:
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
        event: "EventSolution"
    ) -> dict[str, "DynamicControl"]:
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
        event: "EventSolution",
        dynamic_controls: dict[str, "DynamicControl"],
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
) -> Generator[tuple[list[dict], list[str], plt.Figure | None]]:
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
    :rtype: :class:`Generator`[`tuple`[`list`[`dict`], `list`[`str`],
    :class:`plt.Figure` | `None`]]
    """
    for graph_solution in graph_solutions:
        yield graph_solution.create_audit_event_jsons(
            is_template=is_template,
            job_name=job_name,
            return_plot=return_plots
        )


def get_categorised_audit_event_jsons(
    categorised_graph_solutions: dict[
        str,
        tuple[Iterable[GraphSolution], bool]
    ],
    return_plots: bool = False
) -> dict[str, tuple[Generator[tuple[list[dict], list[str]]], bool]]:
    """Method to get categorised audit event jsons from a dictionary of a list
    of `:class:GraphSolution`'s and valid/invalid boolean pair

    :param categorised_graph_solutions: Dictionary with key as category and
    values a `tuple` with first entry a list of the :class:`GraphSolution`
    instances in that category and second entry a boolean indicating whether
    the category holds valid or invalid :class:`GraphSolution` sequences,
    respectively.
    :type categorised_graph_solutions: `dict`[`str`,
    `tuple`[:class:`Iterable`[:class:`GraphSolution`], `bool`]]
    :return: Returns a dictionary with key as category and
    values a `tuple` with first entry a Generator of `tuple`'s with first
    entry the
    list of audit event jsons and second entry a list of the audit event ids.
    The second entry in the highest level tuple is a boolean indicating whether
    the category holds valid or invalid :class:`GraphSolution` sequences,
    respectively.
    :rtype: `dict`[`str`, `tuple`[:class:`Generator`[`tuple`[`list`[`dict`],
    `list`[`str`]]], `bool`]]
    """
    return {
        category: (get_audit_event_jsons_and_templates(
            graph_sol_valid_bool_pair[0],
            return_plots=return_plots
        ), graph_sol_valid_bool_pair[1])
        for category, graph_sol_valid_bool_pair
        in categorised_graph_solutions.items()
    }

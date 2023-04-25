"""
Classes and methods to process and combine solutions
"""
from __future__ import annotations
from typing import Self, Optional
from copy import copy, deepcopy
from itertools import product
import random


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
        **kwargs
    ) -> None:
        """Constructor method
        """
        self.is_branch = is_branch
        self.is_break_point = is_break_point
        self.meta_data = meta_data
        self.previous_events: list[EventSolution] = []
        self.post_events: list[EventSolution] = []
        self.kwargs = kwargs

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
    def is_end(self):
        """Property defining if the instance is an end event.

        :return: Boolean indicating if the instance is an end event.
        :rtype: `bool`
        """
        return len(self.post_events) == 0


class LoopEventSolution(EventSolution):
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
            meta_data=meta_data,
            **kwargs
        )
        self.graph_solutions = graph_solutions
        self.expanded_solutions: Optional[list[GraphSolution]] = None

    def expand_loops(self, loop_count: int) -> None:
        """Method to expand the loop

        :param loop_count: The number of iterations of the loop
        :type loop_count: `int`
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
                solutions_no_break, repeat=loop_count
            )
        )
        # setup list for all combinations of solutions with a break.
        # Initialised with the possible solutions with a break
        solutions_with_break_combos = self.solution_combinations_with_break(
            loop_count=loop_count,
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
        self.branch_points: dict[str, EventSolution] = {}
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

    def _add_branch_point(self, event: EventSolution) -> None:
        """Private method to add an :class:`EventSolution` instance to the
        dictionary of branch points using the `event_dict_count` of the
        instance as a key.

        :param event: :class:`EventSolution` to be added
        :type event: :class:`EventSolution`
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
        if event.is_branch:
            self._add_branch_point(event)
        if event.is_break_point:
            self._add_break_point(event)
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

    def expand_loop_events(self, num_loops: int) -> None:
        """Method to expand all the loop events contained in the instance.

        :param num_loops: The number of loops that should occur for each loop
        :type num_loops: `int`
        """
        for event in self.loop_events.values():
            event.expand_loops(num_loops)

    def expand_branch_events(self, num_branches: int) -> None:
        """Method to expand all the branch events contained in the instance.

        :param num_branches: The number of branches that should extend from
        the event.
        :type num_branches: `int`
        """
        branched_events = []
        for event in self.branch_points.values():
            branched_events.extend(event.extend_branches(num_branches))
        self.parse_event_solutions(branched_events)

    def expand_graph_solutions(
        self,
        num_branches: int,
        num_loops: int
    ) -> None:
        """Method to expand all the branch and loop events of the instance
        whilst also expanding any nested loops within the loop events.

        :param num_branches: The number of branches that should extend from
        branch events
        :type num_branches: `int`
        :param num_loops: The number of iterations for the loops in loop
        events.
        :type num_loops: `int`
        """
        for event in self.loop_events.values():
            for solution in event.graph_solutions:
                solution.expand_graph_solutions(
                    num_branches,
                    num_loops
                )
        self.expand_branch_events(num_branches)
        self.expand_loop_events(num_loops)

    def combine_nested_loop_solutions(
        self
    ) -> list[GraphSolution]:
        """Method to get all the expanded combinations of loop events and
        their nested loops (can go arbitrarily deep).

        :return: Returns a list of all the possible valid sequences of Events
        :rtype: `list`[:class:`GraphSolution`]
        """
        combined_graph_solutions = [self]
        for event_key, event in self.loop_events.items():
            all_event_combined_solutions = self.loop_event_combined_solutions(
                expanded_solutions=event.expanded_solutions
            )
            combined_graph_solutions_temp: list[GraphSolution] = []
            for solution in combined_graph_solutions:
                for loop_solution_combination in all_event_combined_solutions:
                    solution_copy = deepcopy(solution)
                    event_copy = solution_copy.events[event_key]
                    loop_solution_combination_copy = deepcopy(
                        loop_solution_combination
                    )
                    self.replace_loop_event_with_sub_graph_solution(
                        solution=solution_copy,
                        loop_solution_combination=(
                            loop_solution_combination_copy
                        ),
                        event=event_copy,
                        event_key=event_key
                    )
                    combined_graph_solutions_temp.append(solution_copy)
            combined_graph_solutions = combined_graph_solutions_temp
        return combined_graph_solutions

    @staticmethod
    def loop_event_combined_solutions(
        expanded_solutions: list[GraphSolution]
    ) -> list[GraphSolution]:
        """Method to obtain all the combined valid event sequences from a list
        of expanded (all nested loop and branch events have been expanded)
        :class:`GraphSolution`'s

        :param expanded_solutions: List of expanded (nested loop + branch
        events expanded) :class:`GraphSolution`'s
        :type expanded_solutions: `list`[:class:`GraphSolution`]
        :return: Returns a list of all the valid Event sequences
        :rtype: `list`[:class:`GraphSolution`]
        """
        all_event_combined_solutions: list[GraphSolution] = []
        for graph_solution in expanded_solutions:
            combined_solutions = (
                graph_solution.combine_nested_loop_solutions()
            )
            all_event_combined_solutions.extend(
                combined_solutions
            )
        return all_event_combined_solutions

    @staticmethod
    def replace_loop_event_with_sub_graph_solution(
        solution: GraphSolution,
        loop_solution_combination: GraphSolution,
        event: LoopEventSolution,
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
        :param event: The :class:`LoopEventSolution` that is to be replaced.
        :type event: :class:`LoopEventSolution`
        :param event_key: The event key for the :class:`LoopEventSolution` for
        lookup.
        :type event_key: `int`
        """
        GraphSolution.handle_combine_start_events(
            loop_solution_combination=loop_solution_combination,
            event=event,
        )
        GraphSolution.handle_combine_end_events(
            loop_solution_combination=loop_solution_combination,
            event=event,
        )
        solution.remove_event(event_key)
        solution.parse_event_solutions(
            list(loop_solution_combination.events.values())
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

# pylint: disable=R0904
# pylint: disable=R0913
"""
Graph class to hold model info
"""
from typing import Type, Union, Iterable, Optional
from copy import copy

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar
from flatdict import FlatterDict
import numpy as np
from test_event_generator.core.edge import Edge
from test_event_generator.core.group import ORGroup, XORGroup, ANDGroup, Group
from test_event_generator.core.event import Event, LoopEvent, BranchEvent
from test_event_generator.utils.utils import solve_model_core
from test_event_generator.solutions import (
    EventSolution,
    LoopEventSolution,
    GraphSolution,
    BranchEventSolution
)


class Graph:
    """Graph class that builds and solves an ortools model based on an Event
    graph. Solutions are converted to solutions for Events:
    * 1 signifies event occurred
    * 0 signifies event didn't occur
    """
    def __init__(
        self
    ) -> None:
        """Constructor method
        """
        self.model = CpModel()
        self.edges: dict[str, Edge] = {}
        self.groups: dict[tuple, Group] = {}
        self.events: dict[str, Union[Event, LoopEvent]] = {}
        self.solutions = None

    def add_edges(self, edge_uids: list[str]) -> None:
        """Method to add :class:`Edge` instances to instance based on the uids
        for the edges. Places the newly create :class:`Edge` instances in a
        dictionary attribute.

        :param edge_uids: List of edge uids
        :type edge_uids: `list`[`str`]
        """
        for edge_uid in edge_uids:
            self.edges[edge_uid] = Edge(
                model=self.model,
                uid=edge_uid
            )

    @staticmethod
    def extract_edges(graph_def: dict) -> list[str]:
        """Static method that extracts a list of Edges from a graph definition
        standard input.

        :param graph_def: A dictionary of the standardised input for a graph
        definition.
        :type graph_def: `dict`
        :return: The list of extracted edge uids
        :rtype: `list`[`str`]
        """
        edges_duplicates = Graph.get_duplicates(graph_def)
        edges = Graph.unique_edges(edges_duplicates)
        return edges

    @staticmethod
    def get_duplicates(graph_def: dict) -> list[str]:
        """Static method to extract and return a list of duplicate edges from
        the flattened graph definition standard input dictionary.

        :param graph_def: A dictionary of the standardised input for a graph
        definition.
        :type graph_def: `dict`
        :return: The list of extracted edge uids along with duplicates.
        :rtype: `list`[`str`]
        """
        graph_def_flat = FlatterDict(graph_def)
        edges_duplicates = [
            value for key, value in graph_def_flat.items()
            if all(
                restricted_key not in key and value
                for restricted_key in [
                    "type", "loop_graph", "is_loop",
                    "meta_data", "branch_graph",
                    "dynamic_control_events"
                ]
            )
        ]
        return edges_duplicates

    @staticmethod
    def unique_edges(edges_duplicates: list[str]) -> list[str]:
        """Static method to find unique edge uids from a list of edge uids in
        which each edge uid should always have two occurences.

        :param edges_duplicates: List of edge uids
        :type edges_duplicates: `list`[`str`]
        :raises RuntimeError: Raises error when there is at least one edge uid
        that appears more than twice in the list and there is at least one
        edge uid that appears only once in the list.
        :raises RuntimeError: Raises error when there is at least one edge uid
        that appears more than twice in the list.
        :raises RuntimeError: Raises error when there is at least one edge uid
        that appears only once in the list.
        :return: Returns a list of the unique edge uids in the input list.
        :rtype: `list`[`str`]
        """
        edges, counts = np.unique(edges_duplicates, return_counts=True)
        too_many = len(counts[counts > 2])
        too_few = len(counts[counts == 1])
        if too_many and too_few:
            raise RuntimeError(
                "Some of the edges have more than 2 occurences"
                " and some have less than 2 occurences."
            )
        if too_many:
            raise RuntimeError(
                "Some of the edges have more than 2 ocurrences"
            )
        if too_few:
            raise RuntimeError(
                "Some of the edges have less than 2 ocurrences"
            )
        return edges.tolist()

    def parse_graph_def(self, graph_def: dict) -> None:
        """Method to parse a graph definition standard input and create and
        hold an ILP model in the instance.

        Will set loop events if they are present in the graph definition.

        :param graph_def: The standard graph definition input.
        :type graph_def: `dict`
        """
        # get edges from graph definition and add them to instance
        edges = self.extract_edges(graph_def)
        self.add_edges(edges)
        # loop through events in graph def and recursively set groups
        # add starting events to list
        starting_event_out_group_variables = []
        for event_uid, event_def in graph_def.items():
            # create group in
            group_in = self.create_sub_groups(
                group_def=event_def["group_in"],
                key_tuple=(event_uid, "in"),
                is_into_event=True
            )
            # create group out
            group_out = self.create_sub_groups(
                group_def=event_def["group_out"],
                key_tuple=(event_uid, "out"),
                is_into_event=False
            )
            # create event
            event = self.create_event(
                model=self.model,
                uid=event_uid,
                group_in=group_in,
                group_out=group_out,
                meta_data=(
                    event_def["meta_data"] if "meta_data" in event_def
                    else None
                ),
                loop_graph=(
                    event_def["loop_graph"] if "loop_graph" in event_def
                    else None
                ),
                branch_graph=(
                    event_def["branch_graph"] if "branch_graph" in event_def
                    else None
                )
            )
            self.events[event_uid] = event
            # add starting event group out variable to list
            if event.is_start:
                starting_event_out_group_variables.append(group_out.variable)
        # set the starting point constraint
        self.set_start_point_constraint(
            model=self.model,
            group_variables=starting_event_out_group_variables
        )

    @staticmethod
    def create_event(
        model: CpModel,
        uid: Optional[str] = None,
        group_in: Optional[Group] = None,
        group_out: Optional[Group] = None,
        meta_data: Optional[dict] = None,
        loop_graph: Optional[dict] = None,
        branch_graph: Optional[dict] = None
    ) -> LoopEvent | Event | BranchEvent:
        """Create :class:`Event` from :class:`CpModel`
        instance, an instance of :class:`Group` (or `None`) for the group into
        the event, an instance of :class:`Group` (or `None`) for the group
        out of the event, meta_data dictionary if present, loop_graph
        defintion dictionary if present and branch_graph definition dictionary
        if present.

        :param model: CP-SAT model
        :type model: :class:`CpModel`
        :param uid: Unique id for the :class:`Event` to be created
        :type uid: `str`
        :param group_in: :class:`Group` entering the :class:`Event`, defaults
        to `None`
        :type group_in: :class:`Optional`[:class:`Group`], optional
        :param group_out: :class:`Group` exiting the :class:`Event`, defaults
        to `None`
        :type group_out: :class:`Optional`[:class:`Group`], optional
        :param meta_data: Dictionary containing arbitrary meta data, defaults
        to `None`
        :type meta_data: :class:`Optional`[`dict`], optional
        :param loop_graph: Standardise graph definiton for a loop event,
        defaults to `None`
        :type loop_graph: :class:`Optional`[`dict`], optional
        :return: Returns the instance of the created :class:`Event`,
        :class:`LoopEvent` or :class:`BranchEvent`
        :rtype: :class:`LoopEvent` | :class:`Event` | :class:`BranchEvent`
        """

        kwaargs = {
            "model": model,
            "uid": uid,
            "in_group": group_in,
            "out_group": group_out,
        }
        # check for meta data
        if meta_data is None:
            meta_data = {}
        # add meta data
        kwaargs["meta_data"] = meta_data
        # check if loop event
        if loop_graph:
            kwaargs["sub_graph"] = Graph()
            event = LoopEvent(**kwaargs)
            # set the loop event sub graph
            event.set_graph_with_graph_def(loop_graph)
        elif branch_graph:
            kwaargs["sub_graph"] = Graph()
            event = BranchEvent(**kwaargs)
            # set the branch event sub graph
            event.set_graph_with_graph_def(branch_graph)
        else:
            event = Event(**kwaargs)
        return event

    @staticmethod
    def set_start_point_constraint(
        model: CpModel,
        group_variables: Iterable[IntVar]
    ) -> None:
        """Method to set the start point constraints of a :class:`CpModel`
        from an iterable of :class:`IntVar`.

        :param model: CP-SAT model
        :type model: :class:`CpModel`
        :param group_variables: :class:`IntVar` variables from out
        :class:`Group`'s of starting events.
        :type group_variables: :class:`Iterable`[:class:`IntVar`]
        """
        model.Add(
            sum(group_variables) > 0
        )

    def create_sub_groups(
        self,
        group_def: dict | None,
        key_tuple: tuple,
        is_into_event: bool
    ) -> ORGroup | XORGroup | ANDGroup | None:
        """Recursive method to create the parent group and its subgroups from
        the standardised group definition input.

        :param group_def: Standardised group definition input.
        :type group_def: `dict` | `None`
        :param key_tuple: A tuple containing the route through the graph
        definition to the group i.e. ("Event_A", "in", "1", "1",...,"2"),
        where the first two entries are the parent Event and the first
        ancestral group that is either "in" or "out" of the event. The numbers
        then refer to the position in a list of subsequent child groups. Acts
        as a unique identifier for the group.
        :type key_tuple: `tuple`
        :param is_into_event: Whether the group is pointing into (True) the
        Event or out of it (False).
        :type is_into_event: `bool`
        :raises RuntimeError: Raises an error if the input key_tuple has
        length less than two as there must be a parent event and one parent
        group.
        :raises RuntimeError: Raises an error if a edge uid does not appear in
        the pre-constructed edges dictionary of the instance. This will not
        occur if parsing using the method `parse_graph_def` as edge uids will
        have been added correctly to the dictionary.
        :return: Returns the :class:`Group` class created from the group
        definition. Will return `None` if pass `None` as input for `group_def`.
        :rtype: :class:`ORGroup` | :class:`XORGroup` | :class:`ANDGroup` |
        `None`.
        """
        if not group_def:
            return None
        # check that key tuple has length at least 2
        if len(key_tuple) < 2:
            raise RuntimeError(
                "Key tuple must at least have entry for parent event and the "
                "highest group"
            )
        # get group type
        group_type = group_def["type"]
        # get list of subgroups/edges
        sub_groups = group_def["sub_groups"]
        # loop over the subgroups and recursively apply create_sub_groups
        sub_group_instances = []
        for sub_group_num, sub_group in enumerate(sub_groups):
            # check if group
            if isinstance(sub_group, dict):
                sub_key_tuple = key_tuple + (str(sub_group_num),)
                sub_group_instance = self.create_sub_groups(
                    group_def=sub_group,
                    key_tuple=sub_key_tuple,
                    is_into_event=is_into_event
                )
            # must be edge
            else:
                if sub_group not in self.edges:
                    raise RuntimeError(
                        f"The edge {sub_group} is not in the list provided."
                        " Check the edge uid is correct or add it to the list."
                        " The edge is located within the input json at: \n"
                        f"{key_tuple[0]}\ngroup_{key_tuple[1]}\n"
                        "\n".join([
                            f"Sub-group list position {key}"
                            for key in key_tuple[-len(key_tuple) + 2:]
                        ])
                    )
                sub_group_instance = self.edges[sub_group]
            # add instance to sub group list
            sub_group_instances.append(sub_group_instance)
        # create the group
        group = self.select_group(group_type)(
            model=self.model,
            uid=".".join(key_tuple),
            group_variables=sub_group_instances,
            is_into_event=is_into_event
        )
        # add group to groups dictionary
        self.groups[key_tuple] = group
        return group

    @staticmethod
    def select_group(
        group_type: str
    ) -> Type[ORGroup] | Type[XORGroup] | Type[ANDGroup]:
        """Method to select the type :class:`Group` from a string input.

        :param group_type: A string that aliases the :class:`Group`.
        :type group_type: `str`
        :return: The :class:`Group` type
        :rtype: :class:`Type`[:class:`ORGroup`] |
        :class:`Type`[:class:`XORGroup`] | :class:`Type`[:class:`ANDGroup`]
        """
        match group_type:
            case "OR":
                return ORGroup
            case "XOR":
                return XORGroup
            case "AND":
                return ANDGroup
            case _:
                return ORGroup

    def solve(self):
        """Method to solve the ILP model and return solutions in terms of
        Events.
        """
        solver = CpSolver()
        # get group variables to save solutions
        variables_to_save = {
            "Group": [
                group for group_key_tuple, group in self.groups.items()
                if len(group_key_tuple) == 2
            ]
        }
        # add edges to variables to save
        variables_to_save["Edge"] = list(self.edges.values())
        # solve model
        self.solutions = solve_model_core(
            model=self.model,
            solver=solver,
            core_variables=variables_to_save
        )
        # get events solutions
        if len(self.events) == 1:
            self.solutions["Event"] = [
                {event_id: 1 for event_id in self.events}
            ]
            self.solutions["Edge"] = [{}]
        else:
            self.solutions["Event"] = self.convert_to_event_solutions(
                self.solutions["Group"]
            )
        # solve all loop event subgraphs and branch events
        self.solve_loop_events_sub_graphs(
            loop_events=self.filter_events(self.events.values())
        )

    def convert_to_event_solutions(
        self,
        solutions: list[dict[str, int]]
    ) -> list[dict[str, int]]:
        """Method to convert a set of solutions to solutions in terms of
        Events. The solution must only include group solutions for the "in"
        and "out" groups of an Event

        :param solutions: List of solutions for group events
        :type solutions: `list`[`dict`[`str`, `int`]]
        :return: Returns a list of solutions converted to event solutions
        :rtype: `list`[`dict`[`str`, `int`]]
        """
        events_solutions: list[dict[str, int]] = []
        for solution in solutions:
            events_solution = {}
            for event_id, event in self.events.items():
                in_solution, out_solution = 0, 0
                if event.in_group:
                    in_solution = solution[".".join((event_id, "in"))]
                if event.out_group:
                    out_solution = solution[".".join((event_id, "out"))]
                events_solution[event_id] = in_solution | out_solution
            events_solutions.append(events_solution)
        return events_solutions

    @staticmethod
    def solve_loop_events_sub_graphs(
        loop_events: Iterable[LoopEvent | BranchEvent]
    ) -> None:
        """Static method to solve the subgraphs of the :class:`LoopEvent`'s in
        the iterable input. This will also include :class:`BranchEvent`'s as
        well.

        :param loop_events: Iterable of :class:`LoopEvent`'s or
        :class:`BranchEvent`'s
        :type loop_events: :class:`Iterable`[:class:`LoopEvent` |
        :class:`BranchEvent`]
        :raises :class:`RuntimeError`: Raises Exception when any of the values
        in the iterable are not instance of :class:`LoopEvent`.
        """
        # check for any events not LoopEvent
        if any(not isinstance(event, LoopEvent) for event in loop_events):
            raise RuntimeError(
                "At least one of the events is not a LoopEvent."
            )
        for loop_event in loop_events:
            loop_event.solve_sub_graph()

    @staticmethod
    def filter_events(
        loop_events: Iterable[Union[Event, LoopEvent, BranchEvent]]
    ) -> list[LoopEvent | BranchEvent]:
        """Filters out anything but instances of :class:`LoopEvent` from the
        input iterable, this will include :class:`BranchEvent`'s as well

        :param loop_events: Iterable of :class:`Event`
        :type loop_events: :class:`Iterable`[:class:`Union`[:class:`Event`,
        :class:`LoopEvent`, :class:`BranchEvent`]]
        :return: Returns a list of :class:`LoopEvent`'s and/or
        :class:`BranchEvent`'s
        :rtype: `list`[:class:`LoopEvent` | :class:`BranchEvent`]
        """
        return list(filter(lambda x: isinstance(x, LoopEvent), loop_events))

    def get_all_combined_graph_solutions(
        self,
        num_loops: int,
        num_branches: int
    ) -> list[GraphSolution]:
        """Method to get all expanded and combined graph solutions from the
        given ILP solutions from given number of loops and branches

        :param num_loops: The number of loops a loop should have
        :type num_loops: `int`
        :param num_branches: The number of branches a branch should have
        :type num_branches: `int`
        :return: Returns a list of all the expanded and combined
        :class:`GraphSolution`'s
        :rtype: `list`[:class:`GraphSolution`]
        """
        # recursive create graph solutions for all nested sub graphs
        graph_solutions = self.get_nested_unexpanded_graph_solutions(
            graph_events_solutions=self.solutions["Event"],
            graph_edges_solutions=self.solutions["Edge"],
            events=self.events
        )
        # expand and combine all graph solutions
        expanded_and_combined_graph_solutions = []
        for graph_solution in graph_solutions:
            expanded_and_combined_graph_solutions.extend(
                graph_solution.combine_nested_solutions(
                    num_loops=num_loops,
                    num_branches=num_branches
                )
            )
        # update control event counts
        GraphSolution.get_graph_solutions_updated_control_counts(
            expanded_and_combined_graph_solutions
        )
        return expanded_and_combined_graph_solutions

    @staticmethod
    def get_nested_unexpanded_graph_solutions(
        graph_events_solutions: list[dict[str, int]],
        graph_edges_solutions: list[dict[str, int]],
        events: dict[str, "Event"],
    ) -> list[GraphSolution]:
        """Method to get all the nested unexpanded :class:`GraphSolution`'s
        for all the :class:`Event`'s that contain a subgraph from the ILP
        solutions provided

        :param graph_events_solutions: The list of solution values for each of
        the :class:`Event`'s for each possible solution
        :type graph_events_solutions: `list`[`dict`[`str`, `int`]]
        :param graph_edges_solutions: The list of solution values for each of
        the :class:`Edge`'s for each possible solution
        :type graph_edges_solutions: `list`[`dict`[`str`, `int`]]
        :param events: The dictionary of :class:`Event`'s
        :type events: `dict`[`str`, :class:`Event`]
        :return: Returns the list of :class:`GraphSolution`'s
        :rtype: `list`[:class:`GraphSolution`]
        """
        events_with_sub_graph_event_solutions = {
            event_uid: Graph.process_sub_graph_event_solution(
                event=event
            )
            for event_uid, event in events.items()
            if isinstance(event, (LoopEvent, BranchEvent))
        }
        graph_solutions = Graph.get_unexpanded_graph_solutions(
            graph_events_solutions=graph_events_solutions,
            graph_edges_solutions=graph_edges_solutions,
            events=events,
            events_with_sub_graph_event_solutions=(
                events_with_sub_graph_event_solutions
            )
        )
        return graph_solutions

    @staticmethod
    def process_sub_graph_event_solution(
        event: LoopEvent | BranchEvent,
    ) -> LoopEventSolution | BranchEventSolution:
        """Method to create a :class:`SubGraphEventSolution` given the type of
        :class:`Event` and the solutions of its sub graph.

        :param event: The :class:`LoopEvent` or :class:`BranchEvent`
        :type event: :class:`LoopEvent` | :class:`BranchEvent`
        :raises RuntimeError: Raises a :class:`RuntimError` if the instance is
        not a :class:`BranchEvent` or :class:`LoopEvent`
        :return: Returns the created :class:`SubGraphEventSolution`
        :rtype: :class:`LoopEventSolution` | :class:`BranchEventSolution`
        """
        if isinstance(event, BranchEvent):
            class_to_apply = BranchEventSolution
        elif isinstance(event, LoopEvent):
            class_to_apply = LoopEventSolution
        else:
            raise RuntimeError("Not instance of LoopEvent or BranchEvent")
        sub_graph = event.sub_graph
        graph_solutions = (
            Graph.get_nested_unexpanded_graph_solutions(
                graph_events_solutions=sub_graph.solutions["Event"],
                graph_edges_solutions=sub_graph.solutions["Edge"],
                events=sub_graph.events
            )
        )
        event_solution = class_to_apply(
            graph_solutions=graph_solutions,
            meta_data=event.meta_data
        )
        return event_solution

    @staticmethod
    def get_unexpanded_graph_solutions(
        graph_events_solutions: list[dict[str, int]],
        graph_edges_solutions: list[dict[str, int]],
        events: dict[str, Event],
        events_with_sub_graph_event_solutions: dict[
            str, LoopEventSolution | BranchEventSolution
        ]
    ) -> list[GraphSolution]:
        """Method to generate unexpanded graph solutions for a list of
        dictionary of event and edge solution values

        :param graph_events_solutions: A list of dictionaries that contain the
        values (0 or 1) of events for a given solution.
        :type graph_events_solutions: `list`[`dict`[`str`, `int`]]
        :param graph_edges_solutions: A list of dictionaries that contain the
        values (0 or 1) of edges for a given solution.
        :type graph_edges_solutions: `list`[`dict`[`str`, `int`]]
        :param events: Dictionary with event uid as key and a :class:`Event`
        as values
        :type events: `dict`[`str`, :class:`Event`]
        :param events_with_sub_graph_event_solutions: Dictionary containing
        event uid as key and :class:`SubGraphEventSolution`'s as values.
        :type events_with_sub_graph_event_solutions: `dict`[ `str`,
        :class:`LoopEventSolution`  |  :class:`BranchEventSolution` ]
        :return: Returns a list of the :class:`GraphSolution`'s corresponding
        to the given event and edge solution values
        :rtype: `list`[:class:`GraphSolution`]
        """
        graph_solutions: list[GraphSolution] = []
        for graph_events_solution, graph_edges_solution in zip(
            graph_events_solutions, graph_edges_solutions
        ):
            graph_solution = Graph.get_unexpanded_graph_solution(
                graph_events_solution=graph_events_solution,
                graph_edges_solution=graph_edges_solution,
                events=events,
                events_with_sub_graph_event_solutions=(
                    events_with_sub_graph_event_solutions
                )
            )
            graph_solutions.append(graph_solution)
        return graph_solutions

    @staticmethod
    def get_unexpanded_graph_solution(
        graph_events_solution: dict[str, int],
        graph_edges_solution: dict[str, int],
        events: dict[str, Event],
        events_with_sub_graph_event_solutions: dict[
            str, LoopEventSolution | BranchEventSolution
        ]
    ) -> GraphSolution:
        """Method to get the :class:`GraphSolution`'s for a solution of event
        and edge values with any :class:`SubGraphEventSolution`'s unexpanded.

        :param graph_events_solution: A dictionary that contains the
        values (0 or 1) of events for a given solution.
        :type graph_events_solution: `dict`[`str`, `int`]
        :param graph_edges_solution: A dictionary that contains the
        values (0 or 1) of edges for a given solution.
        :type graph_edges_solution: `dict`[`str`, `int`]
        :param events: Dictionary with event uid as key and a :class:`Event`
        as values
        :type events: `dict`[`str`, :class:`Event`]
        :param events_with_sub_graph_event_solutions: Dictionary containing
        event uid as key and :class:`SubGraphEventSolution`'s as values.
        :type events_with_sub_graph_event_solutions: `dict`[ `str`,
        :class:`LoopEventSolution`  |  :class:`BranchEventSolution` ]
        :return: Returns a :class:`GraphSolution`'s corresponding
        to the given event and edge solution values
        :rtype: :class:`GraphSolution`
        """
        event_solution_instances = Graph.get_event_solution_instances(
            graph_events_solution=graph_events_solution,
            events=events,
            events_with_sub_graph_event_solutions=(
                events_with_sub_graph_event_solutions
            )
        )
        Graph.update_connected_events_for_all_event_solutions(
            event_solution_instances=event_solution_instances,
            events=events,
            graph_edges_solution=graph_edges_solution
        )
        graph_solution = GraphSolution()
        graph_solution.parse_event_solutions(
            list(event_solution_instances.values())
        )
        return graph_solution

    @staticmethod
    def get_event_solution_instances(
        graph_events_solution: dict[str, int],
        events: dict[str, Event],
        events_with_sub_graph_event_solutions: dict[
            str, LoopEventSolution | BranchEventSolution
        ]
    ) -> dict[str, EventSolution | LoopEventSolution | BranchEventSolution]:
        """_summary_

        :param graph_events_solution: A dictionary that contains the
        values (0 or 1) of events for a given solution.
        :type graph_events_solution: `dict`[`str`, `int`]
        :param events: Dictionary with event uid as key and a :class:`Event`
        as values
        :type events: `dict`[`str`, :class:`Event`]
        :param events_with_sub_graph_event_solutions: Dictionary containing
        event uid as key and :class:`SubGraphEventSolution`'s as values.
        :type events_with_sub_graph_event_solutions: `dict`[ `str`,
        :class:`LoopEventSolution`  |  :class:`BranchEventSolution` ]
        :return: Returns a dictionary of the :class:`EventSolution` instances
        for the given solution
        :rtype: `dict`[`str`, :class:`EventSolution` |
        :class:`LoopEventSolution` | :class:`BranchEventSolution`]
        """
        return {
            event_uid: (
                EventSolution(
                    meta_data=events[event_uid].meta_data,
                    **events[event_uid].meta_data
                ) if event_uid not in events_with_sub_graph_event_solutions
                else copy(
                    events_with_sub_graph_event_solutions[event_uid]
                )
            )
            for event_uid, event_solution in graph_events_solution.items()
            if event_solution == 1
        }

    @staticmethod
    def update_connected_events_for_all_event_solutions(
        event_solution_instances: dict[str, EventSolution],
        events: dict[str, Event],
        graph_edges_solution: dict[str, int]
    ) -> None:
        """Method to update all the previous and post events lists for all the
        given :class:`EventSolution`'s

        :param event_solutions: Dictionary of the :class:`EventSolution`'s
        :type event_solutions: `dict`[`str`, :class:`EventSolution`]
        :param events: Dictionary (keys as uid of events) of
        :class:`Event`'s that contain the information on links to other
        :class:`Event`'s.
        :type events: `dict`[`str`, :class:`Event`]
        :param edge_solutions: Dictionary (keys uid of edges) of the solution
        values of the edges
        :type edge_solutions: `dict`[`str`, `int`]
        """
        for event_uid, event_solution in event_solution_instances.items():
            event = events[event_uid]
            Graph.update_connected_events(
                event=event,
                event_solution=event_solution,
                event_solution_instances=event_solution_instances,
                graph_edges_solution=graph_edges_solution
            )

    @staticmethod
    def update_connected_events(
        event: Event,
        event_solution: EventSolution,
        event_solution_instances: dict[str, EventSolution],
        graph_edges_solution: dict[str, int]
    ) -> None:
        """Method to add previous and post events to the :class:`EventSolution`
        based on links described using the edge solutions.

        :param event: The instance of :class:`Event` that contains the
        relevant edge connections.
        :type event: :class:`Event`
        :param event_solution: The instance of :class:`EventSolution` to
        update the connected :class:`EventSolution` instances.
        :type event_solution: :class:`EventSolution`
        :param event_solutions: Dictionary of the :class:`EventSolution`
        :type event_solutions: `dict`[`str`, :class:`EventSolution`]
        :param edge_solutions: Dictionary of edge solutions
        :type edge_solutions: `dict`[`str`, `int`]
        """
        Graph.update_prev_events(
            event=event,
            event_solution=event_solution,
            event_solution_instances=event_solution_instances,
            graph_edges_solution=graph_edges_solution
        )
        Graph.update_post_events(
            event=event,
            event_solution=event_solution,
            event_solution_instances=event_solution_instances,
            graph_edges_solution=graph_edges_solution
        )

    @staticmethod
    def update_prev_events(
        event: Event,
        event_solution: EventSolution,
        event_solution_instances: dict[str, EventSolution],
        graph_edges_solution: dict[str, int]
    ) -> None:
        """Method to add previous events to the :class:`EventSolution`
        based on links described using the edge solutions.

        :param event: The instance of :class:`Event` that contains the
        relevant edge connections.
        :type event: :class:`Event`
        :param event_solution: The instance of :class:`EventSolution` to
        update the connected :class:`EventSolution` instances.
        :type event_solution: :class:`EventSolution`
        :param event_solutions: Dictionary of the :class:`EventSolution`
        :type event_solutions: `dict`[`str`, :class:`EventSolution`]
        :param edge_solutions: Dictionary of edge solutions
        :type edge_solutions: `dict`[`str`, `int`]
        """
        for edge_uid, in_edge in event.in_edges.items():
            if graph_edges_solution[edge_uid] == 1:
                event_solution.add_prev_event(
                    event_solution_instances[in_edge.event_out.uid]
                )

    @staticmethod
    def update_post_events(
        event: Event,
        event_solution: EventSolution,
        event_solution_instances: dict[str, EventSolution],
        graph_edges_solution: dict[str, int]
    ) -> None:
        """Method to add post events to the :class:`EventSolution`
        based on links described using the edge solutions.

        :param event: The instance of :class:`Event` that contains the
        relevant edge connections.
        :type event: :class:`Event`
        :param event_solution: The instance of :class:`EventSolution` to
        update the connected :class:`EventSolution` instances.
        :type event_solution: :class:`EventSolution`
        :param event_solutions: Dictionary of the :class:`EventSolution`
        :type event_solutions: `dict`[`str`, :class:`EventSolution`]
        :param edge_solutions: Dictionary of edge solutions
        :type edge_solutions: `dict`[`str`, `int`]
        """
        for edge_uid, out_edge in event.out_edges.items():
            if graph_edges_solution[edge_uid] == 1:
                event_solution.add_post_event(
                    event_solution_instances[out_edge.event_in.uid]
                )

"""
Graph class to hold model info
"""
from typing import Type, Union, Iterable, Optional

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar
from flatdict import FlatterDict
import numpy as np
from .core.edge import Edge
from .core.group import ORGroup, XORGroup, ANDGroup, Group
from .core.event import Event, LoopEvent
from .utils.utils import solve_model


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
                    "type", "loop_graph", "is_loop"
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
                group_in=group_in,
                group_out=group_out,
                meta_data=(
                    event_def["meta_data"] if "meta_data" in event_def
                    else None
                ),
                loop_graph=(
                    event_def["loop_graph"] if "loop_graph" in event_def
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
        group_in: Optional[Group] = None,
        group_out: Optional[Group] = None,
        meta_data: Optional[dict] = None,
        loop_graph: Optional[dict] = None
    ) -> LoopEvent | Event:
        """Create :class:`Event` from :class:`CpModel`
        instance, an instance of :class:`Group` (or `None`) for the group into
        the event, an instance of :class:`Group` (or `None`) for the group
        out of the event, meta_data dictionary if present and loop_graph
        defintion dictionary if present.

        :param model: CP-SAT model
        :type model: :class:`CpModel`
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
        :return: Returns the instance of the created :class:`Event` or
        :class:`LoopEvent`
        :rtype: LoopEvent | Event
        """

        kwaargs = {
            "model": model,
            "in_group": group_in,
            "out_group": group_out,
        }
        # check for meta data
        if meta_data:
            kwaargs["meta_data"] = meta_data
        # check if loop event
        if loop_graph:
            kwaargs["sub_graph"] = Graph()
            event = LoopEvent(**kwaargs)
            # set the loop event sub graph
            event.set_graph_with_graph_def(loop_graph)
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
        variables_to_save = [
            group.variable for group_key_tuple, group in self.groups.items()
            if len(group_key_tuple) == 2
        ]
        # solve model
        group_solutions = solve_model(
            model=self.model,
            solver=solver,
            variables=variables_to_save
        )
        # get events solutions
        self.solutions = self.convert_to_event_solutions(group_solutions)
        # solve all loop event subgraphs
        self.solve_loop_events_sub_graphs(
            loop_events=self.filter_events(self.events.values())
        )

    def convert_to_event_solutions(
        self,
        solutions: dict[int, dict[str, int]]
    ) -> list[dict[str, int]]:
        """Method to convert a set of solutions to solutions in terms of
        Events. The solution must only include group solutions for the "in"
        and "out" groups of an Event

        :param solutions: Dictionary of solutions for group events
        :type solutions: `dict`[`int`, `dict`[`str`, `int`]]
        :return: Returns a list of solutions converted to event solutions
        :rtype: `list`[`dict`[`str`, `int`]]
        """
        events_solutions: list[dict[str, int]] = []
        for solution in solutions.values():
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
    def solve_loop_events_sub_graphs(loop_events: Iterable[LoopEvent]) -> None:
        """Static method to solve the subgraphs of the :class:`LoopEvent`'s in
        the iterable input.

        :param loop_events: Iterable of :class:`LoopEvent`'s
        :type loop_events: :class:`Iterable`[:class:`LoopEvent`]
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
        loop_events: Iterable[Union[Event, LoopEvent]]
    ) -> list[LoopEvent]:
        """Filters out anything but instances of :class:`LoopEvent` from the
        input iterable.

        :param loop_events: Iterable of :class:`Event`
        :type loop_events: :class:`Iterable`[:class:`Union`[:class:`Event`,
        :class:`LoopEvent`]]
        :return: Returns a list of :class:`LoopEvent`'s
        :rtype: `list`[:class:`LoopEvent`]
        """
        return list(filter(lambda x: isinstance(x, LoopEvent), loop_events))

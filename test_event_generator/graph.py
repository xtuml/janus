"""
Graph class to hold model info
"""
from typing import Type, Union

from ortools.sat.python.cp_model import CpModel, CpSolver
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
            is_source = not group_in
            # check if event is loop event or normal event
            if "is_loop" in event_def:
                if event_def["is_loop"]:
                    # instantiate a graph (needed due to circular imports)
                    sub_graph = Graph()
                    # create the loop event
                    event = LoopEvent(
                        model=self.model,
                        sub_graph=sub_graph,
                        in_group=group_in,
                        out_group=group_out,
                        is_source=is_source,
                        meta_data=(
                            event_def["meta-data"] if "meta-data" in event_def
                            else None
                        )
                    )
                    # set the loop event sub graph
                    event.set_graph_with_graph_def(event_def["loop_graph"])
            else:
                event = Event(
                    model=self.model,
                    in_group=group_in,
                    out_group=group_out,
                    is_source=is_source,
                    meta_data=(
                        event_def["meta-data"] if "meta-data" in event_def
                        else None
                    )
                )
            self.events[event_uid] = event

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

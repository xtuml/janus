"""
Class to hold Event data and set flow and sink source
constraints
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ortools.sat.python.cp_model import CpModel
if TYPE_CHECKING:
    from .group import Group
    from ..graph import Graph


class Event:
    """Event class as a node in a graph. Holds information on the Groups
    entering and leaving the Event.

    :param model: The ortools CP-SAT model instance to
    add the edge as a variable
    :type model: :class:`CpModel`
    :param in_group: The :class:`Group` instance entering the Event, defaults
    to `None`
    :type in_group: :class:`Optional`[:class:`Group`], optional
    :param out_group: The :class:`Group`, defaults to `None`
    :type out_group: :class:`Optional`[:class:`Group`], optional
    :param meta_data: A dictionary of meta-data relating to the Event,
     defaults to `None`
    :type meta_data: :class:`Optional`[`dict`], optional
    :raises :class:`Exception`: Raises an error if the Event is a source and
    has a :class:`Group` instance that enters the Event instance.
    """
    def __init__(
        self,
        model: CpModel,
        in_group: Optional[Group] = None,
        out_group: Optional[Group] = None,
        meta_data: Optional[dict] = None
    ) -> None:
        """Constructor method
        """
        self.model = model
        self.in_group = in_group
        self.out_group = out_group
        self.meta_data = meta_data
        self.set_flow_constraint()

    def set_flow_constraint(self) -> None:
        """Method to set the flow constraint.

        This sets the group coming into the Event equal to the group exiting
        the Event.

        If there is an exiting group and the Event is a source then the
        variable of the exiting group is equal to 1 instead.
        """
        if self.in_group and self.out_group:
            # flow conservation
            self.model.Add(self.in_group.variable == self.out_group.variable)

    def set_groups_event(self, group: Optional[Group]) -> None:
        """Method to set the Event instance of the input Group to the instance
        itself and set the sub-groups and Edges parent group to the input Group

        :param group: The Group instance to update
        :type group: :class:`Optional`[:class:`Group`]
        """
        if group:
            group.event = self
            group.set_sub_groups_parent()

    @property
    def in_group(self) -> Group | None:
        """Getter of property in_group

        :return: The Group that enters the Event
        :rtype: :class:`Group` | `None`
        """
        return self._in_group

    @in_group.setter
    def in_group(self, group: Optional[Group]) -> None:
        """Setter of property in_group

        :param group: The Group that enters the Event
        :type group: :class:`Optional`[:class:`Group`]
        """
        self._in_group = group
        self.set_groups_event(self._in_group)

    @property
    def out_group(self) -> Group | None:
        """Getter of property out_group

        :return: The Group that leaves the Event
        :rtype: :class:`Group` | `None`
        """
        return self._out_group

    @out_group.setter
    def out_group(self, group: Optional[Group]) -> None:
        """Setter of property out_group

        :param group: The Group that leaves the Event
        :type group: :class:`Optional`[:class:`Group`]
        """
        self._out_group = group
        self.set_groups_event(self._out_group)

    @property
    def is_start(self) -> bool:
        """Property indicating is start point (out group with no in group) in
        the graph i.e. the graph can start with this event.

        :return: Boolean value indicating if the :class:`Event` instance is a
        start point.
        :rtype: `bool`
        """
        return bool(self.out_group and not self.in_group)

    @property
    def is_end(self) -> bool:
        """Property indicating is end point (in group with no out group) in
        the graph i.e. the graph can end with this event.

        :return: Boolean value indicating if the :class:`Event` instance is an
        end point.
        :rtype: `bool`
        """
        return bool(self.in_group and not self.out_group)


class LoopEvent(Event):
    """LoopEvent subclass of :class:`Event`. Holds a sub_graph as a
    :class:`Graph` instance that defines the event graph within the loop.

    :param model: The ortools CP-SAT model instance to
    add the edge as a variable
    :type model: :class:`CpModel`
    :param sub_graph_def: The standardised graph definition that defines the
    loop sub graph. Must include a "StartEvent" and "EndEvent" to begin and
    end the sub graph.
    :type sub_graph_def: `dict`
    :param in_group: The :class:`Group` instance entering the Event, defaults
    to `None`
    :type in_group: :class:`Optional`[:class:`Group`], optional
    :param out_group: The :class:`Group`, defaults to `None`
    :type out_group: :class:`Optional`[:class:`Group`], optional
    :param meta_data: A dictionary of meta-data relating to the Event,
     defaults to `None`
    :type meta_data: :class:`Optional`[`dict`], optional
    :raises :class:`Exception`: Raises an error if the Event is a source and
    has a :class:`Group` instance that enters the Event instance.
    """
    def __init__(
        self,
        model: CpModel,
        sub_graph: Graph,
        in_group: Optional[Group] = None,
        out_group: Optional[Group] = None,
        meta_data: Optional[dict] = None
    ) -> None:
        """Constructor method
        """
        super().__init__(model, in_group, out_group, meta_data)
        self.sub_graph = sub_graph

    @property
    def sub_graph(self) -> Graph:
        """Getter property for the instance :class:`Graph` instance that
        defines the sub graph

        :return: The instances :class:`Graph` instance that describes the sub
        graph.
        :rtype: :class:`Graph`
        """
        return self._sub_graph

    @sub_graph.setter
    def sub_graph(self, graph: Graph) -> None:
        """Getter property for the instance :class:`Graph` instance that
        defines the sub graph.

        :param graph: A :class:`Graph` instance to define the sub graph.
        :type graph: :class:`Graph`
        """
        self._sub_graph = graph

    def set_graph_with_graph_def(self, graph_def: dict[str, dict]) -> None:
        """Setter function to set the instances `graph` attribute.

        :param graph_def: Standardised graph definition that defines the loop
        sub graph.
        :type graph_def: `dict`
        """
        self.sub_graph.parse_graph_def(graph_def)

    def solve_sub_graph(self) -> None:
        """Method to solve the instance's sub graph.
        """
        self.sub_graph.solve()

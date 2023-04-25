"""
Class defining Edge structure along with variables
used for an ortools model
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ortools.sat.python.cp_model import CpModel

if TYPE_CHECKING:
    from .event import Event
    from .group import Group


class Edge:
    """Edge class to implement an Edge from one Event to another in a directed
    graph of a Job Definition. Holds an ortools :class:`IntVar` variable
    constrained to be 0 or 1.

    :param model: The ortools CP-SAT model instance to
    add the edge as a variable to
    :type model: :class:`CpModel`
    :param uid: A unique identifier for the Edge
    :type uid: `str`
    :param event_in: An Event that the Edge is directed into, defaults to None
    :type event_in: :class:`Optional`[:class:`Event`], optional
    :param event_out: An Event that the Edge is directed out of,
    defaults to None
    :type event_out: :class:`Optional`[:class:`Event`], optional
    :param group_out: A Group that the Edge is in that directed out of an
    Event, defaults to None
    :type group_out: :class:`Optional`[:class:`Group`], optional
    :param group_in: , defaults to `None`
    :type group_in: :class:`Optional`[:class:`Group`], optional
    """
    def __init__(
        self,
        model: CpModel,
        uid: str,
        event_in: Optional[Event] = None,
        event_out: Optional[Event] = None,
        group_out: Optional[Group] = None,
        group_in: Optional[Group] = None,
    ) -> None:
        """Constructor method
        """
        self.model = model
        self.variable = self.model.NewBoolVar(uid)
        self.uid = uid
        self.event_out = event_in
        self.event_in = event_out
        self.group_out = group_out
        self.group_in = group_in

    @property
    def event_out(self) -> Event | None:
        """Getter for event_out property

        :return: The Event that the Edge is directed out of
        :rtype: :class:`Event` | `None`
        """
        return self._event_out

    @event_out.setter
    def event_out(self, event: Optional[Event]) -> None:
        """Setter for event_out property

        :param event: The Event that the Edge is directed out of
        :type event: :class:`Optional`[:class:`Event`]
        """
        if event:
            event.set_out_edges(self)
        self._event_out = event

    @property
    def event_in(self) -> Event | None:
        """Getter for event_in property

        :return: The Event that the Edge is directed into
        :rtype: :class:`Event` | `None`
        """
        return self._event_in

    @event_in.setter
    def event_in(self, event: Optional[Event]) -> None:
        """Setter for event_in property

        :param event: The Event that the Edge is directed into
        :type event: :class:`Optional`[:class:`Event`]
        """
        if event:
            event.set_in_edges(self)
        self._event_in = event

    @property
    def group_out(self) -> Group | None:
        """Getter for the group_out property

        :return: The Group instance that the Edge is part of
        that is directed out of the Event event_out
        :rtype: :class:`Group` | `None`
        """
        return self._group_out

    @group_out.setter
    def group_out(self, group: Optional[Group]) -> None:
        """Setter for the group_out property

        :param group: The Group instance that the Edge is part of
        that is directed out of the Event event_out
        :type group: :class:`Optional`[:class:`Group`]
        """
        self._group_out = group

    @property
    def group_in(self) -> Group | None:
        """Getter for the group_in property

        :return: The Group instance that the Edge is part of
        that is directed into the Event event_in
        :rtype: :class:`Group` | `None`
        """
        return self._group_in

    @group_in.setter
    def group_in(self, group: Optional[Group]) -> None:
        """Setter for the group_in property

        :param group: The Group instance that the Edge is part of
        that is directed into the Event event_in
        :type group: :class:`Optional`[:class:`Group`]
        """
        self._group_in = group

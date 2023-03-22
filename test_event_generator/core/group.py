"""Contains Group class that is a constrained
set of edges as a variable
"""
from __future__ import annotations
from typing import (
    Callable,
    Optional,
    Union,
    TYPE_CHECKING
)

from ortools.sat.python.cp_model import CpModel
from .edge import Edge
if TYPE_CHECKING:
    from .event import Event


class Group:
    """Group base class used to implement a grouping of a mixture of
    sub-groups and edges. Holds an ortools :class:`IntVar` variable
    constrained to be 0 or 1.

    :param model: The ortools CP-SAT model instance to
    add the edge as a variable to
    :type model: :class:`CpModel`
    :param uid: A unique identifier for the Group
    :type uid: `str`
    :param group_variables: A list of Edges and Groups that are part of the
    Group
    :type group_variables: `list`[:class:`Union`[:class:`Edge`, :class:`Group`]
    ]
    :param is_into_event: A boolean value to signify that the Group is into an
    Event (True) or out of an Event (False)
    :type is_into_event: `bool`
    :param parent_group: The Group that the instance is part of (if it is part
    of one), defaults to `None`
    :type parent_group: :class:`Optional`[:class:`Group`], optional
    :param event: The Event that the Groups goes into/out of, defaults to None
    :type event: :class:`Optional`[:class:`Event`], optional
    """
    def __init__(
        self,
        model: CpModel,
        uid: str,
        group_variables: list[Union[Edge, 'Group']],
        is_into_event: bool,
        parent_group: Optional['Group'] = None,
        event: Optional[Event] = None
    ) -> None:
        """Constructor method
        """
        self.group_variables = group_variables
        self.model = model
        self.variable = self.model.NewBoolVar(uid)
        self.is_into_event = is_into_event
        self.parent_group = parent_group
        self.event = event

    def set_arbitrary_constraint(self, func: Callable, **kwargs) -> None:
        """Method to set an arbitrary constraint using a given function

        :param func: Function to call on instance with kwargs
        :type func: Callable
        """
        func(self, **kwargs)

    @property
    def parent_group(self) -> 'Group' | None:
        """Getter for property parent_group

        :return: The parent group of the instance (if there is one)
        :rtype: :class:`Group` | `None`
        """
        return self._parent_group

    @parent_group.setter
    def parent_group(self, group: Optional['Group']) -> None:
        """Setter for property parent_group

        :param group: The parent group of the instance (if there is one)
        :type group: Optional[:class:`Group`]
        """
        self._parent_group = group

    @property
    def event(self) -> Event | None:
        """Getter for property event

        :return: The event of the instance (if there is one)
        :rtype: :class:`Event` | `None`
        """
        return self._event

    @event.setter
    def event(self, event: Optional[Event]) -> None:
        """Setter for property event

        :param group: The event of the instance (if there is one)
        :type group: Optional[:class:`Event`]
        """
        self._event = event

    def set_sub_groups_parent(self) -> None:
        """Method to set the instance as the parent group of the edges and
        sub-groups
        """
        for sub_group in self.group_variables:
            if isinstance(sub_group, Edge):
                if self.is_into_event:
                    sub_group.group_in = self
                    sub_group.event_in = self.event
                else:
                    sub_group.group_out = self
                    sub_group.event_out = self.event
            else:
                sub_group.parent_group = self
                sub_group.event = self.event
                sub_group.set_sub_groups_parent()


class ORGroup(Group):
    """Group sub class used to implement a grouping of a mixture of
    sub-groups and edges that abide by an OR constraint. Holds an ortools
    :class:`IntVar` variable constrained to be 0 or 1.

    :param model: The ortools CP-SAT model instance to
    add the edge as a variable to
    :type model: :class:`CpModel`
    :param uid: A unique identifier for the Group
    :type uid: `str`
    :param group_variables: A list of Edges and Groups that are part of the
    Group
    :type group_variables: `list`[:class:`Union`[:class:`Edge`, :class:`Group`]
    ]
    :param is_into_event: A boolean value to signify that the Group is into an
    Event (True) or out of an Event (False)
    :type is_into_event: `bool`
    :param parent_group: The Group that the instance is part of (if it is part
    of one), defaults to `None`
    :type parent_group: :class:`Optional`[:class:`Group`], optional
    :param event: The Event that the Groups goes into/out of, defaults to None
    :type event: :class:`Optional`[:class:`Event`], optional
    """
    def __init__(
        self,
        model: CpModel,
        uid: str,
        group_variables: list[Union[Edge, 'Group']],
        is_into_event: bool,
        parent_group: Optional['Group'] = None,
        event: Optional[Event] = None
    ) -> None:
        """Constructor method
        """
        super().__init__(
            model,
            uid,
            group_variables,
            is_into_event,
            parent_group,
            event
        )
        self.set_on_constraint()
        self.set_off_constraint()

    def set_off_constraint(self) -> None:
        """Sets the off constraint for the Group i.e. when all sub-groups and
        edges are 0 then the Group instance is 0.
        """
        self.model.Add(self.variable <= sum(
            group.variable for group in self.group_variables
        ))

    def set_on_constraint(self) -> None:
        """Sets the on constraint for the Group i.e. when at least on of the
        sub-groups and edges is 1 then the Group instance is 1.
        """
        for var in self.group_variables:
            self.model.Add(var.variable <= self.variable)


class ANDGroup(Group):
    """Group sub class used to implement a grouping of a mixture of
    sub-groups and edges that abide by an AND constraint. Holds an ortools
    :class:`IntVar` variable constrained to be 0 or 1.

    :param model: The ortools CP-SAT model instance to
    add the edge as a variable to
    :type model: :class:`CpModel`
    :param uid: A unique identifier for the Group
    :type uid: `str`
    :param group_variables: A list of Edges and Groups that are part of the
    Group
    :type group_variables: `list`[:class:`Union`[:class:`Edge`, :class:`Group`]
    ]
    :param is_into_event: A boolean value to signify that the Group is into an
    Event (True) or out of an Event (False)
    :type is_into_event: `bool`
    :param parent_group: The Group that the instance is part of (if it is part
    of one), defaults to `None`
    :type parent_group: :class:`Optional`[:class:`Group`], optional
    :param event: The Event that the Groups goes into/out of, defaults to None
    :type event: :class:`Optional`[:class:`Event`], optional
    """
    def __init__(
        self,
        model: CpModel,
        uid: str,
        group_variables: list[Union[Edge, 'Group']],
        is_into_event: bool,
        parent_group: Optional['Group'] = None,
        event: Optional[Event] = None
    ) -> None:
        """Constructor method
        """
        super().__init__(
            model,
            uid,
            group_variables,
            is_into_event,
            parent_group,
            event
        )
        self.set_and_constraint()

    def set_and_constraint(self) -> None:
        """Sets the AND constraint for the Group i.e Either all sub-groups and
        edges are all equal to 0 with the Group instance equal to 0 also or all
        sub-groups and edges are all equal to 1 with the Group instance equal
        to 1 also.
        """
        for var in self.group_variables:
            self.model.Add(self.variable == var.variable)


class XORGroup(Group):
    """Group sub class used to implement a grouping of a mixture of
    sub-groups and edges that abide by a XOR constraint. Holds an ortools
    :class:`IntVar` variable constrained to be 0 or 1.

    :param model: The ortools CP-SAT model instance to
    add the edge as a variable to
    :type model: :class:`CpModel`
    :param uid: A unique identifier for the Group
    :type uid: `str`
    :param group_variables: A list of Edges and Groups that are part of the
    Group
    :type group_variables: `list`[:class:`Union`[:class:`Edge`, :class:`Group`]
    ]
    :param is_into_event: A boolean value to signify that the Group is into an
    Event (True) or out of an Event (False)
    :type is_into_event: `bool`
    :param parent_group: The Group that the instance is part of (if it is part
    of one), defaults to `None`
    :type parent_group: :class:`Optional`[:class:`Group`], optional
    :param event: The Event that the Groups goes into/out of, defaults to None
    :type event: :class:`Optional`[:class:`Event`], optional
    """
    def __init__(
        self,
        model: CpModel,
        uid: str,
        group_variables: list[Union[Edge, 'Group']],
        is_into_event: bool,
        parent_group: Optional['Group'] = None,
        event: Optional[Event] = None
    ) -> None:
        """Constructor method
        """
        super().__init__(
            model,
            uid,
            group_variables,
            is_into_event,
            parent_group,
            event
        )
        self.set_xor_constraint()

    def set_xor_constraint(self) -> None:
        """Sets XOR constraint for the Group i.e Either only one of the
        sub-groups and edges is equal to 1 with the rest 0 and the Group
        instance equal to 1 or all of the sub-groups and edges are equal to 0
        and the Group instance is equal to 0.
        """
        self.model.Add(sum(
            group.variable for group in self.group_variables
        ) == self.variable)

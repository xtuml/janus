"""Parser for .puml files
"""
from __future__ import annotations
import re
from copy import copy
from typing import Optional

meta_data_fields = [
    "BCNT",
    "LCNT",
    "IINV",
    "EINV",
]

statement_mappings = {
    "if": [("START", "XOR"), ("PATH", "XOR")],
    "else": [("PATH", "XOR")],
    "elseif": [("PATH", "XOR")],
    "endif": [("END", "XOR")],
    "switch": [("START", "XOR")],
    "case": [("PATH", "XOR")],
    "endswitch": [("END", "XOR")],
    "fork": [("START", "AND"), ("PATH", "AND")],
    "fork again": [("PATH", "AND")],
    "end fork": [("END", "AND")],
    "split": [("START", "OR"), ("PATH", "OR")],
    "split again": [("PATH", "OR")],
    "end split": [("END", "OR")],
    "repeat": [("START", "LOOP")],
    "repeat while": [("END", "LOOP")],
    "break": ["BREAK"],
    "detach": ["DETACH"],
    "kill": ["DETACH"]
}


def get_unparsed_job_defs(
    puml_file: str
) -> list[tuple[str, str]]:
    """Method to get unparsed job definitions from puml

    :param puml_file: The puml file loaded in as a string
    :type puml_file: `str`
    :return: Returns a list of tuples of the job definitions found in the puml
    file. The tuples contain a job defintion name and raw job defintion pair.
    :rtype: `list`[`tuple`[`str`, `str`]]
    """
    raw_job_defs = re.findall(
        (
            r'partition\s*\"(.*)\"\s*{\s*\n.*group\s*\".*\"\s*\n(.*)end group'
            r'\s*\n\s*}\s*\n'
        ),
        puml_file,
        re.DOTALL
    )
    return raw_job_defs


def get_graph_defs_from_puml(
    puml_file: str
) -> dict[str, dict]:
    """Method to get a dictionary of graph defs and job name from puml file

    :param puml_file: The puml file loaded in as a string
    :type puml_file: `str`
    :return: Returns a dictionary of the job names and corresponding graph
    definitions
    :rtype: `dict`[`str`, `dict`]
    """
    # get the unparsed job def list of tuples
    raw_job_def_tuples = get_unparsed_job_defs(puml_file)
    return {
        raw_job_def_tuple[0]: get_graph_def_from_raw_job_def_tuple(
            raw_job_def_tuple
        )
        for raw_job_def_tuple in raw_job_def_tuples
    }


def get_graph_def_from_raw_job_def_tuple(
    raw_job_def_tuple: tuple[str, str]
) -> dict:
    """Method to obtain a graph definition from a raw job def tuple

    :param raw_job_def_tuple: _description_
    :type raw_job_def_tuple: `tuple`[`str`, `str`]
    :return: Returns the graph def extracted
    :rtype: `dict`
    """
    job = Job()
    job.parse_raw_job_def(raw_job_def_tuple)
    job.full_parse()
    graph_def = job.write_graph_definition()
    return graph_def


def parse_raw_job_def_lines(
    raw_job_def_lines: list[str]
) -> list[str]:
    """Method to clean lines of un-needed substrings
    and search for and create :class:`EventData` when they are found

    :param raw_job_def_lines: List of lines in a raw job def
    :type raw_job_def_lines: `list`[`str`]
    :return: Returns a list of mapped indicators
    :rtype: `list`[`str`]
    """
    parsed_lines: list[str | EventData] = []
    for line in raw_job_def_lines:
        # clean line
        cleaned_line = clean_line(line)
        if not cleaned_line:
            continue
        # event option
        if re.search(r':.*;', cleaned_line):
            event = EventData()
            event.parse_cleaned_event_string(cleaned_line)
            parsed_lines.append(event)
        # non event options
        else:
            indicator = re.search(
                r'^([a-zA-Z\s]*)(\(|\s*)',
                cleaned_line
            )
            if indicator:
                indicator = " ".join(indicator.group(1).strip().split())
                if statement_mappings[indicator] == "DETACH":
                    parsed_lines[-1].is_end = True
                elif statement_mappings[indicator] == "BREAK":
                    parsed_lines[-1].is_break = True
                else:
                    parsed_lines.extend(statement_mappings[indicator])
    return parsed_lines


def clean_line(line: str) -> str:
    """Method to clean a job definition line.
    * strips line
    * removes colour options from the line if there

    :param line: String representing the line in the job def
    :type line: `str`
    :return: Returns the cleaned job def line
    :rtype: `str`
    """
    cleaned_line = line.strip()
    # remove colours
    colour_removal = re.search(r'(#[a-zA-Z]*\s*):', cleaned_line)
    if colour_removal:
        cleaned_line = cleaned_line.replace(
            colour_removal.group(1),
            ""
        )
    return cleaned_line


def loop_parse(
    parsed_job: list[str | "EventData"],
    event_type_occurence_count: dict
) -> list[str | EventData | LoopEventData]:
    """Method to obtain all loop events and nested loop events from a
    cleaned list of job def lines

    :param parsed_job: List of indicators and :class:`EventData` defining a job
    :type parsed_job: `list`[`str`, :class:`EventData`]
    :param event_type_occurence_count: Dictionary containing event type
    occurence counts
    :type event_type_occurence_count: `dict`
    :return: Returns parsed job list with the addition of any
    :class:`LoopEventData`
    :rtype: list[`str` | :class:`EventData` | :class:`LoopEventData`]
    """
    # top level list to hold parsed job data
    loop_parsed_job: list[str | EventData] = []
    # set the list that will be appended by EventData and indicator
    # strings to the top level list
    list_to_append = loop_parsed_job
    # list to hold LoopEventData - end member will be the loop entries are
    # added to
    loop_events: list[LoopEventData] = []
    for entry in parsed_job:
        # if EventData add to the list to append
        if isinstance(entry, EventData):
            list_to_append.append(entry)
        # if the entry indicates a loop else add to list to append
        elif "LOOP" in entry:
            # if a loop start create new LoopEventData and add to loop
            # events list, add to list_to_appned and update list_to_append
            # to the LoopEventData's sub job parsed job list
            if "START" in entry:
                new_loop_event = LoopEventData(
                    event_type_occurence_count
                )
                new_loop_event.event_type = "Loop"
                loop_events.append(new_loop_event)
                list_to_append.append(new_loop_event)
                list_to_append = new_loop_event.get_job_parsed_job_list()
            # else pop loop from end of loop events and update list to
            # append t the sub job of the last entry of loop events if
            # there are any LoopEventData in the list of loop events
            # otherwise set list to append to the top level
            # loop_parsed_job list
            else:
                loop_events.pop()
                if loop_events:
                    list_to_append = (
                        loop_events[-1].get_job_parsed_job_list()
                    )
                else:
                    list_to_append = loop_parsed_job
        # otherwise append entry to list_to_append
        else:
            list_to_append.append(entry)
    return loop_parsed_job


class Job:
    """Class to handle the parsing of a cleaned job definition

    :param parsed_job: Cleaned job definition lines containing indicators and
    :class:`EventData`
    :type parsed_job: `list`[`str`  | :class:`EventData`]
    """
    def __init__(
        self,
    ) -> None:
        """Constructor method
        """
        self.name: Optional[str] = None
        self.parsed_job: Optional[list[str, EventData]] = None
        self.events: dict[tuple[str, int], EventData] = {}
        self.event_type_occurence_count = {}
        self.edges = {}

    def count_event_occurence(self) -> None:
        """Method to count occurrences of events and to assign occurence id to
        :class:`EventData`'s
        """
        for entry in self.parsed_job:
            # if the entry in the cleaned job list is not EventData nothing
            # needs to be done
            if not isinstance(entry, EventData):
                continue
            # if the event type doesn't belong to the dictionary intialise
            # else add one to the entry count
            if entry.event_type not in self.event_type_occurence_count:
                self.event_type_occurence_count[entry.event_type] = 0

            else:
                self.event_type_occurence_count[entry.event_type] += 1
            # update occurence id for entry
            entry.occurence_id = self.event_type_occurence_count[
                entry.event_type
            ]
            # add to dictionary of events
            self.events[entry.event_tuple] = entry
            # if the entry is LoopEventData count the events in the sub job
            # also
            if isinstance(entry, LoopEventData):
                entry.job.count_event_occurence()

    def add_edge(
        self,
        event_start: "EventData",
        event_end: "EventData"
    ) -> Edge | None:
        """Method to add an edge to the job given two :class:`EventData`'s.
        Returns the edge in question

        :param event_start: The event the edge is directed out from
        :type event_start: :class:`EventData`
        :param event_end: The event the edge is directed into
        :type event_end: :class:`EventData`
        :return: Returns the created :class:`Edge` or `None` if the start
        event detaches
        :rtype: :class:`Edge` | `None`
        """
        if event_start.is_end:
            return
        edge_tuple = (event_start, event_end)
        if edge_tuple not in self.edges:
            self.edges[edge_tuple] = Edge(
                edge_tuple
            )
        return self.edges[edge_tuple]

    def parse_raw_job_def(
        self,
        raw_job_def_tuple: tuple[str, str]
    ) -> None:
        """Method to parse in a name and raw job def string tuple

        :param raw_job_def_tuple: Tuple containing the name of the job def and
        the raw job def string
        :type raw_job_def_tuple: `tuple`[`str`, `str`]
        """
        self.name = raw_job_def_tuple[0]
        # split raw job def on new lines
        raw_job_def_lines = raw_job_def_tuple[1].split('\n')
        # pre-parse
        pre_parse = parse_raw_job_def_lines(raw_job_def_lines)
        # parse loops
        self.parsed_job = loop_parse(
            pre_parse,
            self.event_type_occurence_count
        )

    def full_parse(
        self
    ) -> None:
        # count events
        self.count_event_occurence()
        # parse groups
        mid_parse = self.parse_indicators()
        # final parse
        self.final_parse(mid_parse)

    def parse_indicators(
        self,
    ) -> list[EventData | Group]:
        """Method to parse indicators to :class:`Group`'s. Also fully parses
        sub :class:`Job`'s of :class:`LoopEventData`

        :return: Returns a list of :class:`EventData` and :class:`Group`
        describing the job def
        :rtype: `list`[:class:`EventData` | `Group`]
        """
        parsed_job = self.parsed_job
        # highest level list to hold the parsed job
        mid_parsed_job = []
        # set the list to append to the highest level list to start
        list_to_append = mid_parsed_job
        # initiate list of Group's
        groups: list["Group"] = []
        # loop over entries and parse
        for entry in parsed_job:
            # if EventData just add to list
            if isinstance(entry, EventData):
                list_to_append.append(entry)
                # if this is also LoopEventData fully parse the sub job
                if isinstance(entry, LoopEventData):
                    loop_mid_parsed_job = entry.job.parse_indicators()
                    entry.job.final_parse(loop_mid_parsed_job)
            # if the entry indicates a path to be taken add to path and update
            # list_to_append to that most recent path
            elif "PATH" in entry:
                groups[-1].add_new_path()
                list_to_append = groups[-1].get_most_recent_path()
            else:
                # if entry indicates the start of a Group intialise and add to
                # list of Group's
                if "START" in entry:
                    groups.append(Group(entry[1]))
                # if entry indicates an end remove last member of Group's list
                # and update list to append to the now last member of the
                # list's most recent path or if there are no more Group's in
                # the list set it to mid_parse_job then add the Group to that
                # list
                elif "END" in entry:
                    group = groups.pop()
                    if groups:
                        list_to_append = groups[-1].get_most_recent_path()
                    else:
                        list_to_append = mid_parsed_job
                    list_to_append.append(group)
        return mid_parsed_job

    def final_parse(
        self,
        mid_parse_job: list["EventData" | "Group"],
        prev_entry: Optional["EventData" | "Group"] = None
    ) -> None:
        """Recursive method to perfrom a final parse of the job and add edges
        between events

        :param mid_parse_job: Parsed job definition with indicators parsed to
        :class:`Group`'s.
        :type mid_parse_job: `list`[:class:`EventData`  |  :class:`Group]
        :param prev_entry: The previous entry in the parsed job list, defaults
        to `None`
        :type prev_entry: :class:`Optional`[:class:`EventData`  |
        :class:`Group`], optional
        """
        # copy parsed job list
        copied_job = copy(mid_parse_job)
        # get the entry by popping the first member of the list
        entry = copied_job.pop(0)
        # check if the entry is EventData
        if isinstance(entry, EventData):
            # if there is a prev entry create a Group for its group_in
            if prev_entry:
                entry.group_in = Group()
            # if the previous entry is an event, the entry event only has a
            # single edge coming in so create that edge and add it to the
            # group_in
            if isinstance(prev_entry, EventData):
                edge = self.add_edge(
                    event_start=prev_entry,
                    event_end=entry
                )
                if edge:
                    entry.group_in.add_sub_group(edge)
                    # if the previous entry does not have a group out create on
                    # and add the edge to it
                    if not prev_entry.group_out:
                        prev_entry.group_out = Group()
                        prev_entry.group_out.add_sub_group(edge)
            # if the entry is a Group
            elif isinstance(prev_entry, Group):
                # get all events going into the entry event by searching for
                # the ending events in the previous entry Group
                in_events = prev_entry.get_merge_end_events()
                # loop over those events and create an edge and add to
                # group_in and each of the ending events group_out,
                # respectively
                for event in in_events:
                    edge = self.add_edge(
                        event_start=event,
                        event_end=entry
                    )
                    if not edge:
                        continue
                    entry.group_in.add_sub_group(edge)
                    event.group_out = Group()
                    event.group_out.add_sub_group(edge)
        # if the entry is a Group
        elif isinstance(entry, Group):
            # if previous entry is an EventData update its group_out to the
            # entry
            if isinstance(prev_entry, EventData):
                if not prev_entry.group_out:
                    prev_entry.group_out = entry
            # loop over the entries paths and parse that path into the job.
            # This will recursively search for nested paths within the entries
            # paths
            for path in entry.paths:
                self.final_parse(
                    mid_parse_job=path,
                    prev_entry=prev_entry
                )
                # set top level edges
                if isinstance(path[0], EventData):
                    entry.add_sub_group(self.edges[(prev_entry, path[0])])
                else:
                    entry.add_sub_group(path[0])
        # recursive parse for next entry
        if copied_job:
            self.final_parse(
                mid_parse_job=copied_job,
                prev_entry=entry
            )

    def write_graph_definition(self) -> dict:
        """Method to write the graph definition from the instance events dict
        after parsing

        :return: Returns a standardised graph definition
        :rtype: `dict`
        """
        graph_definition = {}
        # loop over events and expand any groups (in or out)
        for event in self.events.values():
            graph_definition[str(event)] = {
                "group_in": (
                    event.group_in.expand_group_def() if event.group_in
                    else None
                ),
                "group_out": (
                    event.group_out.expand_group_def() if event.group_out
                    else None
                ),
                "meta_data": {
                    "EventType": event.event_type,
                    "isBreak": event.is_break
                }
            }
            # if the EventData is LoopEventData get the graph definition of
            # the sub job
            if isinstance(event, LoopEventData):
                graph_definition[str(event)]["loop_graph"] = (
                    event.job.write_graph_definition()
                )
        return graph_definition


class EventData:
    """Class to hold Data on Events
    """
    def __init__(self) -> None:
        """Constructor method
        """
        self.event_type: Optional[str] = None
        self.occurence_id: Optional[int] = None
        self.loop_counts: dict = {}
        self.branch_counts: dict = {}
        self.intra_job_invs: dict = {}
        self.extra_job_invs: dict = {}
        self.group_out: Optional[Group] = None
        self.group_in: Optional[Group] = None
        self.is_end: bool = False
        self.is_break: bool = False

    def parse_cleaned_event_string(
        self,
        event_string: str
    ) -> None:
        """MEthod to parse the event from a cleaned event string

        :param event_string: The cleaned event string
        :type event_string: `str`
        """
        event_string = event_string[1:-1]
        # split the string on commas
        event_raw_data = event_string.split(",")
        # get event type
        self.event_type = event_raw_data.pop(0)
        raw_data_list: list[list[str]] = []
        # get all the raw data
        while event_raw_data:
            raw_datum = event_raw_data.pop(0)
            if raw_datum in meta_data_fields:
                raw_data_list.append([raw_datum])
            else:
                raw_data_list[-1].append(raw_datum)
        # parse the relevant event data
        for raw_data in raw_data_list:
            name = self.pop_from_list_of_strings_by_substring(
                raw_data,
                sub_string="name="
            )
            if raw_data[0] == "LCNT":
                self.parse_loop_count(
                    name=name,
                    raw_data=raw_data
                )
            elif raw_data[0] == "BCNT":
                self.parse_branch_count(
                    name=name,
                    raw_data=raw_data
                )
            elif raw_data[0] == "IINV":
                self.parse_iinv(
                    name=name,
                    raw_data=raw_data
                )
            elif raw_data[0] == "EINV":
                self.parse_einv(
                    name=name,
                    raw_data=raw_data
                )

    def __hash__(self) -> int:
        """Dunder hash method

        :return: Returns the hash
        :rtype: `int`
        """
        return hash((self.event_type, self.occurence_id))

    def __repr__(self) -> str:
        """Dunder str representation method

        :return: Returns the string representation of the instance
        :rtype: `str`
        """
        if self.occurence_id is not None:
            return self.event_type + f"_{self.occurence_id}"
        return self.event_type

    @property
    def event_tuple(self) -> tuple[str | None, int | None]:
        """Property to provide the event tuple
        (EventType, occurence_id)

        :return: _description_
        :rtype: tuple[str | None, int | None]
        """
        return (self.event_type, self.occurence_id)

    @staticmethod
    def pop_from_list_of_strings_by_substring(
        list_of_strings: list[str],
        sub_string: str
    ) -> Optional[str]:
        """Helper method to pop member from a list of strings by substring

        :param list_of_strings: The list of strings to act on
        :type list_of_strings: `list`[`str`]
        :param sub_string: The sub-string to search for
        :type sub_string: `str`
        :return: Returns the string remainder if the substring is found
        otherwise returns `None`
        :rtype: `str` | `None`
        """
        counter = 0
        for string in list_of_strings:
            if sub_string in string:
                break
            counter += 1
        if counter < len(list_of_strings):
            string_remainder = list_of_strings.pop(counter)
            return string_remainder.replace(sub_string, "")

    def parse_loop_count(
        self,
        name: str,
        raw_data: list[str]
    ) -> None:
        """Method to parse LCNT

        :param name: The name of the loop count
        :type name: `str`
        :param raw_data: The raw data to search in
        :type raw_data: `list`[`str`]
        """
        self.loop_counts[name] = {
            "user": self.pop_from_list_of_strings_by_substring(
                raw_data,
                "user="
            )
        }

    def parse_branch_count(
        self,
        name: str,
        raw_data: list[str]
    ) -> None:
        """Method to parse BCNT

        :param name: The name of the branch count
        :type name: `str`
        :param raw_data: The raw data to search in
        :type raw_data: `list`[`str`]
        """
        user_data = self.pop_from_list_of_strings_by_substring(
            raw_data,
            "user="
        )
        self.branch_counts[name] = {
            "user": user_data if user_data else self.event_type
        }

    def parse_iinv(
        self,
        name: str,
        raw_data: list[str]
    ) -> None:
        """Method to parse IINV

        :param name: The name of the intra job invariant
        :type name: `str`
        :param raw_data: The raw data to search in
        :type raw_data: `list`[`str`]
        """
        user_data = self.pop_from_list_of_strings_by_substring(
            raw_data,
            "user="
        )
        is_user = self.pop_from_list_of_strings_by_substring(
            raw_data,
            "USER"
        )
        self.intra_job_invs[name] = {
            "user": user_data,
            "is_user": bool(is_user),
            "is_src": bool(not is_user)
        }

    def parse_einv(
        self,
        name: str,
        raw_data: list[str]
    ) -> None:
        """Method to parse EINV

        :param name: The name of the extra job invariant
        :type name: `str`
        :param raw_data: The raw data to search in
        :type raw_data: `list`[`str`]
        """
        user_data = self.pop_from_list_of_strings_by_substring(
            raw_data,
            "user="
        )
        is_user = self.pop_from_list_of_strings_by_substring(
            raw_data,
            "USER"
        )
        is_src = self.pop_from_list_of_strings_by_substring(
            raw_data,
            "SRC"
        )
        self.intra_job_invs[name] = {
            "user": user_data,
            "is_user": bool(is_user),
            "is_src": bool(is_src)
        }


class LoopEventData(EventData):
    """Sub class of :class:`EventData` to handle loops in job def

    :param event_type_occurence_count: The dictionary to count event type
    occurence ids
    :type event_type_occurence_count: `dict`[`str`, :class:`EventData`  |
    :class:`LoopEventData`]
    """
    def __init__(
        self,
        event_type_occurence_count: dict[str, "EventData" | "LoopEventData"]
    ) -> None:
        """Constructor method
        """
        super().__init__()
        self.job = Job()
        self.job.parsed_job = []
        self.job.event_type_occurence_count = event_type_occurence_count

    def get_job_parsed_job_list(
        self
    ) -> list[str | EventData]:
        """Method to get the sub jobs parsed job list

        :return: Returns the sub job parsed job list
        :rtype: `list`[`str` | :class:`EventData`]
        """
        return self.job.parsed_job


class Group:
    """Class to hold in formation for constraints

    :param group_type: The type of :class:`Group` XOR, AND OR,
    defaults to "OR"
    :type group_type: :class:`Optional`[`str`], optional
    """
    def __init__(self, group_type: Optional[str] = "OR") -> None:
        """Constructor method
        """
        self.group_type = group_type
        self.paths: list[list["EventData" | "Group"]] = []
        self.groups: list["Group" | "Edge"] = []
        self.merge_edges = []

    def add_new_path(
        self,
    ) -> None:
        """Method to add a new path list to the instance paths attribute
        """
        self.paths.append([])

    def get_most_recent_path(
        self,
    ) -> list:
        """Method to get the member of the paths attribute

        :return: Returns the last member of the paths attribute
        :rtype: `list`
        """
        return self.paths[-1]

    def add_sub_group(
        self,
        sub_group: "Group" | "Edge"
    ) -> None:
        """Method to add :class:`Group` or :class:`Edge` to the list of groups

        :param sub_group: The sub group to add
        :type sub_group: :class:`Group` | :class:`Edge`
        """
        self.groups.append(sub_group)

    def get_merge_start_events(
        self
    ) -> list[EventData]:
        """Method to obtain the events that are at the front of the
        :class:`Group` that would merge into an event coming before it

        :return: Returns a list of the :class:`EventData` at the start of the
        :class:`Group`
        :rtype: `list`[:class:`EventData`]
        """
        merge_start_events = []
        for path in self.paths:
            if isinstance(path[0], EventData):
                merge_start_events.append(path[0])
            else:
                merge_start_events.extend(path[0].get_merge_start_events())
        return merge_start_events

    def get_merge_end_events(
        self
    ) -> list[EventData]:
        """Method to obtain the events that are at the end of the
        :class:`Group` that would merge into an event coming after it

        :return: Returns a list of the :class:`EventData` at the start of the
        :class:`Group`
        :rtype: `list`[:class:`EventData`]
        """
        merge_end_events = []
        for path in self.paths:
            if isinstance(path[-1], EventData):
                merge_end_events.append(path[-1])
            else:
                merge_end_events.extend(path[-1].get_merge_end_events())
        return merge_end_events

    def expand_group_def(self) -> dict[str, str | None]:
        """Method to get the group def for a standardised graph def.
        Also expands any sub groups

        :return: Returns a dictionary of the expanded group definition
        :rtype: `dict`[`str`, `str` | `None`]
        """
        group_def = {
            "type": self.group_type
        }
        sub_groups = [
            group.expand_group_def()
            if isinstance(group, Group)
            else str(group)
            for group in self.groups
        ]
        group_def["sub_groups"] = sub_groups
        return group_def


class Edge:
    """Class to hold information on edges between events

    :param edge_tuple: tuple defining event from and event to
    :type edge_tuple: `tuple`[:class:`EventData`, :class:`EventData`]
    """
    def __init__(
        self,
        edge_tuple: tuple[EventData, EventData]
    ) -> None:
        """Constructor method
        """
        self.edge_tuple = edge_tuple

    def __hash__(self) -> int:
        """Dunder hash method

        :return: Returns the hash of the instance
        :rtype: `int`
        """
        return hash(self.edge_tuple)

    def get_edge_tuple_repr(self) -> tuple[tuple[str | None, int | None], ...]:
        """Returns a tuple of the event tuples that define the edge

        :return: Returns the edge event tuple
        :rtype: `tuple`[`tuple`[`str` | `None`, `int` | `None`], `...`]
        """
        return tuple(
            event.event_tuple
            for event in self.edge_tuple
        )

    def __repr__(self) -> str:
        """Dunder string representation method

        :return: Returns a string representation of the edge
        :rtype: `str`
        """
        return "->".join(
            str(event)
            for event in self.edge_tuple
        )

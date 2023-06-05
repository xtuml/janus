"""Main function for running from command line
"""
import json
import os
from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from test_event_generator.graph import Graph
from test_event_generator.solutions import (
    get_audit_event_jsons_and_templates,
    GraphSolution
)
from test_event_generator.io.parse_puml import get_graph_defs_from_puml


def main(args: list[str]) -> None:
    """Main function to run command line with arguments.
    Usage:

    * `python -m test_event_generator graph.json --graphdef`
    * `python -m test_event_generator graph.json --graphdef --plot`
    * `python -m test_event_generator graph.json --graphdef --saveplot`
    * `python -m test_event_generator graph.json --graphdef --outsubdir
    <directory name>`
    * `python -m test_event_generator graph.json --graphdef --numloops 2`
    * `python -m test_event_generator graph.json --graphdef --numbranches 2`


    :param args: The list of arguments from the command line
    :type args: `list`[`str`]
    """
    # check if eith .json or .puml files are present
    file_paths: list[str] = [
        arg
        for arg in args
        if ".json" in arg or ".puml" in arg
    ]
    if len(file_paths) == 0:
        print("No file paths given")
        return
    num_loops = 2
    num_branches = 2
    out_sub_dir = None
    job_name = "default_job_name"
    return_plots = False
    save_fig = False
    # check command line options
    if "--numloops" in args:
        num_loops = int(get_arg_value(args, "--numloops"))
    if "--numbranches" in args:
        num_branches = int(get_arg_value(args, "--numbranches"))
    if "--outsubdir" in args:
        out_sub_dir = get_arg_value(args, "--outsubdir")
    if "--jobname" in args:
        job_name = get_arg_value(args, "--jobname")
    if "--plot" in args:
        return_plots = True
    if "--saveplot" in args:
        return_plots = True
        save_fig = True
    if "--graphdef" in args:
        graph_defs = get_graph_defs_from_file_paths(
            file_paths=file_paths,
            out_sub_dir=out_sub_dir
        )
    elif "--puml" in args:
        graph_defs = {}
        for file_path in file_paths:
            graph_defs |= get_graph_defs_from_puml_file(
                file_path,
                out_sub_dir
            )

    for output_path_prefix, graph_def in graph_defs.items():
        graph_sols = get_graph_sols_for_graph_def(
            graph_def=graph_def,
            num_loops=num_loops,
            num_branches=num_branches
        )
        audit_event_sequences_event_ids = get_audit_event_jsons_and_templates(
            graph_sols,
            is_template=False,
            job_name=job_name,
            return_plots=return_plots
        )
        handle_sequence_and_plot_output(
            audit_event_sequences_event_ids=audit_event_sequences_event_ids,
            output_path_prefix=output_path_prefix,
            save_fig=save_fig
        )


def get_arg_value(
    args: list[str],
    arg: str
) -> str:
    """Function to get the value of an argument

    :param args: List of arguments passed to command line
    :type args: `list`[`str`]
    :param arg: The argument to be found
    :type arg: `str`
    :return: Returns the string value of the argument
    :rtype: `str`
    """
    index = args.index(arg)
    return args[index + 1]


def get_graph_defs_from_puml_file(
    puml_file_path: str,
    out_sub_dir: Optional[str] = None
) -> dict:
    """Method to get graph defs from a single puml file

    :param puml_file_path: The file path of the puml file
    :type puml_file_path: `str`
    :param out_sub_dir: An optional out sub directory, defaults to `None`
    :type out_sub_dir: :class:`Optional`[`str`], optional
    :return: Dictionary of graph defs with output path prefix as keys
    :rtype: `dict`
    """
    # get output path prefix
    output_path_prefix = get_output_path_prefix(
        puml_file_path,
        out_sub_dir
    )
    output_path_prefix = os.path.split(output_path_prefix)[0]
    # load puml file
    with open(puml_file_path, 'r', encoding="utf8") as file:
        puml_file = file.read()
    # get graph_defs
    graph_defs = get_graph_defs_from_puml(puml_file)
    graph_defs = {
        os.path.join(output_path_prefix, name): graph_def
        for name, graph_def in graph_defs.items()
    }
    return graph_defs


def get_graph_defs_from_file_paths(
    file_paths: list[str],
    out_sub_dir: Optional[str] = None
) -> dict:
    """Function to load all graph definitions from the list of file paths and
    provide a mapping from an output path prefix to those loaded files

    :param file_paths: List of file paths
    :type file_paths: `list`[`str`]
    :param out_sub_dir: The output subdirectory, defaults to `None`
    :type out_sub_dir: :class:`Optional`[`str`], optional
    :return: Returns a dictionary mapping output path prefix to json file
    :rtype: `dict`
    """
    graph_defs = {}
    for file_path in file_paths:
        output_path_prefix = get_output_path_prefix(
            file_path=file_path,
            out_sub_dir=out_sub_dir
        )
        with open(file_path, 'r', encoding="utf8") as file:
            graph_defs[output_path_prefix] = json.load(file)
    return graph_defs


def get_output_path_prefix(
    file_path: str,
    out_sub_dir: Optional[str] = None
) -> str:
    """Function to get the output path prefix given a file path and
    (optionally) an output sub directory

    :param file_path: The path of the input file
    :type file_path: `str`
    :param out_sub_dir: Optional output subdirectory to place files in
    (creates if directory doesn't exist), defaults to `None`
    :type out_sub_dir: :class:`Optional`[`str`], optional
    :raises RuntimeError: Raises a :class:`RuntimeError` if the file does not
    indicate it is json or puml.
    :return: Returns the output path prefix that files will be saved to
    :rtype: `str`
    """
    if ".json" not in file_path and ".puml" not in file_path:
        raise RuntimeError("File must be of json  or puml type")
    if ".json" in file_path:
        output_path_prefix = file_path.split(".json")[0]
    else:
        output_path_prefix = file_path.split(".puml")[0]
    # if there is an output subdirectory update the pathing
    if out_sub_dir:
        path_split = os.path.split(output_path_prefix)
        output_path_prefix = os.path.join(
            path_split[0],
            out_sub_dir,
        )
        # if the directory doesn't exist make it
        if not os.path.isdir(output_path_prefix):
            os.mkdir(output_path_prefix)
        output_path_prefix = os.path.join(
            output_path_prefix,
            path_split[1],
        )
    return output_path_prefix


def get_graph_sols_for_graph_def(
    graph_def: dict,
    num_loops: int,
    num_branches: int
) -> list[GraphSolution]:
    """Function to get list of :class:`GraphSolution` from an input graph_def

    :param graph_def: Standardised graph definition
    :type graph_def: `dict`
    :param num_loops: Number of loops in expansion
    :type num_loops: `int`
    :param num_branches: Number of branches in expansion
    :type num_branches: `int`
    :return: Returns a list of the :class:`GraphSolution` combinations
    :rtype: `list`[:class:`GraphSolution`]
    """
    graph = Graph()
    graph.parse_graph_def(graph_def)
    graph.solve()
    graph_sols = graph.get_all_combined_graph_solutions(
        num_loops=num_loops,
        num_branches=num_branches
    )
    return graph_sols


def save_sequence_files(
    audit_event_sequence_json: list[dict],
    output_path_prefix: str,
    sequence_num: int
) -> None:
    """Function to save sequence files

    :param audit_event_sequence_json: List of dictionaries of an audit event
    sequence
    :type audit_event_sequence_json: `list`[`dict`]
    :param output_path_prefix: The output path prefix to save the file under
    :type output_path_prefix: `str`
    :param sequence_num: The number of the sequence
    :type sequence_num: `int`
    """
    with open(
        f"{output_path_prefix}_sequence_{sequence_num}.json",
        'w',
        encoding="utf8"
    ) as file:
        json.dump(audit_event_sequence_json, file, indent=4)


def handle_plots(
    audit_event_sequence_plot: Optional[Figure],
    output_path_prefix: str,
    save_fig: bool,
    sequence_num: int
) -> None:
    """Function to handle plotting of and audit event sequence if the input
    :class:`Figure` instance exists

    :param audit_event_sequence_plot: :class:`Figure` instance that holds the
    plot
    :type audit_event_sequence_plot: :class:`Optional`[:class:`Figure`]
    :param output_path_prefix: The output path prefix under which to save the
    file
    :type output_path_prefix: `str`
    :param save_fig: Boolean indicating whether to save the plot or not
    :type save_fig: `bool`
    :param sequence_num: The number of the audit event sequence
    :type sequence_num: `int`
    """
    if audit_event_sequence_plot:
        if save_fig:
            audit_event_sequence_plot.savefig(
                f"{output_path_prefix}_sequence_{sequence_num}.png"
            )
        audit_event_sequence_plot.show()
        plt.show()


def handle_sequence_and_plot_output(
    audit_event_sequences_event_ids: list[
        tuple[list[dict], list[str], Figure | None]
    ],
    output_path_prefix: str,
    save_fig: bool
) -> None:
    """Function to handle the saving of sequence files and output of plots
    from a given list of tuples with list of sequences, list of event ids and
    an optional :class:`Figure` instance

    :param audit_event_sequences_event_ids: list of tuples with list of
    sequences, list of event ids and an optional :class:`Figure` instance
    :type audit_event_sequences_event_ids: `list`[ `tuple`[`list`[`dict`],
    `list`[`str`], :class:`Figure`  |  `None`] ]
    :param output_path_prefix: The output path prefix
    :type output_path_prefix: `str`
    :param save_fig: Boolean indicating whether to save a figure or not
    :type save_fig: `bool`
    """
    for i, audit_event_sequence_event_ids in enumerate(
        audit_event_sequences_event_ids
    ):
        save_sequence_files(
            audit_event_sequence_json=audit_event_sequence_event_ids[0],
            output_path_prefix=output_path_prefix,
            sequence_num=i + 1
        )
        handle_plots(
            audit_event_sequence_plot=audit_event_sequence_event_ids[2],
            output_path_prefix=output_path_prefix,
            save_fig=save_fig,
            sequence_num=i + 1
        )


if __name__ == "__main__":
    import sys
    main(sys.argv)

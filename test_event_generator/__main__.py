# pylint: disable=R0913
"""Main function for running from command line
"""
import json
import os
from typing import Optional, Iterable, Generator, Any

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from test_event_generator.io.run import get_graph_def_test_events
from test_event_generator import puml_file_to_test_events


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
    out_dir = "./"
    save_fig = False
    invalid = False
    # check command line options
    if "--numloops" in args:
        num_loops = int(get_arg_value(args, "--numloops"))
    if "--numbranches" in args:
        num_branches = int(get_arg_value(args, "--numbranches"))
    if "--outdir" in args:
        out_dir = get_arg_value(args, "--outdir")
    if "--saveplot" in args:
        save_fig = True
    if "--invalid" in args:
        invalid = True
    options = {
        "is_template": False,
        "return_plots": save_fig,
        "num_loops": num_loops,
        "num_branches": num_branches,
        "invalid": invalid
    }
    if "--graphdef" in args:
        jobs_test_events = {}
        graph_defs = get_graph_defs_from_file_paths(
            file_paths
        )
        for out_path_prefix, graph_def in graph_defs:
            job_def_name = os.path.split(out_path_prefix)[1]
            jobs_test_events[job_def_name] = get_graph_def_test_events(
                graph_def,
                job_def_name,
                **options
            )

    elif "--puml" in args:
        jobs_test_events = {}
        for file_path in file_paths:
            jobs_test_events |= puml_file_to_test_events(
                file_path,
                **options
            )

    handle_jobs_categorised_audit_event_sequences(
        jobs_test_events,
        output_path=out_dir,
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


def save_sequence_files(
    audit_event_sequence_json: list[dict],
    output_path_prefix: str,
    sequence_num: int
) -> str:
    """Function to save sequence files

    :param audit_event_sequence_json: List of dictionaries of an audit event
    sequence
    :type audit_event_sequence_json: `list`[`dict`]
    :param output_path_prefix: The output path prefix to save the file under
    :type output_path_prefix: `str`
    :param sequence_num: The number of the sequence
    :type sequence_num: `int`
    :return: Returns file name
    :rtype: `str`
    """
    file_path = f"{output_path_prefix}_sequence_{sequence_num}.json"
    with open(
        file_path,
        'w',
        encoding="utf8"
    ) as file:
        json.dump(audit_event_sequence_json, file, indent=4)
    file_name = os.path.split(file_path)[1]
    return file_name


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
            plt.close(audit_event_sequence_plot)


def handle_sequence_and_plot_output(
    audit_event_sequences_event_ids: Iterable[
        tuple[list[dict], list[str], Figure | None, str]
    ],
    output_path_prefix: str,
    save_fig: bool,
    job_name_category_valid: tuple[str, str, bool]
) -> None:
    """Function to handle the saving of sequence files and output of plots
    from a given list of tuples with list of sequences, list of event ids and
    an optional :class:`Figure` instance

    :param audit_event_sequences_event_ids: list of tuples with list of
    sequences, list of event ids and an optional :class:`Figure` instance and
    job id
    :type audit_event_sequences_event_ids:
    :class:`Iterable`[`tuple`[`list`[`dict`], `list`[`str`], :class:`Figure`
    |  `None`], `str`]
    :param output_path_prefix: The output path prefix
    :type output_path_prefix: `str`
    :param save_fig: Boolean indicating whether to save a figure or not
    :type save_fig: `bool`
    :param job_name_category_valid: Tuple containing job name, category and
    validity
    :type job_name_category_valid: `tuple`[`str, `str`, `bool`]
    """
    job_ids = []
    file_names = []
    for i, audit_event_sequence_event_ids in enumerate(
        audit_event_sequences_event_ids
    ):
        file_name = save_sequence_files(
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
        job_ids.append(audit_event_sequence_event_ids[3])
        file_names.append(file_name)
    # create job id validity dataframe
    job_id_validity_df = pd.DataFrame(
        list(zip(
            file_names
            [job_name_category_valid[0]] * len(job_ids),
            [job_name_category_valid[1]] * len(job_ids),
            [job_name_category_valid[2]] * len(job_ids),
            job_ids
        )),
        columns=["FileName", "JobName", "Category", "Validity", "JobId"]
    )
    return job_id_validity_df


def handle_jobs_categorised_audit_event_sequences(
    jobs_categorised_audit_event_sequences: dict[str, dict],
    output_path: str,
    save_fig: bool = False
):
    """Method to handle output from generated job specific categorised test
    event sequences

    :param jobs_categorised_audit_event_sequences: Dictionary with keys as job
    names and values a categorised test event sequences
    :type jobs_categorised_audit_event_sequences: `dict`[`str`, `dict`]
    :param output_path: The path of the output directory
    :type output_path: `str`
    :param save_fig: Boolean indicating to save figures, defaults to `False`
    :type save_fig: `bool`, optional
    """
    for job_name, categorised_audit_event_sequences in (
        jobs_categorised_audit_event_sequences.items()
    ):
        handle_job_categorised_audit_event_sequences(
            categorised_audit_event_sequences,
            output_path,
            job_name,
            save_fig
        )


def handle_job_categorised_audit_event_sequences(
    categorised_audit_event_sequences: dict[
        str,
        tuple[tuple[Generator[tuple[
            list[dict], list[str], plt.Figure | None, str
        ], Any, None], bool]]
    ],
    output_path: str,
    job_name: str,
    save_fig: bool = False,
):
    """Method to handle the output of categorised test event sequences

    :param categorised_audit_event_sequences: Categorised test event sequences
    :type categorised_audit_event_sequences: `dict`[ `str`,
    `tuple`[`tuple`[:class:`Generator`[`tuple`[ `list`[`dict`], `list`[`str`],
    :class:`plt.Figure`  |  `None`,
    `str` ], `Any`, `None`], `bool`]] ]
    :param output_path: The path of the output directory
    :type output_path: `str`
    :param job_name: The name of the job
    :type job_name: `str`
    :param save_fig: Boolean indicating to save figures, defaults to `False`
    :type save_fig: `bool`, optional
    """
    validity_dfs = []
    for category, data in categorised_audit_event_sequences.items():
        output_path_prefix = os.path.join(
            output_path,
            "_".join((job_name, category, "valid" if data[1] else "invalid"))
        )
        validity_df = handle_sequence_and_plot_output(
            data[0],
            save_fig=save_fig,
            job_name_category_valid=(job_name, category, data[1]),
            output_path_prefix=output_path_prefix
        )
        validity_dfs.append(validity_df)
    job_validity_df = pd.concat(validity_dfs, ignore_index=True)
    job_validity_df.to_csv(
        os.path.join(
            output_path,
            f"{job_name}_validity_df.csv"
        ),
        index=False
    )


if __name__ == "__main__":
    import sys
    main(sys.argv)

"""
Utility functions
"""
from __future__ import annotations
from typing import Union, TYPE_CHECKING

from pandas import DataFrame, concat
from ortools.sat.python.cp_model import (
    CpSolverSolutionCallback, IntVar, CpModel, CpSolver
)
if TYPE_CHECKING:
    from ..core.edge import Edge
    from ..core.group import Group


class SolutionStore(CpSolverSolutionCallback):
    """Store solutions."""

    def __init__(self, variables: list[IntVar]) -> None:
        """Store solutions that satisfy constraints in CP-SAT model

        :param variables: List of IntVar variables
        :type variables: `list`[:class:`IntVar`]
        """
        super().__init__()
        self.store: list[dict[str, int]] = []
        self.__variables = variables
        self.__solution_count = 0

    def on_solution_callback(self) -> None:
        """Implementation of abstract method for parent class.
        Stores solutions in dictionary with key as the count and variables
        given by their name.
        """
        solutions = {}
        self.__solution_count += 1
        for variable in self.__variables:
            solutions[variable.Name()] = self.Value(variable)
        self.store.append(solutions)

    def solution_count(self) -> int:
        """Getter method to return the solution count.

        :return: The number of solutions found.
        :rtype: int
        """
        return self.__solution_count

    @property
    def solutions_df(self) -> DataFrame:
        """Property defined by converting store into :class:`DataFrame`.

        :return: Returns a dataframe with variables as indexes and solution
        number as columns.
        :rtype: :class:`DataFrame`
        """
        return solutions_to_df(self.store)


def solve_model(
    model: CpModel,
    solver: CpSolver,
    variables: list[IntVar]
) -> list[dict[str, int]]:
    """Solve a CP-SAT model and return all valid solutions for all provided
    variables satisfying the constraints of the model

    :param model: CP-SAT model
    :type model: :class:`CpModel`
    :param solver: The CP-SAT solver class with which to solve the model
    :type solver: :class:`CpSolver`
    :param variables: List of CP-SAT variables to return solutions for
    :type variables: `list`[:class:`IntVar`]
    :return: Returns a list with solution number as key and a dictionary
    providing the values of the variables
    :rtype: `list`[`dict`[`str`, `int`]]
    """
    solution_store = SolutionStore(variables=variables)
    solver.parameters.enumerate_all_solutions = True
    solver.Solve(model=model, solution_callback=solution_store)
    return solution_store.store


def solutions_to_df(solutions: list[dict[str, int]]) -> DataFrame:
    """Creates a :class:`DataFrame` from the input solutions

    :param solutions: List of solutions containing dictionary with format:
    key = variable uid, value = variable value
    :type solutions: `list`[`dict`[`str`, `int`]]
    :return: Returns a dataframe with variables as indexes and solution
    number as columns.
    :rtype: :class:`DataFrame`
    """
    return DataFrame.from_records(solutions).T


def combine_separated_solutions(
    *separated_solutions: DataFrame
) -> DataFrame:
    """Combine :class:`DataFrame`'s of solutions into single
    :class:`DataFrame`. The :class:`DataFrame`'s must have the same number of
    columns.

    :raises :class:`RuntimeError`: Raises error if DataFrame's don't have the
    same number of columns
    :return: Returns a concatenated DataFrame
    :rtype: :class:`DataFrame`
    """
    # check all list are of equal length
    if all([
        len(
            separated_solutions[i].columns
        ) - len(
            separated_solutions[i + 1].columns
        ) == 0
        for i in range(len(separated_solutions) - 1)
    ]):
        return concat(separated_solutions)
    else:
        raise RuntimeError("All input DataFrame's must be of the same length.")


def add_solution_type_column(
    solutions_df: DataFrame,
    types: dict[str, list[str]]
) -> None:
    """Add a "Type" column to a dataframe with indices specified by uids.

    :param solutions_df: :class:`DataFrame` with solutions.
    :type solutions_df: :class:`DataFrame`
    :param types: Dictionary with keys as the "Type" to be input into the
    :class:`DataFrame` and values a list of uids that are indices in the
    :class:`DataFrame`.
    :type types: `dict`[`str`, `list`[`str`]]
    """
    solutions_df["Type"] = "Default"
    for type_string, uids in types.items():
        solutions_df.loc[uids, "Type"] = type_string


class SolutionStoreCore(CpSolverSolutionCallback):
    """Store solutions of CP-SAT model for core variables.

    :param core_variables: Dictionary of core variables with Type as key
    and values as list of the Type of core variable.
    :type core_variables: `dict`[`str`,
    :class:`Union`[`list`[:class:`Edge`], `list`[:class:`Group`]]]
    """
    def __init__(
        self,
        core_variables: dict[str, Union[list[Edge], list[Group]]]
    ) -> None:
        """Constructor method.
        """
        super().__init__()
        self.__variables = core_variables
        self.store: dict[str, list[dict[str, int]]] = {
            key: [] for key in core_variables.keys()
        }
        self.__solution_count = 0

    def on_solution_callback(self) -> None:
        """Implementation of abstract method for parent class.
        Stores solutions in dictionary with key as the count and variables
        given by their name.
        """
        self.__solution_count += 1
        for core_variable_type, core_variables in self.__variables.items():
            self.store[core_variable_type].append(
                self.get_solutions(core_variables)
            )

    def get_solutions(
        self,
        variables: Union[list[Edge], list[Group]]
    ) -> dict[str, int]:
        """Extracts solutions from core variables internal :class:`IntVar`.

        :param variables: List of core variables
        :type variables: :class:`Union`[`list`[:class:`Edge`],
        `list`[:class:`Group`]]
        :return: Returns a dictionary with key as the uid of the core variable
        and value as the internal :class:`IntVar` value of the core variable.
        :rtype: `dict`[`str`, `int`]
        """
        solutions = {}
        for variable in variables:
            solutions[variable.uid] = self.Value(variable.variable)
        return solutions

    def solution_count(self) -> int:
        """Getter method to return the solution count.

        :return: The number of solutions found.
        :rtype: int
        """
        return self.__solution_count


def solve_model_core(
    model: CpModel,
    solver: CpSolver,
    core_variables: dict[str, Union[list[Edge], list[Group]]]
) -> dict[str, list[dict[str, int]]]:
    """Solve a CP-SAT model and return all valid solutions for all provided
    variables satisfying the constraints of the model

    :param model: CP-SAT model
    :type model: :class:`CpModel`
    :param solver: The CP-SAT solver class with which to solve the model
    :type solver: :class:`CpSolver`
    :param core_variables: Dictionary of core variables with Type as key
    and values as list of the Type of core variable.
    :type core_variables: `dict`[`str`,
    :class:`Union`[`list`[:class:`Edge`], `list`[:class:`Group`]]]
    :return: Returns a dictionary of solutions with different core
    variable types as keys and values as  list of dictionaries with the core
    variables uids as keys and solutions values as values.
    :rtype: `dict`[`str`, `list`[`dict`[`str`, `int`]]]
    """
    solution_store = SolutionStoreCore(core_variables=core_variables)
    solver.parameters.enumerate_all_solutions = True
    solver.Solve(model=model, solution_callback=solution_store)
    return solution_store.store

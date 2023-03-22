"""
Utility functions
"""
from ortools.sat.python.cp_model import (
    CpSolverSolutionCallback, IntVar, CpModel, CpSolver
)


class SolutionStore(CpSolverSolutionCallback):
    """Store solutions."""

    def __init__(self, variables: list[IntVar]) -> None:
        """Store solutions that satisfy constraints in CP-SAT model

        :param variables: List of IntVar variables
        :type variables: `list`[:class:`IntVar`]
        """
        super().__init__()
        self.store: dict[int, dict[str, int]] = {}
        self.__variables = variables
        self.__solution_count = 0

    def on_solution_callback(self) -> None:
        """Implementation of abstract method for parent class.
        Stores solutions in dictionary with key as the count and variables
        given by their name.
        """
        self.store[self.__solution_count] = {}
        solutions = self.store[self.__solution_count]
        self.__solution_count += 1
        for varaible in self.__variables:
            solutions[varaible.Name()] = self.Value(varaible)

    def solution_count(self) -> int:
        """Getter method to return the solution count.

        :return: The number of solutions found.
        :rtype: int
        """
        return self.__solution_count


def solve_model(
    model: CpModel,
    solver: CpSolver,
    variables: list[IntVar]
) -> dict[int, dict[str, int]]:
    """Solve a CP-SAT model and return all valid solutions for all provided
    variables satisfying the constraints of the model

    :param model: CP-SAT model
    :type model: :class:`CpModel`
    :param solver: The CP-SAT solver class with which to solve the model
    :type solver: :class:`CpSolver`
    :param variables: List of CP-SAT variables to return solutions for
    :type variables: `list`[:class:`IntVar`]
    :return: Returns a dictionary with solution number as key and a dictionary
    providing the values of the variables
    :rtype: dict[int, dict[str, int]]
    """
    solution_store = SolutionStore(variables=variables)
    solver.parameters.enumerate_all_solutions = True
    solver.Solve(model=model, solution_callback=solution_store)
    return solution_store.store

from typing import Literal
import pytest
from tests.test_event_generator.solutions.conftest import (  # noqa: F401
    graph_simple,
    event_solution,
    prev_event_solution,
    post_event_solution
)


@pytest.fixture
def bunched_xor_puml(
) -> Literal['@startuml\npartition "bunched_XOR_switch" {\n    gro…']:
    """Fixture provding a raw string puml file for bunched XOR constraints on
    an event

    :return: Returns a string representing the puml
    :rtype: `str`
    """
    return (
        '@startuml\npartition "bunched_XOR_switch" {\n    group '
        '"bunched_XOR_switch"\n        #GREEN :A;\n        switch (XOR)\n     '
        '       case ("1")\n\n            if () then (true)\n                '
        'if (XOR) then (true)\n                    :H;\n                else ('
        'false)\n                    :I;\n                endif\n            '
        'else (false)\n                :D;\n            endif\n            '
        'case ("2")\n            if (XOR) then (true)\n                :E;\n'
        '            else (false)\n                :J;\n            endif\n'
        '            case ("3")\n            :G;\n            :M;\n        '
        'endswitch\n        :F;\n    end group\n}\n@enduml'
    )


@pytest.fixture
def bunched_xor_graph_def(
) -> dict[str, dict]:
    """Fixture providing the graph def equivalent to `bunched_xor_puml`

    :return: Returns the graph definition
    :rtype: `dict`[`str`, `dict`]
    """
    return {
        "A_0": {
            "group_in": None,
            "group_out": {
                "type": "XOR",
                "sub_groups": [
                    {
                        "type": "XOR",
                        "sub_groups": [
                            {
                                "type": "XOR",
                                "sub_groups": [
                                    "A_0->H_0",
                                    "A_0->I_0"
                                ]
                            },
                            "A_0->D_0"
                        ]
                    },
                    {
                        "type": "XOR",
                        "sub_groups": [
                            "A_0->E_0",
                            "A_0->J_0"
                        ]
                    },
                    "A_0->G_0",
                ]
            },
            "meta_data": {
                "EventType": "A"
            }
        },
        "H_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "A_0->H_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "H_0->F_0"
                ]
            },
            "meta_data": {
                "EventType": "H"
            }
        },
        "I_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "A_0->I_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "I_0->F_0"
                ]
            },
            "meta_data": {
                "EventType": "I"
            }
        },
        "D_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "A_0->D_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "D_0->F_0"
                ]
            },
            "meta_data": {
                "EventType": "D"
            }
        },
        "E_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "A_0->E_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "E_0->F_0"
                ]
            },
            "meta_data": {
                "EventType": "E"
            }
        },
        "J_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "A_0->J_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "J_0->F_0"
                ]
            },
            "meta_data": {
                "EventType": "J"
            }
        },
        "G_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "A_0->G_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "G_0->M_0"
                ]
            },
            "meta_data": {
                "EventType": "G"
            }
        },
        "M_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "G_0->M_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "M_0->F_0"
                ]
            },
            "meta_data": {
                "EventType": "M"
            }
        },
        "F_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "H_0->F_0",
                    "I_0->F_0",
                    "D_0->F_0",
                    "E_0->F_0",
                    "J_0->F_0",
                    "M_0->F_0",
                ]
            },
            "group_out": None,
            "meta_data": {
                "EventType": "F"
            }
        }
    }


@pytest.fixture
def ANDFork_loop_puml(
) -> Literal['@startuml\npartition "ANDFork_loop_a" {\n    group "…']:
    """Fixture provding a raw string puml file for ANDFork with a nested loop
    an event

    :return: Returns a string representing the puml
    :rtype: `str`
    """
    return (
        '@startuml\npartition "ANDFork_loop_a" {\n    group "ANDFork_loop_a"\n'
        '        #green:A;\n        fork\n            :B;\n            repeat'
        '\n                :D;\n            repeat while\n        fork again\n'
        '            :C;\n        end fork\n        #red:E;\n    end group\n}'
        '\n@enduml'
    )


@pytest.fixture
def ANDFork_loop_graph_def() -> dict[str, dict]:
    """Fixture providing the graph def equivalent to `ANDFork_loop_puml`

    :return: Returns the graph definition
    :rtype: `dict`[`str`, `dict`]
    """
    return {
        "A_0": {
            "group_in": None,
            "group_out": {
                "type": "AND",
                "sub_groups": [
                    "A_0->B_0",
                    "A_0->C_0"
                ]
            },
            "meta_data": {
                "EventType": "A"
            }
        },
        "B_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "A_0->B_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "B_0->Loop_0"
                ]
            },
            "meta_data": {
                "EventType": "B"
            }
        },
        "C_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "A_0->C_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "C_0->E_0"
                ]
            },
            "meta_data": {
                "EventType": "C"
            }
        },
        "Loop_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "B_0->Loop_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "Loop_0->E_0"
                ]
            },
            "meta_data": {
                "EventType": "Loop"
            },
            "loop_graph": {
                "D_0": {
                    "group_in": None,
                    "group_out": None,
                    "meta_data": {
                        "EventType": "D"
                    }
                }
            }
        },
        "E_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "C_0->E_0",
                    "Loop_0->E_0"
                ]
            },
            "group_out": None,
            "meta_data": {
                "EventType": "E"
            }
        }
    }


@pytest.fixture
def loop_loop_puml(
) -> Literal['@startuml\npartition "loop_loop_a" {\n    group "loo…']:
    """Fixture to provide a puml file with a nested loop

    :return: Returns a string of the puml file
    :rtype: `str`
    """
    return (
        '@startuml\npartition "loop_loop_a" {\n    group "loop_loop_a"\n'
        '        #green:A;\n        repeat\n            :B;\n            '
        'repeat\n                :C;\n            repeat while\n'
        '            :D;\n        repeat while\n        #red:E;\n'
        '    end group\n}\n@enduml'
    )


@pytest.fixture
def loop_loop_graph_def(
):
    return {
        "A_0": {
            "group_in": None,
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "A_0->Loop_0"
                ]
            },
            "meta_data": {
                "EventType": "A"
            }
        },
        "Loop_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "A_0->Loop_0"
                ]
            },
            "group_out": {
                "type": "OR",
                "sub_groups": [
                    "Loop_0->E_0"
                ]
            },
            "meta_data": {
                "EventType": "Loop"
            },
            "loop_graph": {
                "B_0": {
                    "group_in": None,
                    "group_out": {
                        "type": "OR",
                        "sub_groups": [
                            "B_0->Loop_1"
                        ]
                    },
                    "meta_data": {
                        "EventType": "B"
                    }
                },
                "Loop_1": {
                    "group_in": {
                        "type": "OR",
                        "sub_groups": [
                            "B_0->Loop_1"
                        ]
                    },
                    "group_out": {
                        "type": "OR",
                        "sub_groups": [
                            "Loop_1->D_0"
                        ]
                    },
                    "meta_data": {
                        "EventType": "Loop"
                    },
                    "loop_graph": {
                        "C_0": {
                            "group_in": None,
                            "group_out": None,
                            "meta_data": {
                                "EventType": "C"
                            }
                        }
                    }
                },
                "D_0": {
                    "group_in": {
                        "type": "OR",
                        "sub_groups": [
                            "Loop_0->D_0"
                        ]
                    },
                    "group_out": None,
                    "meta_data": {
                        "EventType": "D"
                    }
                }
            }
        },
        "E_0": {
            "group_in": {
                "type": "OR",
                "sub_groups": [
                    "Loop_0->E_0"
                ]
            },
            "group_out": None,
            "meta_data": {
                "EventType": "E"
            }
        }
    }

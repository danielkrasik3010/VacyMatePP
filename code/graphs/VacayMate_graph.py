
from typing import Any, Dict
from langgraph.graph import StateGraph, START, END
import sys
import os

# Add the parent directory to the path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Import statements that work both as module and when run directly
try:
    # Try relative imports first (when used as module)
    from ..states import VacationPlannerState
    from ..consts import (
        MANAGER,
        RESEARCHER,
        CALCULATOR,
        PLANNER,
        SUMMARIZER,
    )
    from ..nodes import (
        make_manager_node,
        make_researcher_node,
        make_calculator_node,
        make_planner_node,
        make_summarizer_node,
    )
except ImportError:
    # Fall back to absolute imports (when run directly)
    from states import VacationPlannerState
    from consts import (
        MANAGER,
        RESEARCHER,
        CALCULATOR,
        PLANNER,
        SUMMARIZER,
    )
    from nodes import (
        make_manager_node,
        make_researcher_node,
        make_calculator_node,
        make_planner_node,
        make_summarizer_node,
    )


def build_vacation_graph(config: Dict[str, Any]) -> StateGraph:
    """
    Build the VacationPlanner agent workflow graph.
    Flow:
        Manager -> Researcher -> (Calculator + Planner in parallel) -> Summarizer -> END
    """
    graph = StateGraph(VacationPlannerState)

    # ---------------------- ADD NODES ----------------------
    manager_node = make_manager_node(llm_model=config["agents"][MANAGER]["llm"])
    graph.add_node(MANAGER, manager_node)

    researcher_node = make_researcher_node(llm_model=config["agents"][RESEARCHER]["llm"])
    graph.add_node(RESEARCHER, researcher_node)

    calculator_node = make_calculator_node(llm_model=config["agents"][CALCULATOR]["llm"])
    graph.add_node(CALCULATOR, calculator_node)

    planner_node = make_planner_node(llm_model=config["agents"][PLANNER]["llm"])
    graph.add_node(PLANNER, planner_node)

    summarizer_node = make_summarizer_node(llm_model=config["agents"][SUMMARIZER]["llm"])
    graph.add_node(SUMMARIZER, summarizer_node)

    # ---------------------- ADD EDGES ----------------------
    graph.add_edge(START, MANAGER)
    graph.add_edge(MANAGER, RESEARCHER)
    # Both Calculator and Planner run in parallel after Researcher
    graph.add_edge(RESEARCHER, CALCULATOR)
    graph.add_edge(RESEARCHER, PLANNER)
    # Summarizer waits for both Calculator and Planner to complete
    graph.add_edge(CALCULATOR, SUMMARIZER)
    graph.add_edge(PLANNER, SUMMARIZER)
    graph.add_edge(SUMMARIZER, END)

    # ---------------------- COMPILE ------------------------
    return graph.compile()

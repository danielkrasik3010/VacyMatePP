# graph.py

from typing import Any, Dict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.nodes import Parallel

from state import VacationPlannerState
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

    # Parallel wrapper for Planner + Calculator
    graph.add_node("parallel_tasks", Parallel([CALCULATOR, PLANNER]))

    # ---------------------- ADD EDGES ----------------------
    graph.add_edge(START, MANAGER)
    graph.add_edge(MANAGER, RESEARCHER)

    # researcher → planner & calculator in parallel
    graph.add_edge(RESEARCHER, "parallel_tasks")

    # once both done → summarizer
    graph.add_edge("parallel_tasks", SUMMARIZER)

    # summarizer → END
    graph.add_edge(SUMMARIZER, END)

    # ---------------------- COMPILE ------------------------
    return graph.compile()
from typing import Any, Dict
from langgraph.graph import StateGraph, START, END
import sys
import os

# Make sure the repository root (parent of "code") is on sys.path when running.
# This helps absolute imports like "from code.states..." work reliably when running as a module.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Prefer absolute package imports
from states.VacayMate_state import VacationPlannerState
from consts import (
    MANAGER,
    RESEARCHER,
    CALCULATOR,
    PLANNER,
    SUMMARIZER,
    MERGE_RESULTS,
)
from nodes.VacayMate_nodes import (
    make_manager_node,
    make_researcher_node,
    make_calculator_node,
    make_planner_node,
    make_summarizer_node,
    make_merge_node,
)


def build_vacation_graph(config: Dict[str, Any]) -> StateGraph:
    """
    Build the VacationPlanner agent workflow graph.

    Flow:
        START -> Manager -> Researcher -> (Calculator + Planner in parallel)
        -> MERGE -> Summarizer -> END
    """
    graph = StateGraph(VacationPlannerState)

    # Use the same variables as the config for readability
    llm = config["llm"]
    tools = config["tools"]
    prompt_cfg = config["prompt_config"]

    # ---------------------- ADD NODES ----------------------
    manager_node = make_manager_node(llm=llm, prompt_cfg=prompt_cfg)
    graph.add_node(MANAGER, manager_node)

    researcher_node = make_researcher_node(llm=llm, tools=tools, prompt_cfg=prompt_cfg)
    graph.add_node(RESEARCHER, researcher_node)

    calculator_node = make_calculator_node(llm=llm, tools=tools, prompt_cfg=prompt_cfg)
    graph.add_node(CALCULATOR, calculator_node)

    planner_node = make_planner_node(llm=llm, tools=tools, prompt_cfg=prompt_cfg)
    graph.add_node(PLANNER, planner_node)

    # Use the new make_merge_node function
    merge_node = make_merge_node(llm=llm, tools=tools, prompt_cfg=prompt_cfg)
    graph.add_node(MERGE_RESULTS, merge_node)
    
    summarizer_node = make_summarizer_node(llm=llm, tools=tools, prompt_cfg=prompt_cfg)
    graph.add_node(SUMMARIZER, summarizer_node)

    # ---------------------- ADD EDGES ----------------------
    graph.add_edge(START, MANAGER)
    graph.add_edge(MANAGER, RESEARCHER)

    # Both Calculator and Planner run in parallel after Researcher
    graph.add_edge(RESEARCHER, CALCULATOR)
    graph.add_edge(RESEARCHER, PLANNER)

    # Both Calculator and Planner now feed into the MERGE node
    graph.add_edge(CALCULATOR, MERGE_RESULTS)
    graph.add_edge(PLANNER, MERGE_RESULTS)
    
    # The MERGE node feeds into the Summarizer
    graph.add_edge(MERGE_RESULTS, SUMMARIZER)
    
    graph.add_edge(SUMMARIZER, END)

    # ---------------------- COMPILE ------------------------
    return graph.compile()

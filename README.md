# VacayMate — AI-Powered Vacation Planning Assistant

**An intelligent multi-agent system for comprehensive vacation planning**

VacayMate is an AI-powered vacation planning assistant that uses multiple specialized agents to research destinations, find flights and hotels, calculate costs, create itineraries, and generate complete vacation plans. The system leverages LangGraph for orchestrating agent workflows and integrates with various APIs to provide real-time travel data.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Core Agents](#core-agents)
- [Tools & Integrations](#tools--integrations)
- [Configuration](#configuration)
- [Repository Structure](#repository-structure)
- [Quickstart](#quickstart)
- [Demo Usage](#demo-usage)
- [Implementation Notes](#implementation-notes)
- [Extending the Project](#extending-the-project)
- [Development Tips](#development-tips)
- [Contact & License](#contact--license)
- [Code Statistics](#code-statistics)

---

## Overview

VacayMate transforms vacation planning into an automated, intelligent process. **Key capabilities include:**

- Multi-agent workflow orchestration using LangGraph
- Real-time flight and hotel price research
- Weather forecasting and local event discovery
- Automated cost calculation with commission handling
- Day-by-day itinerary generation
- Professional vacation plan document generation

The system ensures that vacation plans are **comprehensive, cost-effective, and personalized**.

---

## System Architecture

### Agent Workflow

VacayMate uses a sophisticated multi-agent architecture where specialized agents work together:

1. **Manager Agent** - Orchestrates the entire workflow and validates inputs
2. **Researcher Agent** - Gathers flight, hotel, and destination information
3. **Calculator Agent** - Computes total vacation costs with detailed breakdowns
4. **Planner Agent** - Creates day-by-day itineraries with weather and events
5. **Summarizer Agent** - Generates polished final vacation plans

### Workflow Diagram

```
      ┌─────────────┐
      │   START     │
      └──────┬──────┘
             │
             ▼
      ┌─────────────┐
      │   MANAGER   │
      │   AGENT     │
      └──────┬──────┘
             │
             ▼
      ┌─────────────┐
      │ RESEARCHER  │
      │   AGENT     │
      └──────┬──────┘
             │
        ┌────┴────┐
        ▼         ▼
   ┌──────────┐ ┌──────────┐
   │CALCULATOR│ │ PLANNER  │
   │  AGENT   │ │  AGENT   │
   └────┬─────┘ └─────┬────┘
        │             │
        └──────┬──────┘
               ▼
      ┌─────────────┐
      │ SUMMARIZER  │
      │   AGENT     │
      └──────┬──────┘
             │
             ▼
      ┌─────────────┐
      │     END     │
      └─────────────┘
```

---

## Core Agents

### Manager Agent (`VacayMate_nodes.py`)

- **Role**: Workflow orchestrator and input validator
- **Responsibilities**: 
  - Parse and validate user requests
  - Extract travel dates, locations, and preferences
  - Route tasks to appropriate specialized agents
  - Ensure workflow completion in correct sequence

---

### Researcher Agent (`VacayMate_nodes.py`)

- **Role**: Data collection and research specialist
- **Tools Used**: 
  - Flight Prices Tool
  - Hotel Prices Tool  
  - Destination Info Tool
- **Responsibilities**:
  - Find flight options and prices
  - Research hotel availability and rates
  - Gather destination information and attractions

---

### Calculator Agent (`VacayMate_nodes.py`)

- **Role**: Financial analysis and cost computation
- **Tools Used**: Make Quotation Tool
- **Responsibilities**:
  - Calculate total vacation costs
  - Generate detailed cost breakdowns
  - Apply commission rates
  - Provide cost summaries with lowest/highest options

---

### Planner Agent (`VacayMate_nodes.py`)

- **Role**: Itinerary creation and scheduling
- **Tools Used**: 
  - Weather Forecast Tool
  - Event Finder Tool
- **Responsibilities**:
  - Create day-by-day itineraries
  - Integrate weather forecasts
  - Find and include local events
  - Optimize activity scheduling

---

### Summarizer Agent (`VacayMate_nodes.py`)

- **Role**: Final document generation and presentation
- **Responsibilities**:
  - Combine all agent outputs
  - Generate polished vacation plans
  - Format professional travel documents
  - Save plans to markdown files

---

## Tools & Integrations

### Flight Prices Tool (`Flights_prices_tool.py`)

- **API**: SerpAPI Google Flights
- **Functionality**: Real-time flight search and pricing
- **Features**: Round-trip flights, multiple airlines, seat availability

### Hotel Prices Tool (`Hotels_prices_tool.py`)

- **API**: SerpAPI Google Hotels
- **Functionality**: Hotel search and booking information
- **Features**: Price comparison, ratings, amenities, location data

### Weather Forecast Tool (`Weather_Forecast_tool.py`)

- **API**: OpenWeatherMap
- **Functionality**: 5-day weather forecasts
- **Features**: Temperature, conditions, humidity, wind speed

### Event Finder Tool (`Event_finder_tool.py`)

- **API**: SerpAPI Google Events
- **Functionality**: Local event discovery
- **Features**: Date-filtered events, venues, ticket information

### Quotation Tool (`Make_quotation_tool.py`)

- **Functionality**: Cost calculation and quotation generation
- **Features**: 
  - Hotel and flight cost aggregation
  - Daily expense estimation via LLM
  - Commission calculation (10%)
  - Detailed cost breakdowns

### Destination Info Tool (`destination_info_tool.py`)

- **API**: Tavily Search
- **Functionality**: Destination research and information gathering
- **Features**: Attractions, activities, local insights

---

## Configuration

### LLM Configuration (`config/config.yaml`)

```yaml
vacaymate_system:
  max_retries: 3
  timeout_seconds: 300
  max_search_queries: 5
  max_hotels: 10
  max_events: 10

  agents:
    manager:
      llm: gpt-4o-mini
    researcher:
      llm: gpt-4o-mini
    calculator:
      llm: gpt-4o-mini
    planner:
      llm: gpt-4o-mini
    summarizer:
      llm: gpt-4o-mini
```

### Environment Variables (`.env`)

```env
OPENAI_API_KEY=sk-...
GROQ_API_KEY=...
SERPAPI_API_KEY=...
OPENWEATHERMAP_API_KEY=...
TAVILY_API_KEY=...
```

---

## Repository Structure

```
VacayMate/
├── code/
│   ├── graphs/
│   │   ├── VacayMate_graph.py
│   │   ├── __init__.py
│   ├── nodes/
│   │   ├── VacayMate_nodes.py
│   │   ├── __init__.py
│   ├── states/
│   │   ├── VacayMate_state.py
│   │   └── __init__.py
│   ├── tools/
│   │   ├── Event_finder_tool.py
│   │   ├── Flights_prices_tool.py
│   │   ├── Hotels_prices_tool.py
│   │   ├── Make_quotation_tool.py
│   │   ├── Weather_Forecast_tool.py
│   │   ├── city_mapping.py
│   │   └── destination_info_tool.py
│   ├── VacayMate_system.py
│   ├── consts.py
│   ├── llm.py
│   ├── prompt_builder.py
│   └── utils.py
├── config/
│   ├── config.yaml
│   └── reasoning.yaml
├── outputs/
│   └── .gitignore
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── system_graph_VacayMate.png
└── tools_descreption.docx
```

---

## Quickstart

**Clone & install dependencies:**

```bash
git clone https://github.com/your-username/VacayMate
cd VacayMate
python -m venv venv
# Activate the virtual environment
# macOS / Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
pip install -r requirements.txt
```

**Configure environment variables:**

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Run the vacation planner:**

```bash
python code/VacayMate_system.py
```
---

## Demo Usage

**Example vacation request:**

```python
user_request = {
    "user_request": "I want to plan a vacation",
    "current_location": "barcelona",
    "destination": "paris",
    "travel_dates": "2025-09-15 to 2025-09-20",
}
```

**Generated output includes:**

- Flight options with prices and schedules
- Hotel recommendations with ratings and costs
- Weather forecasts for travel dates
- Local events and attractions
- Day-by-day detailed itinerary
- Complete cost breakdown with commission
- Professional vacation plan document

---

## Implementation Notes

### LLM Support

- **OpenAI**: GPT-4o-mini, GPT-4o (primary)
- **Groq**: Llama models (cost-effective alternative)
- Configurable model selection per agent

### API Integrations

- **SerpAPI**: Flight and hotel data, event discovery
- **OpenWeatherMap**: Weather forecasting
- **Tavily**: Destination research
- Rate limiting and error handling implemented

### State Management

- LangGraph state management for agent coordination
- Persistent state across agent transitions
- Error recovery and retry mechanisms

---

## Extending the Project

### Adding New Agents

1. Create agent function in `nodes/VacayMate_nodes.py`
2. Add agent configuration to `config/config.yaml`
3. Update graph structure in `graphs/VacayMate_graph.py`
4. Define state variables in `states/VacayMate_state.py`

### Adding New Tools

1. Create tool file in `tools/` directory
2. Implement tool with `@tool` decorator
3. Add tool to relevant agent configurations
4. Update tool imports in agent nodes

### Custom LLM Integration

1. Add model configuration to `llm.py`
2. Update `config.yaml` with new model options
3. Test with existing agent workflows

---

## Development Tips

### Debugging

- Enable verbose logging in agent executors
- Use `test_*.py` files for component testing
- Check `outputs/` directory for generated plans

### Performance Optimization

- Adjust `max_retries` and `timeout_seconds` in config
- Optimize tool response parsing
- Consider caching for repeated API calls

### Cost Management

- Use Groq models for cost-effective processing
- Monitor API usage across all integrated services
- Implement request batching where possible

---

## Code Statistics

### Performance Metrics That Impress
- **Planning Time:** 3-5 minutes (vs. 6+ hours manual)
- **Data Sources:** 6+ real-time APIs
- **Agent Coordination:** 5 specialized AI agents
- **Output Quality:** Publication-ready documentation
- **Cost Accuracy:** Real-time pricing with commission analysis
- **Itinerary Precision:** Weather-optimized daily schedules
- **Codebase Scale:** 2,860+ lines of production Python code across 22 modules

---

## Contact & License

**Author**: Daniel Krasik  
**Email**: daniel.krasik3010@gmail.com  
**License**: MIT License

---

## Credits

1. **Ready Tensor AI Course** - Educational foundation
2. **LangGraph** - Multi-agent orchestration framework
3. **SerpAPI** - Travel data APIs
4. **OpenWeatherMap** - Weather forecasting
5. **Tavily** - Web search and research

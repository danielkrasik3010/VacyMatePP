# 🌍 VacayMate - AI Travel Planner

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-green.svg)](https://langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4+-purple.svg)](https://langgraph.com)

VacayMate is an intelligent AI-powered travel planning system that creates comprehensive vacation itineraries by orchestrating multiple specialized agents. Built with LangGraph and featuring a beautiful Streamlit UI, it provides real-time flight prices, hotel recommendations, weather forecasts, local events, and detailed cost breakdowns.

## ✨ Features

### 🤖 Multi-Agent Architecture
- **Manager Agent**: Orchestrates the entire planning workflow
- **Researcher Agent**: Gathers flight, hotel, and destination data
- **Calculator Agent**: Provides detailed cost analysis and quotations
- **Planner Agent**: Creates itineraries with weather and events
- **Summarizer Agent**: Compiles everything into a comprehensive plan

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

### 🛠️ Core Capabilities
- ✈️ **Real-time Flight Search** - Live prices from multiple airlines with duration calculations
- 🏨 **Hotel Recommendations** - Detailed hotel data with real addresses and coordinates
- 🌍 **Dynamic Destination Research** - Attractions and activities specific to your destination
- 🌤️ **Weather Forecasting** - 5-day weather outlook for your trip
- 🎉 **Local Events Discovery** - Find events and activities during your stay
- 💰 **Comprehensive Cost Analysis** - Detailed breakdown with commission calculations
- 📄 **Markdown Export** - Download your complete vacation plan

### 🎨 Beautiful UI
- Modern Streamlit interface with gradient designs
- Responsive tables and cards
- Interactive tabs for organized information
- Real-time progress indicators
- Mobile-friendly design

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
## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- API Keys for:
  - OpenAI/Groq (for LLM)
  - Tavily (for destination research)
  - SerpAPI (for hotel search)
  - RapidAPI (for flight prices)
  - OpenWeatherMap (for weather)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/danielkrasik3010/VacayMate.git
   cd VacayMate
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_key
   GROQ_API_KEY=your_groq_key
   TAVILY_API_KEY=your_tavily_key
   SERPAPI_API_KEY=your_serpapi_key
   RAPIDAPI_KEY=your_rapidapi_key
   OPENWEATHER_API_KEY=your_openweather_key
   ```

5. **Run the Streamlit app**
   ```bash
   cd UI
   streamlit run app.py
   ```

## 📁 Project Structure

```
VacayMate/
├── code/                          # Core system code
│   ├── tools/                     # Agent tools
│   │   ├── destination_info_tool.py
│   │   ├── Flights_prices_tool.py
│   │   ├── Hotels_prices_tool.py
│   │   ├── Weather_Forecast_tool.py
│   │   └── Event_finder_tool.py
│   ├── nodes/                     # Agent implementations
│   │   └── VacayMate_nodes.py
│   ├── graphs/                    # LangGraph workflow
│   │   └── VacayMate_graph.py
│   ├── states/                    # State management
│   │   └── VacayMate_state.py
│   └── VacayMate_system.py       # Main system class
├── UI/                           # Streamlit interface
│   ├── app.py                    # Main UI application
│   ├── requirements.txt          # UI dependencies
│   └── README.md                 # UI documentation
├── outputs/                      # Generated vacation plans
├── config/                       # Configuration files
├── requirements.txt              # Main dependencies
└── README.md                     # This file
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



## 🔧 Configuration

### API Keys Setup
The system requires several API keys for full functionality:

1. **LLM Provider** (Choose one):
   - OpenAI: `OPENAI_API_KEY`
   - Groq: `GROQ_API_KEY`

2. **Data Sources**:
   - Tavily (destination info): `TAVILY_API_KEY`
   - SerpAPI (hotels): `SERPAPI_API_KEY`
   - RapidAPI (flights): `RAPIDAPI_KEY`
   - OpenWeatherMap: `OPENWEATHER_API_KEY`

### System Configuration
Edit `config/config.yaml` to customize:
- Agent prompts and behaviors
- API rate limits
- Output formats
- Cost calculation parameters

## 🎯 Usage Examples

### Basic Trip Planning
```python
from code.VacayMate_system import VacayMate

# Initialize the system
vacay_mate = VacayMate(llm_model="gpt-4o-mini")

# Plan a trip
result = vacay_mate.run(
    user_request="Plan a 5-day trip to Paris",
    current_location="Barcelona",
    destination="Paris",
    start_date="2024-06-15",
    return_date="2024-06-20"
)
```

### Advanced Configuration
```python
# Custom configuration
vacay_mate = VacayMate(
    llm_model="groq/mixtral-8x7b-32768",
    max_hotels=10,
    max_events=15
)
```

## 🔄 System Workflow

1. **Input Processing**: User provides trip details
2. **Research Phase**: Gather flights, hotels, and destination info
3. **Planning Phase**: Create itinerary with weather and events
4. **Cost Analysis**: Calculate comprehensive pricing
5. **Summarization**: Compile final vacation plan
6. **Export**: Generate downloadable Markdown report

## 🛠️ Recent Improvements

### Fixed Issues ✅
- **Dynamic Attractions**: Now shows real destination attractions instead of hardcoded Paris data
- **Flight Duration**: Correct calculation and display (e.g., "2h 30m" instead of "120h")
- **Hotel Addresses**: Real street addresses instead of generic "central area"

### Enhanced Data Display 📊
- **Hotel Table**: Added coordinates, hotel class, total price, booking links
- **Flight Table**: Added cabin class, available seats, EUR pricing, return flight details
- **Attraction Parsing**: Intelligent extraction from research content

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com) and [LangGraph](https://langgraph.com)
- UI powered by [Streamlit](https://streamlit.io)
- Data sources: Tavily, SerpAPI, RapidAPI, OpenWeatherMap
- AI models: OpenAI GPT-4, Groq Mixtral

## 📞 Support

For questions, issues, or contributions:
- 🐛 [Report bugs](https://github.com/danielkrasik3010/VacayMate/issues)
- 💡 [Request features](https://github.com/danielkrasik3010/VacayMate/issues)
- 📧 Contact: [GitHub Profile](https://github.com/danielkrasik3010)

---

**Made with ❤️ by [Daniel Krasik](https://github.com/danielkrasik3010)**
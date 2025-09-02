
import os
import json
import datetime
from typing import Optional
from urllib.parse import urlparse
from serpapi import GoogleSearch
from pyowm import OWM
from langchain.agents import tool
from dotenv import load_dotenv
load_dotenv()

# The following API keys are placeholders and should be loaded from your .env file
# as shown in the original code. For this example, they are hardcoded
# to make the code self-contained and runnable.
OWM_API_KEY = 'c9e4f702cc39e83c223bb81911f03aa8'

# ========================================================================
#  WEATHER FORECAST TOOL (with human-readable summary)
# ========================================================================

@tool
def weather_forecast_tool(location: str, days: int = 5, units: str = "metric") -> str:
    """
    Retrieves daily weather forecasts for the next 'days' days.
    Returns date, condition, temp_high, temp_low, wind, humidity, precipitation.
    Also provides a human-readable summary.
    """
    try:
        owm = OWM(OWM_API_KEY)
        mgr = owm.weather_manager()
        forecast = mgr.forecast_at_place(location, '3h')

        daily_forecasts = {}
        for weather in forecast.forecast:
            date_str = weather.reference_time('iso').split(' ')[0]
            temp = weather.temperature('celsius' if units=="metric" else 'fahrenheit')['temp']
            daily_forecasts.setdefault(date_str, {
                "condition": weather.detailed_status,
                "temp_high": temp,
                "temp_low": temp,
                "wind_speed": weather.wind().get('speed'),
                "humidity": weather.humidity,
                "precipitation": weather.rain.get('3h', 0) if weather.rain else 0
            })
            daily_forecasts[date_str]['temp_high'] = max(daily_forecasts[date_str]['temp_high'], temp)
            daily_forecasts[date_str]['temp_low'] = min(daily_forecasts[date_str]['temp_low'], temp)

        output_list = list(daily_forecasts.items())[:days]

        # Human-readable summary
        summary_lines = []
        simplified_forecasts = []
        for date_str, info in output_list:
            simplified_forecasts.append({
                "date": date_str,
                "condition": info['condition'],
                "temp_high": info['temp_high'],
                "temp_low": info['temp_low'],
                "wind_speed": info['wind_speed'],
                "humidity": info['humidity'],
                "precipitation": info['precipitation']
            })
            summary_lines.append(
                f"On {date_str}, expect {info['condition']} with highs of {info['temp_high']}° and lows of {info['temp_low']}°. "
                f"Wind: {info['wind_speed']} units, Humidity: {info['humidity']}%, Precipitation: {info['precipitation']} units."
            )

        return json.dumps({
            "forecasts": simplified_forecasts,
            "human_readable_summary": " ".join(summary_lines)
        }, indent=2)

    except Exception as e:
        return f"Error with Weather Forecast Tool: {e}"

# ========================================================================
# 5. TESTING THE TOOLS
# ========================================================================

if __name__ == "__main__":
    today = datetime.date.today()
    next_week = today + datetime.timedelta(days=7)
    print("Testing Weather Forecast Tool...")
    weather_result = weather_forecast_tool.invoke({
        "location": "London",
        "days": 5,
        "units": "metric"
    })
    print(weather_result)
    print("\n---------------------------------------")

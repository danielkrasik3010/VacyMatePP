import os
import datetime
import statistics
from typing import List, Dict
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

def ask_llm_for_daily_cost(destination: str, max_retries: int = 3) -> float:
    """
    Ask the LLM how much a traveler spends daily on food/attractions in a destination.
    Retry up to `max_retries` if the result is not a clean float.
    """
    query = f"Give me a single number: the average daily cost for a tourist in {destination} (food + attractions). Return only the number."

    for attempt in range(max_retries):
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that returns only numbers."},
                {"role": "user", "content": query},
            ],
        )
        result = response.choices[0].message.content.strip()

        # Try to parse a float
        try:
            daily_cost = float(result.split()[0].replace("$", "").replace(",", ""))
            return daily_cost
        except ValueError:
            if attempt < max_retries - 1:
                continue
            raise ValueError(f"LLM did not return a valid number after {max_retries} tries. Got: {result}")

def calculate_vacation_cost(
    hotel_prices: List[float],
    flight_prices: List[float],
    start_date: str,
    end_date: str,
    destination: str
) -> Dict[str, float]:
    """
    Calculate total vacation cost given hotel/flight prices and destination.
    """

    # 1. Number of days
    d1 = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    num_days = (d2 - d1).days

    # 2. Avg hotel per night * days
    avg_hotel_price = statistics.mean(hotel_prices)
    total_hotel = round((avg_hotel_price * num_days),2)

    # 3. Average flight price (already round-trip from API)
    avg_flight_price = statistics.mean(flight_prices)

    # 4. LLM daily spend
    daily_cost = ask_llm_for_daily_cost(destination)
    total_daily_spend = round((daily_cost * num_days), 2)

    # 5. Final sum before commission
    total_estimate = round((total_hotel + avg_flight_price + total_daily_spend), 2)
    
    # 6. Final quotation with 10% commission
    quotation = round((total_estimate * 1.1), 2)

    return {
        "days": num_days,
        "hotel_total": total_hotel,
        "flight_total": avg_flight_price,
        "daily_cost_estimate": daily_cost,
        "daily_total": total_daily_spend,
        "subtotal": total_estimate,
        "commission_rate": 0.1,
        "commission_amount": round((total_estimate * 0.1), 2),
        "final_quotation": quotation
    }


# ---------------- TEST ---------------- #
if __name__ == "__main__":
    fake_hotels = [120, 150, 130]  # per night
    fake_flights = [300, 350, 400]  # round trip
    start = "2025-07-01"
    end = "2025-07-08"
    destination = "Barcelona"

    result = calculate_vacation_cost(fake_hotels, fake_flights, start, end, destination)
    print("Vacation Cost Breakdown:", result)

    print('Final quotation with commission:', result['final_quotation'])

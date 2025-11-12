import random

def get_current_weather(location: str, unit: str = "fahrenheit"):
    """
    Get the current weather in a given location.

    :param location: The city and state, e.g. San Francisco, CA
    :param unit: The unit to use, either "celsius" or "fahrenheit"
    :return: A string describing the weather.
    """
    if "tokyo" in location.lower():
        temperature = 10 if unit == "celsius" else 50
        return f'{{"location": "{location}", "temperature": "{temperature}", "unit": "{unit}", "forecast": "rainy"}}'
    elif "san francisco" in location.lower():
        temperature = 18 if unit == "celsius" else 65
        return f'{{"location": "{location}", "temperature": "{temperature}", "unit": "{unit}", "forecast": "sunny"}}'
    else:
        temperature = 22 if unit == "celsius" else 72
        return f'{{"location": "{location}", "temperature": "{temperature}", "unit": "{unit}", "forecast": "cloudy"}}'

def get_stock_price(symbol: str):
    """
    Get the current stock price for a given ticker symbol.

    :param symbol: The stock ticker symbol, e.g. AAPL, GOOG
    :return: A string with the stock price.
    """
    price = round(random.uniform(100, 500), 2)
    return f'{{"symbol": "{symbol}", "price": "{price}"}}'

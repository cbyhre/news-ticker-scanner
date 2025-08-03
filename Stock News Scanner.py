import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import pytz

def extract_recent_tickers():
    url = "https://www.stocktitan.net/news/today"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tags = soup.find_all("script", type="application/ld+json")
        for script in script_tags:
            if "DataFeed" in script.text:
                raw_json = script.string or script.get_text()
                break
        else:
            print("JSON-LD block with DataFeed not found.")
            return

        data = json.loads(raw_json)
        utc = pytz.utc
        eastern = pytz.timezone("US/Eastern")
        now_et = datetime.now(eastern)
        cutoff_et = now_et - timedelta(minutes=30)
        results = []
        for item in data.get("dataFeedElement", []):
            entry = item.get("item", {})
            image_url = entry.get("image", "")
            date_str = entry.get("datePublished", "")
            headline = entry.get("headline", "")

            match = re.search(r'/company-logo/([a-z0-9]+)-lg\.webp', image_url, re.IGNORECASE)
            if match and date_str:
                ticker = match.group(1).upper()
                dt_utc = utc.localize(datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.000Z"))
                dt_et = dt_utc.astimezone(eastern)
                if dt_et >= cutoff_et:
                    results.append((ticker, dt_et, headline))

        results.sort(key=lambda x: x[1], reverse=True)

        if results:
            print("Tickers from articles in the last 30 minutes:")
            for ticker, dt, headline in results:
                print(f"{ticker} | {dt.strftime('%Y-%m-%d %I:%M:%S %p ET')} | {headline}")
        else:
            print("⚠️ No articles in the last 30 minutes.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_recent_tickers()

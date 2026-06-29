#!/usr/bin/env python3
"""
AW13 – Social Sentiment Monitoring Warden
Tracks social media sentiment, protests, civil unrest.
"""
import json
import random
from datetime import datetime, timezone

def fetch_social_sentiment():
    """Fetch social sentiment data (mocked for now)."""
    # In production, use Reddit API, Twitter API, or Telegram sentiment
    sentiments = []
    topics = ["protests", "unrest", "demonstration", "strike", "rally"]
    regions = ["USA", "UK", "France", "Germany", "India", "Brazil", "Nigeria", "Egypt"]
    
    for i in range(10):
        sentiments.append({
            "id": f"SOC-{i+1:03d}",
            "topic": random.choice(topics),
            "region": random.choice(regions),
            "sentiment_score": round(random.uniform(-1.0, 1.0), 2),
            "volume": random.randint(100, 50000),
            "trend": random.choice(["rising", "falling", "stable"]),
            "date": datetime.now(timezone.utc).isoformat()
        })
    return sentiments

def main():
    print("📢 AW13 – Social Sentiment Monitoring Warden running...")
    sentiments = fetch_social_sentiment()
    
    output = {
        "source": "AW13 Social Sentiment Warden",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sentiments": sentiments
    }
    
    with open("social_data.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved {len(sentiments)} social sentiment entries to social_data.json")

if __name__ == "__main__":
    main()

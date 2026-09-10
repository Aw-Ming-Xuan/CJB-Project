import requests
import pandas as pd
import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from transformers import pipeline
from deep_translator import GoogleTranslator

API_KEY = "0b5dd87c9fbf4aedb5ec0f53d97c6e6b"
DB_NAME = "Latam_macro_risk.db"

TARGETS = {
    "Brazil": {"query": "economia OR inflação OR Bacen", "lang": "pt"},
    "Mexico": {"query": "economía OR inflación OR Banxico", "lang": "es"},
    "Chile": {"query": "economía OR inflación OR Banco Central", "lang": "es"}
}


# Load the specific financial NLP model ('ProsusAI/finbert') from Hugging Face. 
# The 'pipeline' function sets it up specifically to perform 'sentiment-analysis'
finbert = pipeline("sentiment-analysis", model="ProsusAI/finbert")

# Open a connection to your local database file (e.g., latam_macro_risk.db). 
# If the file doesn't exist yet, this line will create it for you.
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS sentiment_history (
        date TEXT,
        country TEXT,
        headline TEXT,
        sentiment_label TEXT,
        sentiment_score REAL
    )
''')

conn.commit()

# FinBERT outputs a label ("positive", "negative", or "neutral") and a confidence score between 0.0 and 1.0.
# This helper function converts those outputs into a single net score ranging from -1.0 to +1.0.
def convert_finbert_score(result):
    # Extract the label predicted by FinBERT (e.g., 'positive')
    label = result[0]['label']
    
    # Extract FinBERT's confidence score (e.g., 0.85)
    score = result[0]['score']
    
    # If positive, keep the score positive (e.g., +0.85)
    if label == 'positive': 
        return score
    
    # If negative, flip the score to negative (e.g., -0.85)
    elif label == 'negative': 
        return -score
    
    # If neutral, return 0.0 so it doesn't skew the sentiment higher or lower
    return 0.0

# This main function fetches news for each target country, translates local headlines to English,
# calculates the FinBERT score, and inserts the data into your SQLite database.
def fetch_and_score_news():
    # Grab today's date in YYYY-MM-DD format to timestamp our database entries
    today = datetime.today().strftime('%Y-%m-%d')
    
    # Initialize the translator tool so it automatically translates Spanish/Portuguese into English
    translator = GoogleTranslator(source='auto', target='en')
    
    # Loop through each country (Brazil, Mexico, Chile) and its associated search settings
    for country, params in TARGETS.items():
        print(f"Fetching data for {country}...")
        
        # Build the dynamic web address to query NewsAPI for news matching our keywords and language
        url = f"https://newsapi.org/v2/everything?q={params['query']}&language={params['lang']}&sortBy=publishedAt&apiKey={API_KEY}"
        
        try:
            # Send the request to NewsAPI with a 10-second timeout to prevent the script from hanging
            response = requests.get(url, timeout=10)
            
            # Raise an error automatically if the web request returned a bad status code (like 404 or 401)
            response.raise_for_status()
            
            # Parse the incoming JSON web response into a Python dictionary
            data = response.json()
            
            # Check if NewsAPI confirmed the query was successful
            if data.get("status") == "ok":
                # Loop through only the top 15 most recent articles to keep signal high and reduce noise
                for article in data["articles"][:15]: 
                    # Grab the original headline text
                    original_headline = article["title"]
                    
                    # Skip empty or missing headlines
                    if not original_headline: 
                        continue
                        
                    # Translate Spanish or Portuguese headlines into English for FinBERT
                    en_headline = translator.translate(original_headline)
                    
                    # Pass the translated headline into FinBERT to get the sentiment
                    sentiment = finbert(en_headline)
                    
                    # Convert FinBERT's output into a single number between -1.0 and +1.0
                    num_score = convert_finbert_score(sentiment)
                    
                    # Get the raw label ('positive', 'negative', or 'neutral')
                    label = sentiment[0]['label']
                    
                    # Insert this headline's record into our database table
                    cursor.execute(
                        "INSERT INTO sentiment_history VALUES (?, ?, ?, ?, ?)",
                        (today, country, original_headline, label, num_score)
                    )
                
                # Save all new inserted rows for this country to the database
                conn.commit()
                
        # Catch network or API errors cleanly without stopping or crashing the script for other countries
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data for {country}: {e}")

def plot_sentiment_index():
    # Pull all historical data from the SQLite database
    df = pd.read_sql_query("SELECT * FROM sentiment_history", conn)
    
    if df.empty:
        print("No data available to plot.")
        return
        
    # Group the data by date and country to get the daily average
    daily_idx = df.groupby(['date', 'country'])['sentiment_score'].mean().reset_index()
    
    # Set the visual theme for Seaborn (adds a clean grid background)
    sns.set_theme(style="whitegrid")
    
    # Set the size of the pop-up window (width=10, height=6)
    plt.figure(figsize=(10, 6))
    
    # Draw the line chart
    sns.lineplot(
        data=daily_idx, 
        x="date", 
        y="sentiment_score", 
        hue="country",     # Colors lines differently based on country
        marker="o",        # Adds dots at each data point
        linewidth=2
    )
    
    # Draw a dashed gray line at the 0.0 mark for the neutral baseline
    plt.axhline(0, color='gray', linestyle='--', label='Neutral')
    
    # Add chart titles and axis labels
    plt.title("LatAm Macro Risk & Currency Sentiment Index", fontsize=14, pad=15)
    plt.xlabel("Date", fontweight='bold')
    plt.ylabel("Net Sentiment (-1.0 to 1.0)", fontweight='bold')
    
    # Lock the Y-axis scale so it doesn't zoom in too far
    plt.ylim(-1.1, 1.1)
    
    # Display the legend cleanly outside the main chart area
    plt.legend(title="Country", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout() # Ensures labels don't get cut off
    
    # Open the window to display the final chart
    plt.show()

if __name__ == "__main__":
    fetch_and_score_news()
    plot_sentiment_index()
    conn.close()

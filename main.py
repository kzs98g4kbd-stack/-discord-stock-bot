import discord
from discord.ext import tasks
import yfinance as yf
import numpy as np
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

STOCKS = ["BAC","VZ","PFE","KO","SOFI","PLTR","INTC","AMD","NVDA","TSLA"]

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze(stock):
    df = yf.Ticker(stock).history(period="6mo")

    if len(df) < 60:
        return None

    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    df["RSI"] = rsi(df["Close"])

    last = df.iloc[-1]

    price = last["Close"]
    sma20 = last["SMA20"]
    sma50 = last["SMA50"]
    sma200 = last["SMA200"]
    rsi_val = last["RSI"]

    if np.isnan(sma200) or np.isnan(rsi_val):
        return None

    if price > sma200 and sma20 > sma50 and rsi_val < 45:
        return f"🟢 CALL {stock} | Price: {price:.2f} | RSI: {rsi_val:.1f}"

    if price < sma200 and sma20 < sma50 and rsi_val > 60:
        return f"🔴 PUT {stock} | Price: {price:.2f} | RSI: {rsi_val:.1f}"

    return None

@tasks.loop(minutes=15)
async def scan():
    channel = client.get_channel(CHANNEL_ID)

    for stock in STOCKS:
        signal = analyze(stock)
        if signal:
            await channel.send(signal)

@client.event
async def on_ready():
    print("Bot running")
    scan.start()

client.run(TOKEN)

import pandas as pd
import yfinance as yf
import ta
import google.generativeai as genai
import mplfinance as mpf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from textblob import TextBlob
import tkinter as tk
from tkinter import messagebox

genai.configure(api_key="AIzaSyBagCZLXcFCjHZndcumcfetcH7YxwPXBjI")
model = genai.GenerativeModel('gemini-pro')

def show_analysis(t, p, a, r):
    if a == "technical":
        h = yf.Ticker(t).history(period=p)
        ta = calculate_technical_analysis(h)
        analysis_text.delete("1.0", tk.END)
        analysis_text.insert(tk.END, f"Technical Analysis Report:\n{ta}")
    elif a == "fundamental":
        fa = get_fundamental_analysis(t)
        analysis_text.delete("1.0", tk.END)
        analysis_text.insert(tk.END, f"Fundamental Analysis Report:\n{fa}")
    elif a == "sentiment":
        nl = yf.Ticker(t).news
        if not nl:
            s = "Neutral"
        else:
            h = ' '.join(n['title'] for n in nl)
            b = TextBlob(h)
            p = b.sentiment.polarity
            s = "Positive" if p > 0 else "Negative" if p < 0 else "Neutral"
        sentiment_analysis_report = f"Sentiment Analysis Report:\n- Overall Sentiment: {s}\nNews Headlines and Polarities:\n"
        for n in nl:
            np = TextBlob(n['title']).sentiment.polarity
            sentiment_analysis_report += f"- {n['title']}: {np}\n"
        analysis_text.delete("1.0", tk.END)
        analysis_text.insert(tk.END, sentiment_analysis_report + "\n\n" + r)

def analyze_ticker():
    t = ticker_entry.get().upper()
    p = time_period_var.get()
    if not t:
        messagebox.showerror("Error", "Please enter a ticker symbol.")
        return
    h = yf.Ticker(t).history(period=p)
    ta = calculate_technical_analysis(h)
    fa = get_fundamental_analysis(t)
    s = get_sentiment_analysis(t)
    r = generate_report(t, ta, fa, s, p)
    analysis_text.delete("1.0", tk.END)
    analysis_text.insert(tk.END, r)
    show_visualization(t, p)
    for a in ["technical", "fundamental", "sentiment"]:
        b = tk.Button(button_frame, text=f"{a.capitalize()} Analysis", command=lambda a=a: show_analysis(t, p, a, r))
        b.pack(side=tk.LEFT, padx=10)

def show_visualization(t, p):
    try:
        s = yf.Ticker(t)
        h = s.history(period=p)
        fig, ax = mpf.plot(h, type='candle', mav=(10, 50), title=f"{t} Candlestick Chart ({p})", style='yahoo', returnfig=True)
        canvas = FigureCanvasTkAgg(fig, master=display_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def calculate_technical_analysis(h):
    h['EMA50'] = ta.trend.ema_indicator(h['Close'], window=50)
    h['EMA10'] = ta.trend.ema_indicator(h['Close'], window=10)
    if h['Close'].iloc[-1] > h['EMA10'].iloc[-1] and h['Close'].iloc[-1] > h['EMA50'].iloc[-1]:
        return "Uptrend"
    elif h['Close'].iloc[-1] < h['EMA10'].iloc[-1] and h['Close'].iloc[-1] < h['EMA50'].iloc[-1]:
        return "Downtrend"
    else:
        return "Consolidation or uncertainty in the trend"

def get_fundamental_analysis(t):
    s = yf.Ticker(t)
    sector = s.info['sector']
    fa = s.info
    pe_ratio = fa.get('trailingPE', 'N/A')
    eps = fa.get('trailingEps', 'N/A')
    market_cap = fa.get('marketCap', 'N/A')
    return f"Fundamental Analysis:\n- P/E Ratio: {pe_ratio}\n- Earnings Per Share (EPS): {eps}\n- Market Cap: {market_cap}"

def get_sentiment_analysis(t):
    nl = yf.Ticker(t).news
    if not nl:
        return "Neutral"
    h = ' '.join(n['title'] for n in nl)
    p = TextBlob(h).sentiment.polarity
    return "Positive" if p > 0 else "Negative" if p < 0 else "Neutral"

def generate_report(t, ta, fa, s, p):
    s = yf.Ticker(t)
    sector = s.info['sector']
    h = s.history(period=p)
    i = f"Please provide a detailed analysis report for {t}:\n\nCompany Information:\nTicker: {t}\n- Sector: {sector}\n\nTechnical Analysis:\n{ta}\n\n{fa}\n\nSentiment Analysis:\n- Overall Sentiment: {s}\n\nPlease generate a detailed analysis report without any recommendations and disclaimer based on all the publicly available and provided information."
    r = model.generate_content(i).text.replace("*", "")
    return r

def clear_application():
    global ticker_entry, analysis_text, display_frame, button_frame, canvas
    ticker_entry.delete(0, tk.END)
    analysis_text.delete("1.0", tk.END)
    if 'canvas' in globals():
        canvas.get_tk_widget().destroy()
    display_frame.destroy()
    display_frame = tk.Frame(root)
    display_frame.pack(pady=10, fill=tk.BOTH, expand=True)
    analysis_text = tk.Text(display_frame, width=80, height=10)
    analysis_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    button_frame.destroy()
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    analyze_button = tk.Button(button_frame, text="Analyze", command=analyze_ticker)
    analyze_button.pack(side=tk.LEFT, padx=10)
    clear_button = tk.Button(button_frame, text="Clear", command=clear_application)
    clear_button.pack(side=tk.LEFT, padx=10)

root = tk.Tk()
root.title("Sentiment Analysis of Financial Markets")
root.state("zoomed")
input_frame = tk.Frame(root)
input_frame.pack(pady=10)
ticker_label = tk.Label(input_frame, text="Enter Ticker Symbol:")
ticker_label.grid(row=0, column=0)
ticker_entry = tk.Entry(input_frame)
ticker_entry.grid(row=0, column=1)
time_period_label = tk.Label(input_frame, text="Select Time Period:")
time_period_label.grid(row=1, column=0)
time_period_var = tk.StringVar(root)
time_period_var.set("1d")
time_period_options = ["5m", "15m", "1h", "1d", "1wk", "1mo", "6mo", "1y"]
time_period_dropdown = tk.OptionMenu(input_frame, time_period_var, *time_period_options)
time_period_dropdown.grid(row=1, column=1)
display_frame = tk.Frame(root)
display_frame.pack(pady=10, fill=tk.BOTH, expand=True)
analysis_text = tk.Text(display_frame, width=80, height=10)
analysis_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
button_frame = tk.Frame(root)
button_frame.pack(pady=10)
analyze_button = tk.Button(button_frame, text="Analyze", command=analyze_ticker)
analyze_button.pack(side=tk.LEFT, padx=10)
clear_button = tk.Button(button_frame, text="Clear", command=clear_application)
clear_button.pack(side=tk.LEFT, padx=10)
root.mainloop()

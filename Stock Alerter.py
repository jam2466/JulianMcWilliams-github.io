# Import necessary libraries
import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# --- Configuration ---
# Stock ticker symbol
STOCK_TICKER = "MSFT"

# SMA periods
SMA_SHORT_PERIOD = 8
SMA_LONG_PERIOD = 21

# Email settings (replace with your actual details)
SENDER_EMAIL = "mcwilliamsjulian@gmail.com"  # Your Gmail address
SENDER_PASSWORD = "jzyf fwiw ljml tqqm"  # Your Gmail App Password (NOT your regular password)
RECEIVER_EMAIL = "mcwilliamsjulian@gmail.com" # The email address to send alerts to

def fetch_stock_data(ticker, period_days):
    """
    Fetches historical stock data for a given ticker.

    Args:
        ticker (str): The stock ticker symbol (e.g., "MSFT").
        period_days (int): Number of days of historical data to fetch.
                           Ensure this is long enough to calculate the longest SMA.

    Returns:
        pandas.DataFrame: DataFrame containing historical stock data, or None if an error occurs.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days + SMA_LONG_PERIOD * 2) # Fetch enough data for SMAs
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            print(f"No data fetched for {ticker}. Check ticker symbol or date range.")
            return None
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def calculate_smas(df, short_period, long_period):
    """
    Calculates Simple Moving Averages (SMAs) for the 'Close' price.

    Args:
        df (pandas.DataFrame): DataFrame with stock data, including a 'Close' column.
        short_period (int): Period for the short SMA.
        long_period (int): Period for the long SMA.

    Returns:
        pandas.DataFrame: DataFrame with 'SMA_Short' and 'SMA_Long' columns added.
    """
    if 'Close' not in df.columns:
        print("DataFrame must contain a 'Close' column.")
        return df

    df[f'SMA_{short_period}D'] = df['Close'].rolling(window=short_period).mean()
    df[f'SMA_{long_period}D'] = df['Close'].rolling(window=long_period).mean()
    return df

def check_crossover(df, short_sma_col, long_sma_col):
    """
    Checks for SMA crossovers on the most recent data point.

    Args:
        df (pandas.DataFrame): DataFrame with SMA columns.
        short_sma_col (str): Name of the short SMA column.
        long_sma_col (str): Name of the long SMA column.

    Returns:
        str: "BULLISH_CROSS", "BEARISH_CROSS", or "NO_CROSS".
    """
    # Ensure there's enough data for comparison
    if len(df) < 2 or df[short_sma_col].isnull().iloc[-2] or df[long_sma_col].isnull().iloc[-2]:
        print("Not enough data to check for crossover or SMAs not fully calculated.")
        return "NO_CROSS"

    # Get the most recent and previous day's SMA values
    short_sma_current = df[short_sma_col].iloc[-1]
    long_sma_current = df[long_sma_col].iloc[-1]
    short_sma_prev = df[short_sma_col].iloc[-2]
    long_sma_prev = df[long_sma_col].iloc[-2]

    # Check for bullish crossover (short SMA crosses above long SMA)
    if short_sma_prev < long_sma_prev and short_sma_current > long_sma_current:
        return "BULLISH_CROSS"
    # Check for bearish crossover (short SMA crosses below long SMA)
    elif short_sma_prev > long_sma_prev and short_sma_current < long_sma_current:
        return "BEARISH_CROSS"
    else:
        return "NO_CROSS"

def send_email_alert(subject, body, sender, password, receiver):
    """
    Sends an email alert.

    Args:
        subject (str): The subject of the email.
        body (str): The body content of the email.
        sender (str): Sender's email address.
        password (str): Sender's email app password.
        receiver (str): Receiver's email address.
    """
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = receiver

        # Connect to Gmail's SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: # Use 465 for SSL
            smtp.login(sender, password)
            smtp.send_message(msg)
        print(f"Email alert sent successfully to {receiver}!")
    except Exception as e:
        print(f"Error sending email: {e}")
        print("Please ensure you have enabled 'Less secure app access' or generated an 'App password' for Gmail.")
        print("For Gmail App Passwords: https://support.google.com/accounts/answer/185833")

# --- Main Execution ---
if __name__ == "__main__":
    print(f"Starting SMA crossover check for {STOCK_TICKER}...")

    # 1. Fetch stock data
    # Fetch enough data to ensure SMAs are calculated correctly, plus a buffer.
    # A year of data should be more than sufficient for 21-day SMA.
    stock_data = fetch_stock_data(STOCK_TICKER, period_days=365)

    if stock_data is None:
        print("Could not fetch stock data. Exiting.")
    else:
        # 2. Calculate SMAs
        stock_data = calculate_smas(stock_data, SMA_SHORT_PERIOD, SMA_LONG_PERIOD)

        # Print the last few rows to verify calculations (optional)
        print("\nLast few rows of stock data with SMAs:")
        print(stock_data.tail())

        # 3. Check for crossover
        crossover_status = check_crossover(stock_data, f'SMA_{SMA_SHORT_PERIOD}D', f'SMA_{SMA_LONG_PERIOD}D')

        subject = ""
        body = ""

        if crossover_status == "BULLISH_CROSS":
            subject = f"📈 BULLISH CROSS ALERT: {STOCK_TICKER} {SMA_SHORT_PERIOD}D SMA crossed above {SMA_LONG_PERIOD}D SMA!"
            body = (
                f"Dear Trader,\n\n"
                f"A bullish crossover has been detected for {STOCK_TICKER} stock.\n"
                f"The {SMA_SHORT_PERIOD}-day SMA has crossed above the {SMA_LONG_PERIOD}-day SMA.\n\n"
                f"Current {STOCK_TICKER} Close: ${stock_data['Close'].iloc[-1]:.2f}\n"
                f"{SMA_SHORT_PERIOD}-day SMA: ${stock_data[f'SMA_{SMA_SHORT_PERIOD}D'].iloc[-1]:.2f}\n"
                f"{SMA_LONG_PERIOD}-day SMA: ${stock_data[f'SMA_{SMA_LONG_PERIOD}D'].iloc[-1]:.2f}\n\n"
                f"This may indicate a potential upward trend.\n"
                f"Always perform your own analysis before making trading decisions.\n\n"
                f"Best regards,\nYour Trading Bot"
            )
            send_email_alert(subject, body, SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL)
        elif crossover_status == "BEARISH_CROSS":
            subject = f"📉 BEARISH CROSS ALERT: {STOCK_TICKER} {SMA_SHORT_PERIOD}D SMA crossed below {SMA_LONG_PERIOD}D SMA!"
            body = (
                f"Dear Trader,\n\n"
                f"A bearish crossover has been detected for {STOCK_TICKER} stock.\n"
                f"The {SMA_SHORT_PERIOD}-day SMA has crossed below the {SMA_LONG_PERIOD}-day SMA.\n\n"
                f"Current {STOCK_TICKER} Close: ${stock_data['Close'].iloc[-1]:.2f}\n"
                f"{SMA_SHORT_PERIOD}-day SMA: ${stock_data[f'SMA_{SMA_SHORT_PERIOD}D'].iloc[-1]:.2f}\n"
                f"{SMA_LONG_PERIOD}-day SMA: ${stock_data[f'SMA_{SMA_LONG_PERIOD}D'].iloc[-1]:.2f}\n\n"
                f"This may indicate a potential downward trend.\n"
                f"Always perform your own analysis before making trading decisions.\n\n"
                f"Best regards,\nYour Trading Bot"
            )
            send_email_alert(subject, body, SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL)
        else:
            print(f"No SMA crossover detected for {STOCK_TICKER} today.")

    print("Program finished.")

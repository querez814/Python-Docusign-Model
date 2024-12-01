import requests
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import tabulate
import matplotlib as plt

# Configuration
config = {
    "alpha_vantage": {
        "key": "UC9RDCYAL4XWXFM3",
        "symbol": "DOCU",
        "outputsize": {
            "compact": "compact",
            "full": "full"
        },
        "function": {
            "INCOME_STATEMENT": "INCOME_STATEMENT",
            "EARNINGS": "EARNINGS",
            "BALANCE_SHEET": "BALANCE_SHEET",
            "TIME_SERIES_DAILY": "TIME_SERIES_DAILY"
        }
    },
}

# PAGE VARIABLES FROM ALPHA VANTAGE CONFIG
api_key = config["alpha_vantage"]["key"]
symbol = config["alpha_vantage"]["symbol"]
balance_sheet_function = config["alpha_vantage"]["function"]["BALANCE_SHEET"]
income_statement_function = config["alpha_vantage"]["function"]["INCOME_STATEMENT"]
earnings_function = config["alpha_vantage"]["function"]["EARNINGS"]
daily_prices_function = config["alpha_vantage"]["function"]["TIME_SERIES_DAILY"]
compact_sizing = config["alpha_vantage"]["outputsize"]["compact"]
full_sizing = config["alpha_vantage"]["outputsize"]["full"]

# URLS - FROM ALPHA VANTAGE (THESE CONTAIN THE SOON-TO-BE JSONS)
income_statement_url = f"https://www.alphavantage.co/query?function={income_statement_function}&symbol={symbol}&apikey={api_key}"
earnings_url = f"https://www.alphavantage.co/query?function={earnings_function}&symbol={symbol}&apikey={api_key}"
balance_sheet_url = f"https://www.alphavantage.co/query?function={balance_sheet_function}&symbol={symbol}&apikey={api_key}"
daily_prices_url_full = f"https://www.alphavantage.co/query?function={daily_prices_function}&symbol={symbol}&outputsize={full_sizing}&apikey={api_key}"

# READ THE URLS - READ THE URLS FROM ALPHA VANTAGE
r_balance_sheet = requests.get(balance_sheet_url)
r_income_statement = requests.get(income_statement_url)
r_earnings_statement = requests.get(earnings_url)
r_daily_prices = requests.get(daily_prices_url_full)

# TURN THE URLS TO JSON
balance_sheet_data = r_balance_sheet.json()
income_statement_data = r_income_statement.json()
earnings_income_data = r_earnings_statement.json()
daily_prices_data = r_daily_prices.json()

# QUARTERLY REPORTS
quarterly_balance_sheet_data = balance_sheet_data.get("quarterlyReports", [])
quarterly_income_statement_data = income_statement_data.get("quarterlyReports", [])
quarterly_earnings_data = earnings_income_data.get("quarterlyEarnings", [])

# Daily Prices
time_series_daily_prices_data = daily_prices_data.get("Time Series (Daily)")

# TURNING THE JSON TO A PANDAS DF
quarterly_balance_sheet_df = pd.DataFrame(quarterly_balance_sheet_data)
quarterly_income_statement_df = pd.DataFrame(quarterly_income_statement_data)
quarterly_earnings_df = pd.DataFrame(quarterly_earnings_data)

# Convert daily prices data into a DataFrame
time_series_daily_prices_df = pd.DataFrame(time_series_daily_prices_data).T
time_series_daily_prices_df.columns = [col.split(" ")[1] for col in time_series_daily_prices_df.columns]  # Rename columns
time_series_daily_prices_df.index = pd.to_datetime(time_series_daily_prices_df.index)

# Setting pandas options
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# THIS DATAFRAME CONTAINS THE DATE OF THE EARNINGS REPORT - WE NEED TO FIND THE PRICES FOR PRE & POST REPORTING
df_report_dates = quarterly_earnings_df['reportedDate']

#Get Cash Holdings from the Balance Sheet - TO BE USED FURTHER DOWN
df_cash_and_st_investments = quarterly_balance_sheet_df['cashAndShortTermInvestments']

#GET SHORT-TERM DEBT & SHORT-TERM PORTION OF LONG-TERM DEBT
df_current_debt = quarterly_balance_sheet_df['currentDebt']

#GET SHARES OUTSTANDING
df_shares_outstanding = quarterly_balance_sheet_df['commonStockSharesOutstanding']

# THIS DATAFRAME HAS THE REVENUE FROM EACH EARNINGS REPORT
df_revenue = quarterly_income_statement_df['totalRevenue']

# THIS DATAFRAME HAS THE CLOSING PRICE OF DOCUSIGN DAILY
df_closing_prices = time_series_daily_prices_df['close']

# Convert report dates to datetime format for consistency
df_report_dates = pd.to_datetime(df_report_dates)

# Create a DataFrame from report dates and net revenue
df_combo = pd.DataFrame({
    'Report Date': df_report_dates,
    'Net Revenue': df_revenue,
})

time_series_daily_prices_df.index = pd.to_datetime(time_series_daily_prices_df.index)

# Merge the dataframes on 'Report Date' and the index of 'time_series_daily_prices_df' to get the closing price on report date
df_combo = df_combo.merge(time_series_daily_prices_df[['close']], left_on='Report Date', right_index=True, how='left')

# Calculate next trading day for each report date
df_combo['Next Trading Day'] = df_combo['Report Date'].apply(lambda x: time_series_daily_prices_df.index[time_series_daily_prices_df.index > x].min())

# Merge to get the opening price of the next trading day
df_combo = df_combo.merge(time_series_daily_prices_df[['open']], left_on='Next Trading Day', right_index=True, how='left')

# Rename columns for clarity
df_combo.rename(columns={'close': 'Closing Price on Report Date', 'open': 'Opening Price on Next Trading Day'}, inplace=True)

# Convert closing and opening prices to numeric
df_combo['Closing Price on Report Date'] = pd.to_numeric(df_combo['Closing Price on Report Date'], errors='coerce')
df_combo['Opening Price on Next Trading Day'] = pd.to_numeric(df_combo['Opening Price on Next Trading Day'], errors='coerce')

df_combo['Percent Change (%)'] = ((df_combo['Opening Price on Next Trading Day'] - df_combo['Closing Price on Report Date']) / df_combo['Closing Price on Report Date']) * 100

#Calculate the Total Cash Holdings - TO BE USED IN EV/S Calculation
df_cash_and_st_investments = pd.to_numeric(df_cash_and_st_investments,errors='coerce')

df_shares_outstanding = pd.to_numeric(df_shares_outstanding, errors='coerce')



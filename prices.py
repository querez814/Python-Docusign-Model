import pandas as pd
import numpy as np
from tabulate import tabulate
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset
from torch.utils.data import DataLoader

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

from alpha_vantage.timeseries import TimeSeries 

# Configuration dictionary
config = {
    "alpha_vantage": {
        "key": "UC9RDCYAL4XWXFM3",
        "symbol": "DOCU",
        "outputsize": "compact",
        "key_close": "4. close",
    },
}

api_key = config['alpha_vantage']['key']
symbol = config['alpha_vantage']['symbol']

# Initialize the TimeSeries object
ts = TimeSeries(key=api_key, output_format='pandas')

# Fetch weekly price data from Alpha Vantage using the library
data, meta_data = ts.get_weekly(symbol=symbol)

# Rename columns for easier access
data.columns = ["open", "high", "low", "close", "volume"]

# Display data
# Set display options to show all rows and columns without truncation
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

print("Number of data points:", len(data))
print(f"Data range: from {data.index.min().date()} to {data.index.max().date()}")
print(tabulate(data, headers='keys', tablefmt='pretty'))

# Function to download daily adjusted data from Alpha Vantage
def download_data(config):
    ts = TimeSeries(key=api_key, output_format='pandas')
    data, meta_data = ts.get_daily_adjusted(config["alpha_vantage"]["symbol"], outputsize=config["alpha_vantage"]["outputsize"])

    data_date = [date.strftime('%Y-%m-%d') for date in data.index]
    data_close_price = data[config["alpha_vantage"]["key_close"]].values

    num_data_points = len(data_date)
    display_date_range = "from " + data_date[0] + " to " + data_date[num_data_points - 1]
    print("Number of data points:", num_data_points, display_date_range)

    # Displaying daily data with tabulate for clarity
    print(tabulate(data, headers='keys', tablefmt='pretty'))

    return data_date, data_close_price, num_data_points, display_date_range

# Download daily adjusted data and display it
data_date, data_close_price, num_data_points, display_date_range = download_data(config)

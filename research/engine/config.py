COINS = ["ADA", "DOGE", "XRP", "AVAX", "ETH", "SOL", "LTC", "HBAR"]
# columns present in raw/*.csv today
HAVE = [
    "c",
    "sum_open_interest",
    "sum_open_interest_value",
    "sum_taker_long_short_vol_ratio",
    "sum_toptrader_long_short_ratio",
    "count_long_short_ratio",
    "fund",
]
# slots still empty — fill when a file exists, do not invent
MISSING = [
    "mcap",          # CoinGecko blocked 429
    "liq_l", "liq_s",  # no free USD-M archive
    "sv", "sbv",     # spot taker, Coinalyze recorder only
    "book_bid", "book_ask",
]

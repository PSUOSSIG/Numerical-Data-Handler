import argparse
import boto3
import polygon
from utils import map_aggregate_bars_to_dates, get_month_before, get_start_and_end_of_month
from datetime import date
import sys
from icecream import ic
ic.disable()

# This is so we can expand to other tickers later, defaults to NVDA if no argument is passed
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--ticker", help = "stock ticker to get, defaults to NVDA if no ticker is specified")
args = parser.parse_args()
if args.ticker:
    ticker = args.ticker
else: ticker = "NVDA"

# Initialize the R2 client
#   open the file with the r2 keys
with open('cloudflare_ossig_r2_keys', 'r') as f:
    data = f.read().splitlines()
#   The line indices are based on the format for the keys file
access_key_id = data[4]
secret_access_key = data[7]
s3_endpoint = data[10]
#   Load the R2 client and get our bucket
r2 = boto3.resource(
    service_name ="s3",
    endpoint_url = s3_endpoint,
    aws_access_key_id = access_key_id,
    aws_secret_access_key = secret_access_key,
    region_name="enam", # Must be one of: wnam, enam, weur, eeur, apac, auto
)
bucket = r2.Bucket('ossig-stock-data')

# Initialize the polygon client and pull date
#   open the api key file and initialize the client
with open("polygon_api_key", 'r') as f:
    polygon_api_key = f.read().strip()
polygon_client = polygon.StocksClient(api_key=polygon_api_key)
# Try to open the file specifying the month to get, if it doesn't exist then default to the month before today's month
#   Will stop at a specified hard stop
try:
    with open(f"{ticker}_month_to_get", 'r') as f:
        month_to_get = f.read().strip()
        # We
        with open("hardstop-year", 'r') as f2:
            year = f2.read().strip()
        if int(month_to_get[:4]) < int(year):
            sys.exit(0)
except FileNotFoundError:
    todays_date = date.today().isoformat()
    todays_month = todays_date[:-3]
    month_to_get = get_month_before(todays_month)
# get the start and end dates of the month
month_start, month_end = get_start_and_end_of_month(month_to_get)

ic(month_start, month_end)

# pull date from polygon
aggregates = polygon_client.get_aggregate_bars(
    ticker, month_start, month_end,
    multiplier=30, timespan="minute",
    full_range=True, max_concurrent_workers=1,
    run_parallel=True, warnings=True
)

ic(aggregates)

ic(map_aggregate_bars_to_dates(bars=aggregates, month=month_to_get, convert_to_bytes_json=False))

# convert our aggregates into a bytes json
bytes_json = map_aggregate_bars_to_dates(bars=aggregates, month=month_to_get, convert_to_bytes_json=True)

# put the bytes_json on R2
bucket.put_object(Key=f"polygon-30m/{ticker}/{month_to_get}", Body=bytes_json)

# update the month for the next run of this script
with open(f"{ticker}_month_to_get", 'w+') as f:
    f.write(get_month_before(month_to_get))
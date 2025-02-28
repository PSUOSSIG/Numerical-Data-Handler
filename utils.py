from datetime import date, timedelta
import holidays
import json

def get_dates_between(start_date : str, end_date : str):
    """
    Returns a list of dates between start_date and end_date (inclusive).

    Args:
      start_date: The start date (datetime.date object).
      end_date: The end date (datetime.date object).

    Returns:
      A list of datetime.date objects.
    """
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    dates = []
    current_date = start
    while current_date <= end:
        dates.append(current_date)
        current_date += timedelta(days=1)
    return dates

def get_weekend_dates(start_date : str, end_date : str):
    """
    Returns a list of weekend dates (Saturdays and Sundays) within the given date range.

    Args:
        start_date (date): The start date of the range.
        end_date (date): The end date of the range.

    Returns:
        list: A list of dates representing weekends within the range.
    """
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    weekend_dates = []
    current_date = start
    while current_date <= end:
        if current_date.weekday() in [5, 6]:  # 5 is Saturday, 6 is Sunday
            weekend_dates.append(current_date)
        current_date += timedelta(days=1)
    return weekend_dates

def get_start_and_end_of_month(month : str) -> tuple:
    """
    Returns the start and end date of a month.
    :param month: month to get dates for. format should be YYYY-MM.
    :return: a tuple of the start and end date of the month.
    """

    # The start day is the first day of the month
    start = month+"-01"
    # Get the end date, this is the first day of the next month to compensate for different month end days
    #   Check if the month is December, if so we need to compensate by looking at the next year
    month_number = int(month[-2:])
    year = str(month[:-3])
    if month_number < 12:
        next_month_number = month_number + 1
        next_month = str(next_month_number)
        # add a zero to satisfy iso format if the month is before october
        if next_month_number < 10:
            next_month = "0" + next_month
        end_month = year + '-' + next_month
    else:
        year_number = int(year)
        next_year_number = year_number + 1
        next_year = str(next_year_number)
        # the next month here is always going to be january
        end_month = next_year + "-01"
    # add the day back on to satisfy iso format
    end_plus_one = end_month+"-01"

    # get the actual last day of the month instead of the first day of the next
    end_datetime = date.fromisoformat(end_plus_one) - timedelta(days=1)
    # convert back to a string
    end = end_datetime.isoformat()

    return start, end

def get_market_dates(month : str) -> list:
    """
    Returns a list of market dates within the given month.
    :param month: month to get dates for. format should be YYYY-MM.
    :return: a string of dates the market is open
    """

    # get the start and end of the month
    start, end = get_start_and_end_of_month(month)

    # This gets rid of the extraneous first day of the next month and leaves us with just the dates of the given month
    dates_between = get_dates_between(start, end)

    # Get the market holidays
    market_holidays = holidays.financial_holidays('NYSE')
    # Get the dates of the weekends in the month
    weekend_dates = get_weekend_dates(start, end)

    # Check if dates fall on weekends or holidays and remove them, leaving us with a list of open market days
    open_dates = list()
    for day in dates_between:
        if day not in market_holidays and day not in weekend_dates:
            open_dates.append(day.isoformat())

    # Return open market days
    return open_dates

def map_aggregate_bars_to_dates(bars : list, month : str, convert_to_bytes_json = False) -> dict or bytes:
    """
    maps polygon half-hour aggregate bars for a month to proper dates, accounting for weekends and holidays.
    can return a bytes object or bytes object if convert_to_bytes_json is True for S3 uploads
    :param bars: polygon half-hour aggregate bars for the month/
    :param month: month to map bars to. format should be YYYY-MM.
    :param convert_to_bytes_json: will convert to a bytes object or bytes object if True for S3 uploads
    :return: the mapped dict or the dict converted to a bytes object if convert_to_bytes_json is True
    """
    # Get the open markets dates of the given month
    keys = get_market_dates(month)

    # This creates a dictionary of days with half hour aggregate bars
    #   This dictionary has sub dictionaries that details whether the bars are pre-market, regular-market, or after-hours
    bars_dict = dict()
    for i, key in enumerate(keys):
        # There are 32 market half-hours a day when including pre-market and after-hours
        day_bars = bars[i*32:(i+1) * 32]

        # We make our sub-dictionary and divide our half-hour bars into the proper categories
        half_hours_dict = dict()
        half_hours_dict['pre-market'], half_hours_dict['regular-market'], half_hours_dict['after-hours'] = day_bars[:11], day_bars[11:24], day_bars[24:]

        # Append the sub-dictionary to the main dictionary
        bars_dict[key] = half_hours_dict

    # We label the dictionary as complete to differentiate it from the incomplete daily pull dicts
    bars_dict['complete'] = True

    if convert_to_bytes_json:
        return json.dumps(bars_dict).encode('utf-8')
    return bars_dict

def get_month_before(month : str) -> str:
    """
    gets the month before the one given
    :param month: month to get the one before it. format should be YYYY-MM.
    :return: the month before the given month
    """
    # get the number of the month as an int
    month_number = int(month[-2:])
    # get the string of the year
    year = str(month[:-3])

    # if the month isn't january, decrease it by one, if it is, decrease the year by one and set the month to december
    if month_number > 1:
        month_before_number = month_number-1
        month_before = str(month_before_number)
        if month_before_number < 10:
            month_before = "0" + month_before
        return year + "-" + month_before
    else:
        year_number = int(year)
        year_before = str(year_number - 1)
        return year_before + "-12"
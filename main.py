import pandas as pd
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import uuid
import os
import requests

telegram_bot_api_key = USER = os.getenv('TELEGRAM_BOT_API_KEY')
telegram_bot_chat_id = USER = os.getenv('TELEGRAM_BOT_CHAT_ID')

def send_message(message:str)->None:
    """Send message to me on Telegram when updated.

    Args:
        message (str): String of message to send.
    """    
    requests.post(f'https://api.telegram.org/bot{telegram_bot_api_key}/sendMessage', json={'chat_id': telegram_bot_chat_id, 'text': message})  

def store_df_as_csv(df:pd.DataFrame)->None:
    """Store dataframe as a CSV file.

    Args:
        df (pd.DataFrame): Dataframe of fixtures.
    """    
    df.to_csv('./fixtures.csv', index=False)
def compare_dfs(df:pd.DataFrame)->bool:
    """Compare the latest DF with the stored DF for any changes.

    Args:
        df (pd.DataFrame): Latest copy of fixtures in dataframe

    Returns:
        bool: True if match, False if no match.
    """    
    df2 = pd.read_csv('./fixtures.csv')
    return df.equals(df2)

def write_calendar(cal:Calendar)->None:
    """Write the cal object to an ics file.

    Args:
        cal (Calendar): iCalendar object with all the ics details.
    """    
    f = open(os.path.join('./', 'fixtures.ics'), 'wb')
    f.write(cal.to_ical())
    f.close()

def does_csv_exist()->bool:
    """Check if the CSV file exists.

    Returns:
        bool: True if CSV file exists, False if not.
    """    
    return os.path.isfile('./fixtures.csv')

def create_ical_file(df:pd.DataFrame, cal:Calendar)->None:
    """Create an iCalendar file from a dataframe.

    Args:
        df (pd.DataFrame): Dataframe of fixtures.
        cal (Calendar): iCalendar object with all the ics details.
    """    
    for index, row in df.iterrows():
        event = Event()
        print(row['Date / Time'], row['Home Team'], row['Away Team.1'], row['Venue'])
        start_date_time = datetime.strptime(row['Date / Time'], '%d/%m/%y %H:%M')
        # Set default 8am start time to normal 930 kickoff time.
        if start_date_time.hour == 8:
            start_date_time = start_date_time + timedelta(hours=1, minutes=30)
        # Arrival time is 30 mins before kickoff time.
        arrival_time = start_date_time + timedelta(minutes=-30)
        event.add('summary', str(row['Home Team']) + f" {str(row['Unnamed: 4'])} " + str(row['Away Team.1']))
        event.add('description', f'Arrive by - {arrival_time}')
        event.add('dtstart', start_date_time)
        # End 2 hours after start_date_time
        event.add('dtend', start_date_time + timedelta(hours=2))
        event.add('dtstamp', start_date_time)
        event.add('uid', str(uuid.uuid4()))
        event.add('location', str(row['Venue']))
        cal.add_component(event)
    write_calendar(cal)

cal = Calendar()
cal.add('prodid', 'Down Grange Pumas Fixtures')
cal.add('version', '2.0')
url = "https://fulltime.thefa.com/fixtures.html?selectedSeason=19010414&selectedFixtureGroupAgeGroup=11&selectedFixtureGroupKey=1_579285719&selectedDateCode=all&selectedClub=&selectedTeam=466317969&selectedRelatedFixtureOption=3&selectedFixtureDateStatus=&selectedFixtureStatus=&previousSelectedFixtureGroupAgeGroup=11&previousSelectedFixtureGroupKey=1_579285719&previousSelectedClub=&itemsPerPage=25"
df = pd.read_html(url)[0]
df.head()
exists = does_csv_exist()
if exists:
    no_change = compare_dfs(df)
    if not no_change:
        print("Fixtures updated, ical updated")
        store_df_as_csv(df)
        create_ical_file(df, cal)
        send_message("Fixtures updated, ical updated")
    else:
        print("Fixtures not updated, no update to ical")
else:
    store_df_as_csv(df)
    create_ical_file(df, cal)
    send_message("New ical file created")
    print("New ical file created")

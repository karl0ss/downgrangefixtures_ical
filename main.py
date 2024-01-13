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

def store_df_as_csv(df:pd.DataFrame, name:str)->None:
    """Store dataframe as a CSV file.

    Args:
        df (pd.DataFrame): Dataframe of fixtures.
        name (str): Name of the CSV file.
    """    
    df.to_csv(f'./{name}.csv', index=False)
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

def make_ordinal(n:int)->str:
    '''
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    '''
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix

def create_ical_file(df:pd.DataFrame, cal:Calendar, table:pd.DataFrame)->None:
    """Create an iCalendar file from a dataframe.

    Args:
        df (pd.DataFrame): Dataframe of fixtures.
        cal (Calendar): iCalendar object with all the ics details.
        table (pd.DataFrame): Dataframe of table details.
    """    
    for index, row in df.iterrows():
        event = Event()
        match_type = str(row['Type']) 
        home_team = str(row['Home Team'])
        if ("Tongham") not in home_team:
            home_team = str(row['Home Team']).replace(" U12","")
        away_team = str(row['Away Team.1'])            
        if ("Tongham") not in away_team:
            away_team = str(row['Away Team.1']).replace(" U12","")
        venue = str(row['Venue'])
        print(row['Date / Time'], home_team, away_team, venue)
        start_date_time = datetime.strptime(row['Date / Time'], '%d/%m/%y %H:%M')
        # Set default 8am start time to normal 930 kickoff time.
        if start_date_time.hour == 8:
            start_date_time = start_date_time + timedelta(hours=1, minutes=30)
        # Arrival time is 30 mins before kickoff time.
        arrival_time = start_date_time + timedelta(minutes=-30)
        if match_type == 'L':
            summary = "(League) " + home_team + f" ({make_ordinal(table.loc[table['Team'] == home_team, 'POS'].iloc[0])})" + f" {str(row['Unnamed: 4'])} " + away_team + f" ({make_ordinal(table.loc[table['Team'] == away_team, 'POS'].iloc[0])})"
        else:
            summary = "(Cup) " + home_team + f" {str(row['Unnamed: 4'])} " + away_team            
        event.add('summary', summary)
        notes = row['Status / Notes']
        if pd.isna(notes):
            notes = 'None'
        event.add('description', "Arrive by - " + str(arrival_time) + "\n Notes - " + notes + "\n Table - \n" + str(table))
        event.add('dtstart', start_date_time)
        # End 2 hours after start_date_time
        event.add('dtend', start_date_time + timedelta(hours=2))
        event.add('dtstamp', start_date_time)
        event.add('uid', str(uuid.uuid4()))
        event.add('location', venue)
        cal.add_component(event)
    write_calendar(cal)
    
def process_table():
    table_df = pd.read_html("https://fulltime.thefa.com/table.html?selectedSeason=19010414&selectedDivision=165601607&ftsTablePageContent.fixtureAnalysisForm.standingsTableDay=13&ftsTablePageContent.fixtureAnalysisForm.standingsTableMonth=0&ftsTablePageContent.fixtureAnalysisForm.standingsTableYear=2024&activeTab=1")[0]    
    table_df = table_df[:-1]
    table_df.drop(table_df.columns[len(table_df.columns)-1], axis=1, inplace=True)
    table_df['POS'] = table_df['POS'].astype('Int64')
    table_df['P'] = table_df['P'].astype('Int64')
    table_df['W'] = table_df['W'].astype('Int64')
    table_df['D'] = table_df['D'].astype('Int64')
    table_df['L'] = table_df['L'].astype('Int64')
    table_df['PTS'] = table_df['PTS'].astype('Int64')
    store_df_as_csv(table_df, "table")
    return table_df

cal = Calendar()
cal.add('prodid', 'Down Grange Pumas Fixtures')
cal.add('version', '2.0')
fixtures_df = pd.read_html("https://fulltime.thefa.com/fixtures.html?selectedSeason=19010414&selectedFixtureGroupAgeGroup=11&selectedFixtureGroupKey=1_579285719&selectedDateCode=all&selectedClub=&selectedTeam=466317969&selectedRelatedFixtureOption=3&selectedFixtureDateStatus=&selectedFixtureStatus=&previousSelectedFixtureGroupAgeGroup=11&previousSelectedFixtureGroupKey=1_579285719&previousSelectedClub=&itemsPerPage=25")[0]
fixtures_df.head()
table = process_table()
exists = does_csv_exist()
if exists:
    no_change = compare_dfs(fixtures_df)
    if not no_change:
        print("Fixtures updated, ical updated")
        store_df_as_csv(fixtures_df, "fixtures")
        create_ical_file(fixtures_df, cal, table)
        send_message("Fixtures updated, ical updated")
    else:
        print("Fixtures not updated, no update to ical")
else:
    store_df_as_csv(fixtures_df, "fixtures")
    create_ical_file(fixtures_df, cal, table)
    send_message("New ical file created")
    print("New ical file created")

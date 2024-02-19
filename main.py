import pandas as pd
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import uuid
import os
import csv
import requests
import lxml.html as lh

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
def compare_dfs(df:pd.DataFrame, name:str)->bool:
    """Compare the latest DF with the stored DF for any changes.

    Args:
        df (pd.DataFrame): Latest copy of fixtures in dataframe
        name (str): Name of the CSV file.

    Returns:
        bool: True if match, False if no match.
    """    
    df2 = pd.read_csv(f'./{name}.csv')
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
        if row['Date / Time'] == 'TBC':
            continue
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
            notes = 'No Match Notes'
        elif notes == 'Postponed':
            continue
        event.add('description', "Arrive by - " + str(arrival_time) + "\n" + notes + "\nTable -\n" + "https://fulltime.thefa.com/index.html?league=9268728&selectedSeason=19010414&selectedDivision=165601607&selectedCompetition=0&selectedFixtureGroupKey=1_579285719")
        event.add('dtstart', start_date_time)
        # End 2 hours after start_date_time
        event.add('dtend', start_date_time + timedelta(hours=2))
        event.add('dtstamp', start_date_time)
        event.add('uid', str(uuid.uuid4()))
        event.add('location', venue)
        cal.add_component(event)
    write_calendar(cal)
    
def process_table(table_df:pd.DataFrame)->pd.DataFrame:
    table_df = table_df[:-1]
    table_df.drop(table_df.columns[len(table_df.columns)-1], axis=1, inplace=True)
    table_df['POS'] = table_df['POS'].astype('int')
    table_df['P'] = table_df['P'].astype('int')
    table_df['W'] = table_df['W'].astype('int')
    table_df['D'] = table_df['D'].astype('int')
    table_df['L'] = table_df['L'].astype('int')
    table_df['PTS'] = table_df['PTS'].astype('int')
    store_df_as_csv(table_df, "table")
    return table_df

def process_results()->None:
    req = requests.get("https://fulltime.thefa.com/results.html?selectedSeason=19010414&selectedFixtureGroupAgeGroup=11&selectedFixtureGroupKey=1_579285719&selectedRelatedFixtureOption=3&selectedClub=&selectedTeam=466317969&selectedDateCode=all&previousSelectedFixtureGroupAgeGroup=11&previousSelectedFixtureGroupKey=1_579285719&previousSelectedClub=")

    doc = lh.fromstring(req.text)
    headers = ['Date', 'Home Team', 'Score', 'Away Team']

    with open('results.csv', 'w', newline='') as fp:
        file = csv.writer(fp)    
        file.writerow(headers)    
        for idx,row in enumerate(doc.xpath("//div[contains(@id,'fixture')]"), start=1):
            date = row.xpath(f'/html[1]/body[1]/main[1]/div[2]/section[1]/div[1]/div[3]/div[1]/div[2]/div[{idx}]/div[1]/div[3]/a[1]/span[1]//text()')[0]
            home_team = row.xpath(f'/html[1]/body[1]/main[1]/div[2]/section[1]/div[1]/div[3]/div[1]/div[2]/div[{idx}]/div[1]/div[4]/div[1]/a[1]//text()')[0].strip()
            score = row.xpath(f'/html[1]/body[1]/main[1]/div[2]/section[1]/div[1]/div[3]/div[1]/div[2]/div[{idx}]/div[1]/div[5]//text()')[0].strip()
            if score == 'X - X':
                continue
            away_team = row.xpath(f'/html[1]/body[1]/main[1]/div[2]/section[1]/div[1]/div[3]/div[1]/div[2]/div[{idx}]/div[1]/div[6]/div[2]/a[1]//text()')[0].strip()
            file.writerow([date,home_team,score,away_team])

def compare_table():
    table_df = pd.read_html("https://fulltime.thefa.com/table.html?league=9268728&selectedSeason=19010414&selectedDivision=165601607&selectedCompetition=0&selectedFixtureGroupKey=1_579285719")[0]    
    store_df_as_csv(table_df, "base_table")
    return table_df

cal = Calendar()
cal.add('prodid', 'Down Grange Pumas Fixtures')
cal.add('version', '2.0')
fixtures_df = pd.read_html("https://fulltime.thefa.com/fixtures.html?selectedSeason=19010414&selectedFixtureGroupAgeGroup=11&selectedFixtureGroupKey=1_579285719&selectedDateCode=all&selectedClub=&selectedTeam=466317969&selectedRelatedFixtureOption=3&selectedFixtureDateStatus=&selectedFixtureStatus=&previousSelectedFixtureGroupAgeGroup=11&previousSelectedFixtureGroupKey=1_579285719&previousSelectedClub=&itemsPerPage=25")[0]
fixtures_df.head()
process_results()
table = compare_table()
exists = does_csv_exist()
if exists:
    fixtures_change = compare_dfs(fixtures_df, "fixtures")
    table_change = compare_dfs(table, "base_table")
    if not table_change:
        send_message("Table has updated")
    if not all([fixtures_change, table_change]):
        print("Data Updated, ical updated")
        store_df_as_csv(fixtures_df, "fixtures")
        create_ical_file(fixtures_df, cal, process_table(table))
        send_message("Fixtures updated, ical updated")
    else:
        print("No Data Updated, No update to ical")
else:
    store_df_as_csv(fixtures_df, "fixtures")
    create_ical_file(fixtures_df, cal, process_table(table))
    send_message("New ical file created")
    print("New ical file created")

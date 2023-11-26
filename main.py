import pandas as pd
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import uuid
import os

def store_df_as_csv(df:pd.DataFrame)->None:
    """_summary_

    Args:
        df (pd.DataFrame): _description_
    """    
    df.to_csv('./fixtures.csv', index=False)
def compare_dfs(df:pd.DataFrame)->bool:
    """_summary_

    Args:
        df (pd.DataFrame): _description_

    Returns:
        bool: _description_
    """    
    df2 = pd.read_csv('./fixtures.csv')
    return df.equals(df2)

def write_calendar(cal:Calendar)->None:
    """_summary_

    Args:
        cal (Calendar): _description_
    """    
    f = open(os.path.join('./', 'fixtures.ics'), 'wb')
    f.write(cal.to_ical())
    f.close()

def does_csv_exist()->bool:
    """_summary_

    Returns:
        bool: _description_
    """    
    return os.path.isfile('./fixtures.csv')

def create_ical_file(df, cal)->None:
    for index, row in df.iterrows():
        event = Event()
        print(row['Date / Time'], row['Home Team'], row['Away Team.1'], row['Venue'])
        start_date_time = datetime.strptime(row['Date / Time'], '%d/%m/%y %H:%M')
        if start_date_time.hour == 8:
            start_date_time = start_date_time + timedelta(hours=1, minutes=30)
        arrival_time = start_date_time + timedelta(minutes=-30)
        event.add('summary', str(row['Home Team']) + " vs " + str(row['Away Team.1']))
        event.add('description', f'Arrive by - {arrival_time}')
        event.add('dtstart', start_date_time)
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
        store_df_as_csv(df)
        create_ical_file(df, cal)
else:
    store_df_as_csv(df)
    create_ical_file(df, cal)
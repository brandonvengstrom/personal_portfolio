import pandas as pd
import os 
from bs4 import BeautifulSoup
import time
from datetime import datetime
from io import StringIO
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeOut

start = datetime.today()
# Setting variables ----------------------------------------------------------------------------------
base_url = '''https://www.sports-reference.com'''
start_season = 2022
current_year = datetime.now().year
# Creates list of seasons pre current year
seasons = [i for i in range(start_season, current_year)]

# File Directories 
base_path = os.getcwd()
save_folder = os.path.join(base_path, 'html_data')
season_folder = os.path.join(save_folder, 'season')
team_folder = os.path.join(save_folder, 'team')

# Definations ----------------------------------------------------------------------------------------
# Get HTML
# Playwright was used due to the nature of the site using Java script in order to load the bottom half of the webpage that requests was not recognizing
def get_html(url, selector, sleep=5, retries=3):
    '''Makes request to pull html with a given CSS selector from given url Sleeps for {sleep} seconds and multiplies by {retries}'''
    html = None
    for i in range(1, retries +1):
        time.sleep(sleep*i)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url)
                html = page.inner_html(selector)
        except PlaywrightTimeOut:
            print(f'Time out error on {url}')
            continue
        else:
            break
    return html

# Scrape Season 
def season_scrape(year: int):
    '''Scrapes season standing for CFB for a given year and saves HTML to directory'''
    realtive_url = f'/cfb/years/{year}-standings.html'
    season_url = base_url+realtive_url
    save_path = os.path.join(season_folder, season_url.split("/")[-1])
    if os.path.exists(save_path):
        pass 
    else:
        season_standings_html = get_html(season_url, '#div_standings')
        if season_standings_html is None:
            pass
        with open(save_path, "w+") as f:
            f.write(str(season_standings_html))

# Parse Season
def parse_season(path) -> list:
    '''Parsese Season Data into team specfic links'''
    with open (path, "r") as f:
        html = f.read()
    html = BeautifulSoup(html, features='lxml')
    team_links = html.find_all('a')
    team_links = [links.get("href") for links in team_links]
    team_links = [links for links in team_links if '/schools/' in links]
    team_links = [base_url + link for link in team_links]
    return team_links

# Team Translation
def team_name_translattion(path):
    '''From the seasons table grabs teams name and link refrence in order to create a translation table'''
    with open(path, "r") as f:
        html=f.read()
    html = BeautifulSoup(html, features='lxml')
    html = html.select('table.stats_table')[0]
    table = pd.read_html(StringIO(str(html)))[0].droplevel(0, axis=1)
    table = table[['School', 'Conf']]
    table = table[table['School'] != 'School']
    table = table.dropna(subset='School')
    # Finding Links to Teams
    team_links = []
    for rows in html.findAll("tr"):
        row = rows.findAll("td")
        for each in row:
            try:
                link = each.find('a')['href']
                team_links.append(link)
            except:
                pass
    team_links = [links for links in team_links if '/schools/' in links]
    tranlastion = [link.split("/")[-2].replace("-", ' ').title() for link in team_links]
    # table['Link'] = team_links
    table['Tranlastion'] = tranlastion
    return table

# Get Team Data
def get_game_log(url: str):
    '''Given A Team & Season specfic URL Returns HTML for gamelog from CFB Refrence'''
    # Grabbing Team Home Table
    year = url.split("/")[-1].replace(".html", '')
    team = url.split("/")[-2].replace("-", '_').title()
    team_year = team + "_" + year
    game_log_url = url.replace('.html','/gamelog/')
    save_path = os.path.join(team_folder, team_year)
    if os.path.exists(save_path):
        pass 
    else:
        # Scrapping Game Log
        game_log_html = get_html(game_log_url, '#content')
        if game_log_html is None:
            pass
        with open(save_path, "w+") as f:
            f.write(str(game_log_html))

# Parse Team Data 
def parse_team(path) -> pd.DataFrame:
    '''Takes path to team HTML and retursn game log stats'''
    with open(path, 'r') as f:
        html = f.read()
    year = path.split("\\")[-1].replace(".html",'')[-4:]
    team = path.split("\\")[-1].replace(".html",'')[:-5].replace("_", " ").title()
    # Pulling Team Data
    offense = pd.read_html(StringIO(html), match="Offensive Game Log Table")[0]
    defense = pd.read_html(StringIO(html), match="Defensive Game Log Table")[0]
    # Fixing Index
    offense.columns = ['_'.join((col[0], col[1])) if 'Unnamed' not in col[0] else col[1] for col in offense.columns]
    offense['Team'] = team
    defense.columns = ['_'.join((col[0], col[1])) if 'Unnamed' not in col[0] else col[1] for col in defense.columns]
    defense['Team'] = team
    stats = pd.merge(
         left= offense
        ,right= defense
        ,on = ['Team', 'Date']
        ,how = 'left'
        ,suffixes=('_off', '_def')
    )
    # Adding team name to data frame
    stats['Team'] = team
    stats['Season'] = year
    # Removing Unwanted Row 
    stats = stats.dropna(subset="Opponent_off")
    return stats

# Scraping and Parsing Data ----------------------------------------------------------------------
# Running scrape for seasons
for season in seasons:
    season_scrape(season)

# Parsing season data  
start = datetime.today()
season_files = os.listdir(season_folder)
translation_list = []
for file in season_files:
    path = os.path.join(season_folder, file)
    team_links = parse_season(path=path)
    for links in team_links:
        get_game_log(links)
    traslation = team_name_translattion(path)
    translation_list.append(traslation)

# Combining translation list 
dim_translation = pd.concat(translation_list)

# Parsing Team Data 
team_files = os.listdir(team_folder)
test_file = team_files[1]
path = os.path.join(team_folder, test_file)
team_frame = parse_team(path)

# # Combing Data 
# Runnig for all data scraped  
team_files = os.listdir(team_folder)
all_stas = [parse_team(os.path.join(team_folder, files)) for files in team_files]
all_team_stats = pd.concat(all_stas)
all_team_stats = all_team_stats.drop(['Opponent_def'] ,axis=1)
all_team_stats = all_team_stats.rename(
     columns= {'Opponent_off': 'Opponent'}
    )


# Determing Post Season 
all_team_stats['is_post_season'] = all_team_stats['Opponent'].str.contains(r'\*', na=False)
all_team_stats['Opponent'] = all_team_stats['Opponent'].str.replace('*', '')

# Team Translations ---------------------------------------------------------------------------------------------
# Team
dim_translation = dim_translation.drop_duplicates(subset='School').reset_index(drop=True)
translation_join = pd.merge(
     left=all_team_stats
    ,right=dim_translation
    ,left_on=['Team']
    ,right_on =['Tranlastion']
    ,how='left'
)
all_team_stats = translation_join.drop(['Tranlastion', 'Team'], axis=1)
all_team_stats = all_team_stats.rename(columns= {'School': 'Team'})

# Oppenent
dim_translation_two = dim_translation.drop(['Conf'], axis=1)
translation_join = pd.merge(
     left=all_team_stats
    ,right=dim_translation_two
    ,left_on=['Opponent']
    ,right_on =['Tranlastion']
    ,how='left'
)

# If translastion exsists use translation elese use what was pre existing
translation_join['School'] = translation_join['School'].combine_first(translation_join['Opponent'])
all_team_stats = translation_join.drop(['Tranlastion', 'Opponent'], axis=1)
all_team_stats = all_team_stats.rename(columns= {'School': 'Opponent'})

# Saving File to CSV to be used latter
fille_name = f'webscrapped_cfb_stats_{seasons[0]}-{seasons[-1]}.csv'
file_path = os.path.join(save_folder, fille_name)
print(f'Saving file to {file_path}')
all_team_stats.to_csv(file_path, index=False)

# Runtime -------------------------------------------------------------------------------------------
print(f'Runtime: {datetime.today() - start}')

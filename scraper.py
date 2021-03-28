from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd

def scrape(url):
    html = urlopen(url)

    soup = BeautifulSoup(html)

    headers = [th.getText() for th in soup.findAll('tr', limit=2)[0].findAll('th')][1:] # Gets all column headers

    rows = soup.findAll('tr')[1:]
    stats = [[td.getText() for td in rows[i].findAll('td')]
                for i in range(len(rows))]

    return pd.DataFrame(data = stats, columns = headers)

# Team abbreviations... Teams with a space get two entries, one for each word, because of the way I determine teams later
abbrevs = {
    "Atlanta": "ATL",
    "Brooklyn": "BKN",
    "Boston": "BOS",
    "Charlotte": "CHA",
    "Chicago": "CHI",
    "Cleveland": "CLE",
    "Dallas": "DAL",
    "Denver": "DEN",
    "Detroit": "DET",
    "State": "GSW",
    "Golden": "GSW",
    "Houston": "HOU",
    "Indiana": "IND",
    "Clippers": "LAC",
    "Lakers": "LAL",
    "Memphis": "MEM",
    "Miami": "MIA",
    "Milwaukee": "MIL",
    "Minnesota": "MIN",
    "New Orleans": "NOP",
    "Orleans": "NOP",
    "New York": "NYK",
    "York": "NYK",
    "New Jersey": "NJ",
    "Jersey": "NJ",
    "Oklahoma": "OKC",
    "City": "OKC",
    "Orlando": "ORL",
    "Philadelphia": "PHI",
    "Phoenix": "PHX",
    "Portland": "POR",
    "Sacramento": "SAC",
    "San": "SAS",
    "Seattle": "SEA",
    "Antonio": "SAS",
    "Toronto": "TOR",
    "Utah": "UTA",
    "Vancouver": "VAN",
    "Washington": "WAS"
}

def pbp_scrape(d,m,yr):
    """
    This function takes a date and scrapes all the play by play data on that date
    from BasketballReference
    """
    box_score_url = "https://www.basketball-reference.com/boxscores/?month="+m+"&day="+d+"&year="+yr

    box_scores = urlopen(box_score_url)

    soup1 = BeautifulSoup(box_scores, features = "html.parser")

    columns = ["Day", "Month", "Year", "GameType", "HomeTm", "AwayTm", "PlayFor", "Time", "Quarter","Score", "Shooter", "ShotType","ShotOutcome","ShotDist",
                    "Blocker", "Assister", "Rebounder", "ReboundType", "Fouler", "Fouled", "FoulType", "TO_by", "TO_type","Stealer"]
    
    all_data = pd.DataFrame(columns = columns)

    urls = [link.get('href') for link in soup1.findAll("a")]

    if any("Series Summary" in link for link in urls):
        all_data["GameType"] = "Playoff"
    else:
        all_data["GameType"] = "Regular"


    urls = [link for link in urls if "pbp" in link]
    

    for url in urls:

        html = urlopen("https://www.basketball-reference.com/"+url)

        soup = BeautifulSoup(html, features = "html.parser")


        plays = [i.getText() for i in soup.findAll('tr')] # Get all the rows
    
        # Make rows less hectic... it's an ugly line but it gets the job done
        plays = [i.replace("\xa0\xa0", "_").replace("\xa0", "_").replace("+1", "_").replace("+2", "_").replace("+3", "_").replace("\n", " ")[1:-1] 
                    for i in plays]

        teams = plays[1].split(" ")
        homeTm, awayTm = teams[1], teams[-1]

        # Accounting for possible repeats in team names LA and New
        if homeTm == "LA":
            homeTm = teams[2]
        if homeTm == "New" and teams[2] == "Orleans":
            homeTm = "New Orleans"
        if homeTm == "New" and teams[2] == "York":
            homeTm = "New York"
        if homeTm == "New" and teams[2] == "Jersey":
            homeTm = "New Jersey"
    
        plays = [play for play in plays if (":" in play and "End of" not in play)] # removes all the 1st Q, 2nd Q, teams etc.

        

        data = pd.DataFrame(index = range(len(plays)-1), columns = columns) # len(plays)-1 since I don't keep the jump ball

        data["Day"] = d
        data["Month"] = m
        data["Year"] = yr
        data["HomeTm"] = abbrevs[homeTm]
        data["AwayTm"] = abbrevs[awayTm]

        div = str(soup.find_all("div", {"id": "all_other_scores"})[0])[350:500] # Just want to check if the word 'series' is in here and it would occur early, so don't need the entire string

        if "Series" in div:
            data["GameType"] = "Playoff"
        else:
            data["GameType"] = "Regular"
    
        quarter = 1

        for i in enumerate(plays[1:]): # 1st play onwards since the zeroth play is the jump ball... Maybe I'll add in a column for jump ball later
            index = i[0]
            play = i[1]
            data["Quarter"][index] = quarter
            if ":" in play:
                data["Time"][index] = play[:play.index(":")+5]
                play = play[play.index(":")+6:] # Whenever I do this it's just to make indexing easier later

            if "Start of" in play:
                quarter+=1
                continue

            if "_" in play:
                # Use the index of the underscore to figure out which team made the play, and where in the string the score is
                if play[0] == "_":
                    data["PlayFor"][index] = abbrevs[awayTm]
                    data["Score"][index] = play[1: play[1:].index("_")+1]
                    play = play[play[1:].index("_")+2:]
                else:
                    data["PlayFor"][index] = abbrevs[homeTm]
                    data["Score"][index] = play[play[:-1].index("_")+1:-1]
                    play = play[:play[:-1].index("_")]


            play = play.split(" ")

            if "World" in play: # Ron Artest is the worst for making me do this
                if "Peace" in play:
                    play.remove("Peace")
                    play[play.index("World")] = "World Peace"
                elif "Peace)" in play:
                    play.remove("Peace)")
                    play[play.index("World")] = "World Peace)"


            # Now we determine the type of play and catalogue it accordingly
            # Get ready for a lot of if statements
            if "makes" in play or "misses" in play: # This means there was a shot
                data["Shooter"][index] = play[0] + " " + play[1]


                # Determine if it was a make or a miss and whether there was an assist or block
                if "misses" in play:
                    data["ShotOutcome"][index] = 0
                else:
                    data["ShotOutcome"][index] = 1


                if "(assist" in play:
                    data["Assister"][index] = play[-2] + " " + play[-1][:-1]

                if "(block" in play:
                        data["Blocker"][index] = play[-2] + " " + play[-1][:-1]

                if "free" in play:
                    continue
                elif "ft" in play:
                    data["ShotDist"][index] = int(play[play.index("ft")-1])
                else:
                    data["ShotDist"][index] = 0 # Some of the early years are missing the distances for some plays, I'll just have to live with it being zero


                if "dunk" in play:
                    data["ShotType"][index] = "Dunk"
                elif "layup" in play:
                    data["ShotType"][index] = "Layup"
                elif "free" in play:
                    data["ShotType"][index] = "FT"
                elif "hook" in play:
                    data["ShotType"][index] = "Hook"
                else:
                    if "3-pt" in play:
                        data["ShotType"][index] = "3pt"
                    else:
                        data["ShotType"][index] = "2pt"


            elif "rebound" in play: # This means there was a rebound (super helpful comment)
                if "Team" in play:
                    data["Rebounder"][index] = "Team"
                else:
                    data["Rebounder"][index] = play[-2] +" " + play[-1]
            
                data["ReboundType"][index] = play[0]


            elif "foul" in play and "(drawn" in play: # Foul
                x = play.index("foul") # Just when the word 'foul' occurs in the string

                data["FoulType"][index] = " ".join([i[1] for i in enumerate(play) if i[0]<x])
                data["Fouled"][index] = play[-2] + " " + play[-1][:-1]
                data["Fouler"][index] = play[x+2] + " " + play[x+3]


            elif "Turnover" in play: # TO
                if "Team" in play:
                    data["TO_by"][index] = "Team"
                    y = 3 # Indices changes since there's one less element in the list 'play'
                else:
                    data["TO_by"][index] = play[2] + " " + play[3]
                    y = 4

                if "steal" in play: # This means there was a steal
                    data["Stealer"][index] = play[-2] + " " + play[-1][:-1]

                    data["TO_type"][index] = " ".join(play[y:-4])[1:-1]
                else:
                    data["TO_type"][index] = " ".join(play[y:])[1:-1]

        all_data = all_data.append(data, ignore_index = True)

    return all_data
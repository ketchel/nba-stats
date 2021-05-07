from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd

def scrape(url):
    html = urlopen(url)

    soup = BeautifulSoup(html, features = "html.parser")

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

    This could probably be made more efficient, but once you run it you'll have the data forever
    so it's not a huge deal if it's a bit slow.
    """
    box_score_url = "https://www.basketball-reference.com/boxscores/?month="+m+"&day="+d+"&year="+yr

    box_scores = urlopen(box_score_url)

    soup1 = BeautifulSoup(box_scores, features = "html.parser")

    columns = ["Day", "Month", "Season", "GameType", "HomeTm", "AwayTm", "PlayFor", "Time", "Quarter","Score", "Shooter", "ShotType","ShotOutcome","ShotDist",
                    "Blocker", "Assister", "Rebounder", "ReboundType", "Fouler", "Fouled", "FoulType", "TO_by", "TO_type","Stealer"]
    
    all_data = pd.DataFrame(columns = columns)

    urls = [link.get('href') for link in soup1.findAll("a")]

    if any("Series Summary" in link for link in urls):
        all_data["GameType"] = "Playoff"
    else:
        all_data["GameType"] = "Regular"

    """
    I feel that there must be a more efficient way to generate
    all the urls on the page that have the pbp data but I can't find
    one in the beautiful soup documentation
    """
    urls = [link for link in urls if "pbp" in link]
    

    for url in urls:

        html = urlopen("https://www.basketball-reference.com/"+url)

        soup = BeautifulSoup(html, features = "html.parser")


        plays = [i.getText() for i in soup.findAll('tr')] # Get all the rows
    
        # Make rows less hectic... it's an ugly line but it gets the job done
        plays = [i.replace("\xa0\xa0", "_").replace("\xa0", "_").replace("+1", "_").replace("+2", "_").replace("+3", "_").replace("\n", " ")[1:-1] 
                    for i in plays]

        # I've seen a typo where there's a +6 somewhere... I added a +5 and +4 just to be safe
        plays = [i.replace("+6","_").replace("+5","_").replace("+4","_") for i in plays]

        teams = plays[1].split(" ")
        homeTm, awayTm = teams[1], teams[-1]

        # Accounting for possible repeats in team names LA and New
        if homeTm == "LA":
            homeTm = teams[2]
        if homeTm == "New" and (teams[2] == "Orleans" or teams[2] == "Orleans/Oklahoma"):
            homeTm = "New Orleans"
        if homeTm == "New" and teams[2] == "York":
            homeTm = "New York"
        if homeTm == "New" and teams[2] == "Jersey":
            homeTm = "New Jersey"
    
        plays = [play for play in plays if (":" in play and "End of" not in play)] # removes all the 1st Q, 2nd Q, teams etc.

        
        data = pd.DataFrame(index = range(len(plays)-1), columns = columns) # len(plays)-1 since I don't keep the jump ball

        
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


            # Some players names have an extra space in them...

            space_players = ["World", "Peace", "Van", "Exel", "Del", "Negro", "Llamas", 
                             "Grey", "Michael", "McAdoo", "Van", "Horn"]

            for i in range(0, len(space_players), 2):
                if space_players[i] in play and space_players[i+1] in play:
                    play.remove(space_players[i+1])
                    play[play.index(space_players[i])] = space_players[i] + " " + space_players[i+1]
                elif space_players[i] in play and space_players [i+1] + ")" in play:
                    play.remove(space_players[i+1] + ")")
                    try:
                        play.index(space_players[i])
                    except:
                        print(play)
                        print(d, m, yr)
                    play[play.index(space_players[i]) ] = space_players[i] + " " + space_players[i+1] + ")"



            # Luc Mbah a Moute gets his own conditional since his name has two extra spaces >:(

            if "Moute" in play:
                    play.remove("a")
                    play.remove("Moute")
                    play[play.index("Mbah")] = "Mbah a Moute"
            elif "Moute)" in play:
                play.remove("a")
                play.remove("Moute)")
                play[play.index("Mbah")] = "Mbah a Moute)"


            # Now determine the type of play and catalogue it accordingly
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

                

                if "ft" in play:
                    data["ShotDist"][index] = int(play[play.index("ft")-1])
                elif "rim" in play:
                    data["ShotDist"][index] = 0
                else:
                    data["ShotDist"][index] = -1 # Some of the early years are missing the distances for some plays


                if "dunk" in play:
                    data["ShotType"][index] = "Dunk"

                elif "free" in play:
                    data["ShotType"][index] = "FT"

                    # This doesn't really work because substitutions might happen between the foul and the foul shots
                    # But the truth is it doesn't really matter for the data I want, and the fouled can be extrapolated
                    # From who takes the foul shot anway
                    data["Fouled"][index - 1] = data["Shooter"][index]
                    data["ShotDist"][index] = 15

                elif "layup" in play:
                    data["ShotType"][index] = "Layup"   
                    
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


            elif "foul" in play: # Foul
                x = play.index("foul") # Just when the word 'foul' occurs in the string

                data["FoulType"][index] = " ".join([i[1] for i in enumerate(play) if i[0]<x])
                
                # Some of the older years are missing the fouler
                try:
                    data["Fouler"][index] = play[x+2] + " " + play[x+3]
                except:
                    data["Fouler"][index] = ""

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

    if int(m) <= 12 and int(m) > 9:
        season = yr[2:] + "-" + str(int(yr)+1)[2:]
    else:
        season = str(int(yr)-1)[2:] +"-" + str(yr)[2:]

    # This info could be stored as a datetime in sql, but I prefer having the season over the year
    all_data["Day"] = d
    all_data["Month"] = m
    all_data["Season"] = season

    return all_data

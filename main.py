import requests
from steam import Steam
from decouple import config
import streamlit as st
import pandas as pd
# import plotly.express as px
from datetime import datetime

api_key = "<api key>"
KEY = config("STEAM_API_KEY")
steam = Steam(KEY)

#METHODS
# Find a Steam account by URL
@st.cache_data
def findUser(url):
    id = url.replace("https://steamcommunity.com/profiles/", "")

    if id == url:
        vanityid = url.replace("https://steamcommunity.com/id/", "")
        id = requests.get(
            f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={api_key}&vanityurl={vanityid}").json()

    # Gets the raw JSON file
    data = requests.get(
        f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key}&steamids={id}").json()

    # If there are no players in the response, return fail
    if data['response']['players'] == []:
        return 1

    # Return the first player in the response
    return data['response']['players'][0]


@st.cache_data
def findApp(id):
    # I would not use this, getOwnedGames provides all the info you would need anyway
    app = requests.get(f"http://store.steampowered.com/api/appdetails?appids={id}").json()

    if app == 'null':
        return 1

    return app[f"{id}"]['data']


@st.cache_data
def getUserAchievements(user, app):
    userID = user["steamid"]
    appID = app["appid"]
    userAch = requests.get(
        f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={api_key}&steamid={userID}&appid={appID}&l=en").json()

    # Will fail if user has private achievements
    # Will fail if user has private achievements or 'achievements' key is missing
    if not userAch["playerstats"]["success"] or "achievements" not in userAch["playerstats"]:
        return 1

    return userAch["playerstats"]["achievements"]


@st.cache_data
def getOwnedGames(user, includeFree):
    userID = user["steamid"]

    ownedGames = requests.get(
        f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={api_key}&steamid={userID}&include_appinfo=true&include_played_free_games={includeFree}&skip_unvetted_apps=true&language=en").json()

    if "games" not in ownedGames["response"]:
        st.warning("User does not own any games.")
        return []

    return ownedGames["response"]["games"]

@st.cache_data
def total_ach(data):
    count = 0
    if isinstance(data, list):
        for i in data:
            if int(i['achieved']) > 0:
                count += int(i['achieved'])
    return count

#Store for table
@st.cache_data
def ach_record(user, gameLibrary):
    directory = {}
    table = {
        'Game Name': [],
        'Total Achievements': []

    }
    for i in gameLibrary:
        achievements = getUserAchievements(user, i)
        directory[i['name']] = achievements
        table['Game Name'].append(i['name'])
        table['Total Achievements'].append(total_ach(achievements))

    return directory, table

@st.cache_data
def get_user_by_name(user_name):
    data = steam.users.search_user(user_name)
    return data

@st.cache_data
def get_user_by_id(user_id):
    try:
        data = steam.users.get_user_details(user_id)
        return data
    except:
        return st.error("An error occurred when retrieving User by Steam ID. Please enter a valid Steam ID.")

@st.cache_data
def get_user_location(data):
    try:
        country = data['loccountrycode']
        df = pd.read_csv("tableConvert.com_c47xbj.csv")
        loc_data = df.loc[df["Alpha-2 code"] == country]
        #st.success(loc_data)
        loc_data = loc_data.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
        st.success("User is from this region")
        st.map(loc_data, zoom=2)
    except:
        st.warning("User's region couldn't be found")

def increment_pages():
    st.session_state.pages += 1


def decrement_pages():
    st.session_state.pages -= 1

@st.cache_data
def printAchievements(app, achievements_dir):
    app_key = app["name"]
    achievements = achievements_dir.get(app_key)

    if len(achievements) == 0:
        st.write("No achievements found for this game.")
    else:
        num_achievements = len([a for a in achievements if a['achieved']])
        if num_achievements == 0:
            st.write("You have not achieved any achievements for this game.")
        else:
            st.write(
                f"You have achieved {num_achievements} out of {len(achievements)} achievements for this game.")
            page_size = 5
            num_pages = (num_achievements + page_size - 1) // page_size

            col1, col2 = st.columns(2)
            if st.session_state.pages > 1:
                col1.button("◀️", on_click=decrement_pages)
            if st.session_state.pages < num_pages:
                col1.button("▶️️", on_click=increment_pages)
            start_idx = (st.session_state.pages - 1) * page_size
            end_idx = min(start_idx + page_size, num_achievements)
            for achievement in achievements:
                if achievement['achieved']:
                    st.write(f"Name: {achievement['name']}")
                    st.write(f"Description: {achievement['description']}")
                    time_achieved = datetime.utcfromtimestamp(achievement['unlocktime']).strftime(
                        '%Y-%m-%d %H:%M:%S')
                    st.write(f"Achieved on: {time_achieved}")
                    st.write("---")


#HEADER
st.title("Steam User Info")

# Find User By
find_by = ["Name", "User ID"]
category = st.sidebar.selectbox("Find user by:", options= find_by)

if category == "Name":
    agreement = st.checkbox("By checking this box you agree to being aware that the information provided is not stolen. Any data displayed is provided by Steam.")

    if agreement:
        user_name = st.text_input("Enter a username")
        submit_user =st.button("Submit")
        if submit_user:
            user_data = get_user_by_name(user_name)
            if user_data == "No match":
                st.error("No Match Found")
            else:
                user = findUser(user_name)
                #st.success(user_data)
                user_player = user_data["player"]
                user_player_name = user_player["personaname"]
                #display_name = "User's Player Name: " + user_player_name
                #st.subheader(display_name)
                if user == 1:
                    st.error("No Match Found")
                else:

                    # Display Player found
                    st.success("Player Found")
                    st.subheader("User's Player Name: " + user['personaname'])
                    st.image(user['avatarfull'])
                    loc_data = get_user_location(user_player)
                    gameLibrary = getOwnedGames(user, True)
                    achievements_dir, achievements_table = ach_record(user, gameLibrary)

                    if 'pages' not in st.session_state or 'game' not in st.session_state:
                        st.session_state.pages = 1

                    def printAchs(app):
                        printAchievements(app, achievements_dir)

                    with st.form("Get Achievements"):
                        game = st.selectbox("Select Game", gameLibrary, format_func=lambda x: x['name'])
                        st.form_submit_button("Submit", on_click=printAchs, args=(game,))

                    # total_ach(getUserAchievements(user, game_selected))

                    ach_df = pd.DataFrame(achievements_table)
                    st.dataframe(ach_df)



else:
    agreement = st.checkbox("By checking this box you agree to being aware that the information provided is not stolen. Any data displayed is provided by Steam.")
    if agreement:
        user_id = st.text_input("Enter a ID")
        submit_user = st.button("Submit")
        if submit_user:
            user_data = get_user_by_id(user_id)
            if user_data == "No match":
                st.error("No Match Found")
            else:
                user_player = user_data["player"]
                # st.success(user_data)
                user_name = user_player['personaname']
                user = findUser(user_name)
                # st.success(user_data)

                user_player_name = user_player["personaname"]
                # display_name = "User's Player Name: " + user_player_name
                # st.subheader(display_name)
                if user == 1:
                    st.error("No Match Found")
                else:

                    # Display Player found
                    st.success("Player Found")
                    st.subheader("User's Player Name: " + user['personaname'])
                    st.image(user['avatarfull'])
                    #gameLibrary = getOwnedGames(user, True)

                    loc_data = get_user_location(user_player)
                    gameLibrary = getOwnedGames(user, True)

                    #gameOption = st.selectbox("Select Game", gameLibrary, index=0, format_func=lambda x: x['name'])
                    # st.subheader(getUserAchievements(user, gameOption))
                    #total_ach(getUserAchievements(user, gameOption))
                    ach_for_player = ach_record(user, gameLibrary)

                    ach_df = pd.DataFrame(ach_for_player)
                    st.dataframe(ach_df)


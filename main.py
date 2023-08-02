import streamlit as st
import requests
import pandas as pd
import plotly.express as px

api_key = "<API KEY>"

#METHODS

#Find a Steam account by URL
@st.cache_data
def findUser(url):
    id = url.replace("https://steamcommunity.com/profiles/", "")

    if id == url:
        vanityid = url.replace("https://steamcommunity.com/id/", "")
        id = requests.get(f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={api_key}&vanityurl={vanityid}").json()

    #Gets the raw JSON file
    data = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key}&steamids={id}").json()

    #If there are no players in the response, return fail
    if data['response']['players'] == []:
        return 1

    #Return the first player in the response 
    return data['response']['players'][0]

@st.cache_data
def findApp(id):
    #I would not use this, getOwnedGames provides all the info you would need anyway
    app = requests.get(f"http://store.steampowered.com/api/appdetails?appids={id}").json()

    if app == 'null':
        return 1

    return app[f"{id}"]['data']


@st.cache_data
def getUserAchievements(user, app):
    userID = user["steamid"]
    appID = app["appid"]
    userAch = requests.get(f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={api_key}&steamid={userID}&appid={appID}").json()

    #Will fail if user has private achievements
    if userAch["playerstats"]["success"] == False:
        return 1

    return userAch["playerstats"]["achievements"]

@st.cache_data
def getOwnedGames(user, includeFree):
    userID = user["steamid"]

    ownedGames = requests.get(f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={api_key}&steamid={userID}&include_appinfo=true&include_played_free_games={includeFree}&skip_unvetted_apps=true&language=en").json()


    return ownedGames["response"]["games"]


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




def main():
    st.title("STEAM API")
    st.header("Steam User Info")

    find_by = []
    category = st.sidebar.selectbox("Find user by:", options= find_by)

    agreement = st.checkbox("By checking this box you agree to being aware that the information provided is not stolen. Any data displayed is provided by Steam.")
    if agreement:
        userInput = st.text_input("Enter a Steam Profile URL or Username")
        submitUser = st.button("Submit")
        if submitUser:
            user = findUser(userInput)
            if user == 1:
                st.error("No Match Found")
            else:

                #Display Player found
                st.success("Player Found")
                st.subheader("User's Player Name: " + user['personaname'])
                st.image(user['avatarfull'])
                loc_data = get_user_location
                gameLibrary = getOwnedGames(user, True)
                

                gameOption = st.selectbox("Select Game", gameLibrary, index=0, format_func= lambda x: x['name'])
                st.subheader(getUserAchievements(user, gameOption))
                
        


    

from steam import Steam
from decouple import config
import streamlit as st
import pandas as pd
import plotly.express as px


KEY = config("STEAM_API_KEY")
steam = Steam(KEY)
#METHODS
@st.cache_data
def get_user_by_name(user_name):
    data = steam.users.search_user(user_name)
    return data

@st.cache_data
def get_user_location(data):
    try:
        country = data['loccountrycode']
        df = pd.read_csv("tableConvert.com_c47xbj.csv")
        loc_data = df.loc[df["Alpha-2 code"] == country]
        #st.success(loc_data)
        loc_data = loc_data.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
        st.map(loc_data, zoom=2)
    except:
        st.warning("User's region couldn't be found")

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
                #st.success(user_data)
                user_player = user_data["player"]
                user_player_name = user_player["personaname"]
                display_name = "User's Player Name: " + user_player_name
                st.subheader(display_name)
                loc_data = get_user_location(user_player)


else:
    st.warning("Section Not Finished")

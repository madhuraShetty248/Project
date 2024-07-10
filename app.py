import streamlit as st
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time
import plotly.express as px
import pandas as pd
import sqlite3
from PIL import Image
import os
import base64


# Database functions
def init_db():
    conn = sqlite3.connect('toll_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY, user_id INTEGER, 
                  start_lat REAL, start_lon REAL,
                  end_lat REAL, end_lon REAL, 
                  distance REAL, toll REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()


def add_user(username):
    conn = sqlite3.connect('toll_system.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()


def add_transaction(username, start_lat, start_lon, end_lat, end_lon, distance, toll):
    conn = sqlite3.connect('toll_system.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user_id = c.fetchone()[0]
    c.execute('''INSERT INTO transactions 
                 (user_id, start_lat, start_lon, end_lat, end_lon, distance, toll) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (user_id, start_lat, start_lon, end_lat, end_lon, distance, toll))
    conn.commit()
    conn.close()


def get_transaction_history(username):
    conn = sqlite3.connect('toll_system.db')
    query = '''SELECT transactions.* FROM transactions
               JOIN users ON transactions.user_id = users.id
               WHERE users.username = ?'''
    df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()
    return df


# Toll calculation
def calculate_toll(distance):
    base_rate = 0.1  # $0.1 per km
    return distance * base_rate


# Geocoding functions
@st.cache_resource
def get_geocoder():
    return Nominatim(user_agent="my_toll_app")


def geocode_address(address, geocoder):
    try:
        location = geocoder.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except (GeocoderTimedOut, GeocoderUnavailable):
        st.error("Geocoding service is unavailable. Please try again later.")
        return None


def calculate_distance(start_coords, end_coords):
    return geodesic(start_coords, end_coords).kilometers


# Page functions
def get_started():
    st.set_page_config(layout="wide")  # Set the page to wide mode

    # Add custom CSS for centering and styling
    st.markdown("""
        <style>
        .title {
            text-align: center;
            padding: 1rem 0;
            color: white;
            background-color: rgba(0,0,0,0.6);
            position: relative;
            z-index: 1000;
        }
        .stButton>button {
            position: relative;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
        }
        .fullscreen-bg {
            display: block;
            margin: 1rem auto;
            width: 50%; /* Adjust the size of the image */
            height: auto;
            z-index: 500;
        }
        </style>
        """, unsafe_allow_html=True)

    # Title in the middle
    st.markdown("<h1 class='title'>Welcome To The GPS Toll-Based System Simulation</h1>", unsafe_allow_html=True)

    # Create three columns for the button
    col1, col2, col3 = st.columns([1, 2, 1])

    # Place the button in the middle column
    with col2:
        if st.button("Get Started", key="start_button"):
            st.session_state.page = "email"
            st.experimental_rerun()

    # Load and display the image
    image_path = r"C:\Users\madhu\Downloads\image.jpeg"
    if os.path.exists(image_path):
        image = Image.open(image_path)
        st.markdown(
            f"""
            <img src="data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" class="fullscreen-bg">
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("Welcome image not found. Please check the image path.")


def enter_email():
    st.title("Enter Your Email Address")
    email = st.text_input("Email Address")
    if st.button("Submit"):
        if email:
            st.session_state.email = email
            st.session_state.page = "simulation"
            st.experimental_rerun()
        else:
            st.error("Please enter a valid email address.")


def simulation():
    st.title("🚗GPS Toll-Based System Simulation")
    st.write(f"Welcome, {st.session_state.email}!")
    st.write("This is a simulation of a GPS toll-based system.")

    init_db()
    geocoder = get_geocoder()

    with st.sidebar:
        st.title("User Information")
        username = st.text_input("Enter your username")
        if username:
            add_user(username)

    tabs = st.tabs(["Route Simulation", "Transaction History"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            start_address = st.text_input("Enter the starting address")
        with col2:
            end_address = st.text_input("Enter the destination address")

        if st.button("Simulate Route", key="simulate"):
            with st.spinner("Calculating route..."):
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)

                start_coords = geocode_address(start_address, geocoder)
                end_coords = geocode_address(end_address, geocoder)

                if start_coords and end_coords:
                    start_lat, start_lon = start_coords
                    end_lat, end_lon = end_coords

                    st.success("Route calculated successfully!")

                    distance = calculate_distance(start_coords, end_coords)
                    toll = calculate_toll(distance)

                    m = folium.Map(location=[(start_lat + end_lat) / 2, (start_lon + end_lon) / 2], zoom_start=4)
                    folium.Marker([start_lat, start_lon], popup=f"Start: {start_address}").add_to(m)
                    folium.Marker([end_lat, end_lon], popup=f"End: {end_address}").add_to(m)
                    folium.PolyLine(locations=[[start_lat, start_lon], [end_lat, end_lon]], color="red", weight=2.5,
                                    opacity=1).add_to(m)

                    folium_static(m, width=700, height=400)

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Distance", f"{distance:.2f} km")
                    col2.metric("Toll", f"${toll:.2f}")
                    col3.metric("Estimated Time", f"{distance / 100:.2f} hours")

                    if username:
                        add_transaction(username, start_lat, start_lon, end_lat, end_lon, distance, toll)

                else:
                    st.error("Could not geocode one or both addresses. Please check your input and try again.")

    with tabs[1]:
        if username:
            st.subheader(f"Transaction History for {username}")
            history = get_transaction_history(username)
            if not history.empty:
                fig = px.line(history, x='timestamp', y='toll', title='Toll History')
                st.plotly_chart(fig)
                st.dataframe(history)
            else:
                st.info("No transaction history available.")
        else:
            st.warning("Please enter a username to view transaction history.")


# Main app logic
def main():
    if 'page' not in st.session_state:
        st.session_state.page = "start"

    if st.session_state.page == "start":
        get_started()
    elif st.session_state.page == "email":
        enter_email()
    elif st.session_state.page == "simulation":
        simulation()


if __name__ == "__main__":
    main()
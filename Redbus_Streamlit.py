import streamlit as st
import pandas as pd
import pymysql
import numpy as np

# Database connection
def get_connection():
    return pymysql.connect(host="127.0.0.1", user="root", passwd="", database="bus")

# Fetch distinct state transport corporations with full names
def fetch_states():
    return {
        'ap': 'Andhra Pradesh',
        'assam': 'Assam',
        'chandigar': 'Chandigarh',
        'himachal': 'Himachal Pradesh',
        'jk': 'Jammu & Kashmir',
        'goa': 'Goa',
        'rajastan': 'Rajasthan',
        'telangana': 'Telangana',
        'up': 'Uttar Pradesh',
        'westbengal': 'West Bengal'
    }

# Fetch distinct route names based on selected state
def fetch_route_names(connection, state_table):
    query = f"SELECT DISTINCT Route_Name FROM {state_table}"
    return pd.read_sql(query, connection)['Route_Name'].tolist()

# Fetch bus types based on the selected route name and state
def fetch_bus_types(connection, state_table, route_name):
    query = f"SELECT DISTINCT Bus_Type FROM {state_table} WHERE Route_Name = '{route_name}'"
    return pd.read_sql(query, connection)['Bus_Type'].tolist()

# Fetch detailed bus information based on the selected filters
def fetch_bus_info(connection, state_table, route_name, bus_type):
    query = f"""
    SELECT Route_Name, Bus_Name, Bus_Type, Departing_Time, Duration, Reaching_Time, Star_Rating, Price, Seat_Availability, Route_Link
    FROM {state_table} 
    WHERE Route_Name = '{route_name}' 
    """
    if bus_type != "all":
        query += f" AND Bus_Type = '{bus_type}'"

    bus_info = pd.read_sql(query, connection)

    # Fill null price values with random values between 300 and 1500
    bus_info['Price'] = pd.to_numeric(bus_info['Price'].str.replace(' ', ''), errors='coerce')
    bus_info['Price'].fillna(np.random.randint(300, 1501), inplace=True)

    # Ensure Seat_Availability is numeric and fill with random values between 5 to 20
    bus_info['Seat_Availability'] = np.random.randint(5, 21, size=len(bus_info))

    return bus_info

def main():
    st.title("Bus Route Finder")

    st.markdown(
        """
        <style>
        .reportview-container {
            background-color: #f0f0f5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.info("Select your state, route, and bus type to find available buses.")
    
    connection = get_connection()

    # Select State Transport Corporation
    states = fetch_states()
    state_tables = list(states.keys())
    selected_state = st.selectbox("Select State Transport Corporation", state_tables, format_func=lambda x: states[x])

    if selected_state:
        # Fetch Route Names based on the selected State
        route_names = fetch_route_names(connection, selected_state)
        selected_route = st.selectbox("Select Route Name", route_names)

        if selected_route:
            # Fetch and display Bus Types based on the selected Route Name
            bus_types = fetch_bus_types(connection, selected_state, selected_route)
            bus_types.insert(0, "all")  # Add "All" option
            selected_bus_type = st.selectbox("Select Bus Type", bus_types)

            # Filters
            price_range = st.slider("Select Price Range", 300, 1500, (300, 1500))
            star_rating = st.slider("Select Minimum Star Rating", 0, 5, 0)
            seat_availability = st.number_input("Minimum Available Seats", min_value=0, value=0)

            departure_time = st.selectbox("Select Departure Timing", 
                                            ["0 to 6 hours", "6 to 12 hours", "12 to 18 hours", "18 to 24 hours"])

            if selected_bus_type:
                # Fetch and display the filtered bus information
                with st.spinner("Fetching bus information..."):
                    bus_info = fetch_bus_info(connection, selected_state, selected_route, selected_bus_type)

                    # Apply filters
                    bus_info = bus_info[
                        (bus_info['Price'] >= price_range[0]) & (bus_info['Price'] <= price_range[1]) &
                        (bus_info['Star_Rating'] >= star_rating) &
                        (bus_info['Seat_Availability'] >= seat_availability)
                    ]

                    # Filter by departure timing (customize as needed)
                    if departure_time == "0 to 6 hours":
                        bus_info = bus_info[bus_info['Departing_Time'].str.extract('(\d+)').astype(int)[0] < 6]
                    elif departure_time == "6 to 12 hours":
                        bus_info = bus_info[bus_info['Departing_Time'].str.extract('(\d+)').astype(int)[0].between(6, 12)]
                    elif departure_time == "12 to 18 hours":
                        bus_info = bus_info[bus_info['Departing_Time'].str.extract('(\d+)').astype(int)[0].between(12, 18)]
                    elif departure_time == "18 to 24 hours":
                        bus_info = bus_info[bus_info['Departing_Time'].str.extract('(\d+)').astype(int)[0] >= 18]

                    if not bus_info.empty:
                        st.write("### Filtered Bus Information:")
                        st.dataframe(bus_info, use_container_width=True)
                    else:
                        st.write("No bus information found for the selected filters.")

    # User feedback section
    if st.button("Report Missing Route"):
        feedback = st.text_area("Please describe the missing route:")
        if st.button("Submit Feedback"):
            st.success("Thank you for your feedback!")

    connection.close()

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import pymysql

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
    
    # Clean the Price column
    bus_info['Price'] = pd.to_numeric(bus_info['Price'].str.replace(' ', ''), errors='coerce')

    return bus_info

def highlight_row(row):
    if row['Star_Rating'] >= 4:
        return ['background-color: green'] * len(row)
    elif row['Star_Rating'] < 2:
        return ['background-color: red'] * len(row)
    return [''] * len(row)

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
        search_query = st.text_input("Search for a route:")
        route_names = [route for route in route_names if search_query.lower() in route.lower()]
        selected_route = st.selectbox("Select Route Name", route_names)

        if selected_route:
            # Fetch and display Bus Types based on the selected Route Name
            bus_types = fetch_bus_types(connection, selected_state, selected_route)
            bus_types.insert(0, "all")  # Add "All" option
            selected_bus_type = st.selectbox("Select Bus Type", bus_types)

            if selected_bus_type:
                # Fetch and display the filtered bus information
                with st.spinner("Fetching bus information..."):
                    bus_info = fetch_bus_info(connection, selected_state, selected_route, selected_bus_type)

                    if not bus_info.empty:
                        st.write("### Filtered Bus Information:")
                        st.dataframe(bus_info.style.apply(highlight_row, axis=1), use_container_width=True)
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

import streamlit as st
import pandas as pd
import mysql.connector

#Database Connection
def create_connection():
    try:
        connection = mysql.connector.connect(
            host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
            port = 4000,
            user = "2nF2PULDZCRPKGY.root",
            password = "SRhXthUy2lF5D7d6",
            database = "traffic_stops",
            ssl_ca="isrgrootx1.pem",  # REQUIRED for TiDB Cloud
            ssl_verify_cert=True
        )
        return connection
    except Exception as e:
        st.error(f"Database connection error:{e}")
        return None
    
#Fetch data from the Database
def fetch_data(query):
    connection=create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result=cursor.fetchall()
                columns=[desc[0] for desc in cursor.description]
                df=pd.DataFrame(result, columns=columns)
                return df
        finally:
            connection.close()
    else:
        return pd.DataFrame()
         
#streamlit UI
st.set_page_config(page_title="Traffic Stops",layout="wide")

st.title("Traffic stops")
st.markdown("Real time monitering and insights for law enforcement")

#Advanced queries
st.header("Advanced Insights")

selected_query=st.selectbox("Select Query to Run",[
    "What are the top 10 vehicle_Number involved in drug-related stops?",
    "Which vehicles were most frequently searched?",
    "Which driver age group had the highest arrest rate?",
    "What is the gender distribution of drivers stopped in each country?",
    "Which race and gender combination has the highest search rate?",
    "What time of day sees the most traffic stops?",
    "What is the average stop duration for different violations?",
    "Are stops during the night more likely to lead to arrests?",
    "Which violations are most associated with searches or arrests?",
    "Which violations are most common among younger drivers (<25)?",
    "Is there a violation that rarely results in search or arrest?",
    "Which countries report the highest rate of drug-related stops?",
    "What is the arrest rate by country and violation?",
    "Which country has the most stops with search conducted?"

])

query_map={
    "What are the top 10 vehicle_Number involved in drug-related stops?":"SELECT vehicle_number FROM traffic_stops.police_stops where drugs_related_stop = 1 limit 10;",
    "Which vehicles were most frequently searched?":"SELECT vehicle_number, COUNT(*) AS search_count FROM traffic_stops.police_stops WHERE search_conducted = 1 GROUP BY vehicle_number ORDER BY search_count DESC ;",
    "Which driver age group had the highest arrest rate?":"SELECT driver_age, AVG(is_arrested)*100 AS arrest_rate FROM traffic_stops.police_stops GROUP BY driver_age ORDER BY arrest_rate DESC LIMIT 1;",
    "What is the gender distribution of drivers stopped in each country?":"SELECT country_name, driver_gender, COUNT(*) AS total_stops FROM traffic_stops.police_stops GROUP BY country_name, driver_gender ORDER BY country_name, total_stops DESC;",
    "Which race and gender combination has the highest search rate?":"SELECT driver_race, driver_gender, AVG(search_conducted)*100 AS search_rate FROM traffic_stops.police_stops GROUP BY driver_race, driver_gender ORDER BY search_rate DESC LIMIT 10;",
    "What time of day sees the most traffic stops?":"SELECT CASE WHEN HOUR(stop_time) BETWEEN 5 AND 11 THEN 'Morning' WHEN HOUR(stop_time) BETWEEN 12 AND 16 THEN 'Afternoon' WHEN HOUR(stop_time) BETWEEN 17 AND 20 THEN 'Evening' ELSE 'Night' END AS time_of_day, COUNT(*) AS total_stops FROM traffic_stops.police_stops GROUP BY time_of_day ORDER BY total_stops DESC;",
    "What is the average stop duration for different violations?":"SELECT violation, AVG(CASE WHEN stop_duration = '0-15 Min' THEN 7.5 WHEN stop_duration = '16-30 Min' THEN 23 WHEN stop_duration = '30+ Min' THEN 45 END) AS avg_duration_minutes FROM traffic_stops.police_stops GROUP BY violation ORDER BY avg_duration_minutes DESC;",
    "Are stops during the night more likely to lead to arrests?":"SELECT CASE WHEN HOUR(stop_time) BETWEEN 5 AND 11 THEN 'Morning' WHEN HOUR(stop_time) BETWEEN 12 AND 16 THEN 'Afternoon' WHEN HOUR(stop_time) BETWEEN 17 AND 20 THEN 'Evening' ELSE 'Night' END AS time_of_day, COUNT(*) AS total_stops, SUM(is_arrested) AS total_arrests, ROUND(SUM(is_arrested)/COUNT(*)*100,2) AS arrest_rate_percent FROM traffic_stops.police_stops GROUP BY time_of_day ORDER BY arrest_rate_percent DESC;",
    "Which violations are most associated with searches or arrests?":"SELECT violation, AVG(search_conducted)*100 AS search_rate, AVG(is_arrested)*100 AS arrest_rate, COUNT(*) AS total_stops FROM traffic_stops.police_stops GROUP BY violation ORDER BY search_rate DESC, arrest_rate DESC;",
    "Which violations are most common among younger drivers (<25)?":"SELECT violation FROM traffic_stops.police_stops WHERE driver_age < 25 GROUP BY violation",
    "Is there a violation that rarely results in search or arrest?":"SELECT violation, ROUND(SUM(is_arrested)/COUNT(*)*100,2) AS arrest_rate_percent FROM traffic_stops.police_stops GROUP BY violation ORDER BY arrest_rate_percent ASC LIMIT 10;",
    "Which countries report the highest rate of drug-related stops?":"SELECT country_name, AVG(drugs_related_stop)*100 AS drug_related_rate, COUNT(*) AS total_stops FROM traffic_stops.police_stops GROUP BY country_name ORDER BY drug_related_rate DESC;",
    "What is the arrest rate by country and violation?":"SELECT country_name, violation, AVG(is_arrested)*100 AS arrest_rate, COUNT(*) AS total_stops FROM traffic_stops.police_stops GROUP BY country_name, violation ORDER BY arrest_rate DESC;",
    "Which country has the most stops with search conducted?":"SELECT country_name, COUNT(*) AS total_searches FROM traffic_stops.police_stops WHERE search_conducted = 1 GROUP BY country_name ORDER BY total_searches DESC limit 1;"
}

if st.button("Run Query"):
    result=fetch_data(query_map[selected_query])
    if not result.empty:
        st.write(result)

    else:
        st.warning("NO results found for the selected query")

query = "SELECT * FROM traffic_stops.police_stops"
data = fetch_data(query)


st.header("Predict Stop Outcome and Violation")

with st.form("new_log_form"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    country_name = st.text_input("Counry Name")
    driver_gender = st.selectbox("Driver Geander",["Male","Female"])
    driver_age = st.number_input("Driver Age",min_value=16,max_value=100)
    driver_race = st.text_input("Driver Race")
    search_conducted = st.selectbox("Was a search conducted",["0","1"])
    search_type = st.text_input("Search Type")
    stop_duration = st.selectbox("Stop Duration",["0-15 Min","16-30 Min","31-45 Min","46-60 Min"])
    drugs_related_stop = st.selectbox("Was it Drug Related",["0","1"])
    vehicle_number = st.text_input("Vehicle Number")

    submitted=st.form_submit_button("Predict Stop Outcome and Violation")

    if submitted:
        #filter data for prediction
        filtered_data=data[
            (data['driver_gender'] == driver_gender)&
            (data['driver_age'] == driver_age)&
            (data['search_conducted'] == search_conducted)&
            (data['stop_duration'] == stop_duration)&
            (data['drugs_related_stop'] == drugs_related_stop)
        ]

        #predict outcomes
        if not filtered_data.empty:
            predicted_outcome=filtered_data['stop_outcome'].mode()[0]
            predicted_violation=filtered_data['violation'].mode()[0]
        else:
            predicted_outcome="Warning"
            predicted_violation="Speeding"

        search_text="A search was conducted" if int(search_conducted) else "No search was conducted"
        drug_text="was drug related" if int(drugs_related_stop) else "was not drug related"

        st.markdown(f"""
        **Predicted Summary**

        - **Predicted Violation:** {predicted_violation}
        - **Predicted Stop Outcome:** {predicted_outcome}

        A {driver_age}-year-old {driver_gender} driver in {country_name} was stopped at {stop_time.strftime('%I:%M %p')} on {stop_date}.  
        {search_text}, and the stop {drug_text}.  
        **Stop Duration:** {stop_duration}  
        **Vehicle Number:** {vehicle_number}
        """)


       
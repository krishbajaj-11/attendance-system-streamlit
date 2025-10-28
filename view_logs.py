import streamlit as st
import boto3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AWS Attendance Dashboard", layout="centered")

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('AttendanceTable')

def get_attendance_data():
    response = table.scan()
    data = response.get('Items', [])
    return data

st.title("📋 Student Attendance System")
st.write("Data fetched live from DynamoDB")

if st.button("🔄 Refresh Attendance"):
    records = get_attendance_data()

    if records:
        df = pd.DataFrame(records)
        df = df.sort_values(by='Timestamp', ascending=False)
        st.dataframe(df)
    else:
        st.info("No attendance records found yet.")

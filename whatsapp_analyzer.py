import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re

def parse_chat(file_content):
    """Parse WhatsApp chat file into a pandas DataFrame."""
    # Regular expression pattern for WhatsApp messages
    pattern = r'(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2}) - ([^:]+): (.+)'
    
    messages = []
    for line in file_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            date, time, sender, message = match.groups()
            messages.append({
                'date': datetime.strptime(date, '%d/%m/%Y'),
                'time': time,
                'sender': sender.strip(),
                'message': message
            })
    
    return pd.DataFrame(messages)

def analyze_chat(df, start_date=None, end_date=None):
    """Generate insights from the chat data."""
    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]
    
    # Message count by participant
    participant_stats = df['sender'].value_counts()
    
    # Most active days
    daily_activity = df.groupby('date').size().sort_values(ascending=False)
    
    # Most active hours
    df['hour'] = df['time'].str[:2].astype(int)
    hourly_activity = df.groupby('hour').size()
    
    return participant_stats, daily_activity, hourly_activity

def main():
    st.title("WhatsApp Chat Analyzer")
    
    # File upload
    uploaded_file = st.file_uploader("Upload your WhatsApp chat file (.txt)", type="txt")
    
    if uploaded_file:
        # Read and parse chat
        content = uploaded_file.getvalue().decode("utf-8")
        df = parse_chat(content)
        
        # Date filter
        st.sidebar.header("Filters")
        min_date = df['date'].min()
        max_date = df['date'].max()
        
        start_date = st.sidebar.date_input("Start Date", min_date)
        end_date = st.sidebar.date_input("End Date", max_date)
        
        # Analyze chat
        participant_stats, daily_activity, hourly_activity = analyze_chat(
            df, 
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time())
        )
        
        # Display insights
        st.header("Chat Insights")
        
        # Participant Rankings
        st.subheader("Most Active Participants")
        fig_participants = px.bar(
            participant_stats,
            title="Messages per Participant",
            labels={'value': 'Number of Messages', 'index': 'Participant'}
        )
        st.plotly_chart(fig_participants)
        
        # Daily Activity
        st.subheader("Daily Activity")
        fig_daily = px.line(
            daily_activity,
            title="Messages per Day",
            labels={'value': 'Number of Messages', 'index': 'Date'}
        )
        st.plotly_chart(fig_daily)
        
        # Hourly Activity
        st.subheader("Hourly Activity")
        fig_hourly = px.bar(
            hourly_activity,
            title="Messages by Hour of Day",
            labels={'value': 'Number of Messages', 'index': 'Hour'}
        )
        st.plotly_chart(fig_hourly)
        
        # Additional Statistics
        st.subheader("Summary Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Messages", len(df))
        with col2:
            st.metric("Total Participants", len(participant_stats))
        with col3:
            st.metric("Date Range", f"{min_date.date()} to {max_date.date()}")

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re

def parse_chat(file_content):
    """Parse WhatsApp chat file into a pandas DataFrame."""
    # Updated pattern to match both date formats (M/D/YY and DD/MM/YYYY)
    pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}), (\d{2}:\d{2}) - ([^:]+): (.+)'
    
    messages = []
    for line in file_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            try:
                date, time, sender, message = match.groups()
                # Try to parse date with different formats
                try:
                    # Try M/D/YY format first
                    parsed_date = datetime.strptime(date, '%m/%d/%y')
                except ValueError:
                    try:
                        # Try DD/MM/YYYY format as fallback
                        parsed_date = datetime.strptime(date, '%d/%m/%Y')
                    except ValueError:
                        # Skip invalid dates
                        continue
                
                messages.append({
                    'date': parsed_date,
                    'time': time,
                    'sender': sender.strip(),
                    'message': message
                })
            except ValueError as e:
                st.warning(f"Skipped line due to parsing error: {line[:100]}...")
                continue
    
    if not messages:
        return None
        
    df = pd.DataFrame(messages)
    return df

def analyze_chat(df, start_date=None, end_date=None):
    """Generate insights from the chat data."""
    if df is None or df.empty:
        return None, None, None
        
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
    
    # Add instructions
    st.markdown("""
    ### Instructions:
    1. Export your WhatsApp chat (without media) from any WhatsApp group
    2. Upload the exported .txt file below
    3. Use the date filters in the sidebar to analyze specific time periods
    """)
    
    # File upload
    uploaded_file = st.file_uploader("Upload your WhatsApp chat file (.txt)", type="txt")
    
    if uploaded_file is not None:
        try:
            # Read and parse chat
            content = uploaded_file.getvalue().decode("utf-8")
            df = parse_chat(content)
            
            if df is None or df.empty:
                st.error("No valid messages found in the file. Please check the file format.")
                return
                
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
            
            if participant_stats is None:
                st.error("No data available for the selected date range.")
                return
            
            # Display insights
            st.header("Chat Insights")
            
            # Total Messages and Participants
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Messages", len(df))
            with col2:
                st.metric("Total Participants", len(participant_stats))
            with col3:
                st.metric("Date Range", f"{min_date.date()} to {max_date.date()}")
            
            # Participant Rankings
            st.subheader("Most Active Participants")
            fig_participants = px.bar(
                participant_stats,
                title="Messages per Participant",
                labels={'value': 'Number of Messages', 'index': 'Participant'}
            )
            st.plotly_chart(fig_participants, use_container_width=True)
            
            # Daily Activity
            st.subheader("Daily Activity")
            fig_daily = px.line(
                daily_activity,
                title="Messages per Day",
                labels={'value': 'Number of Messages', 'index': 'Date'}
            )
            st.plotly_chart(fig_daily, use_container_width=True)
            
            # Hourly Activity
            st.subheader("Hourly Activity")
            fig_hourly = px.bar(
                hourly_activity,
                title="Messages by Hour of Day",
                labels={'value': 'Number of Messages', 'index': 'Hour'},
                text='value'  # Show values on bars
            )
            fig_hourly.update_traces(textposition='outside')
            st.plotly_chart(fig_hourly, use_container_width=True)
            
            # Show raw data option
            if st.checkbox("Show raw data"):
                st.dataframe(df)
                
        except Exception as e:
            st.error(f"An error occurred while processing the file: {str(e)}")
            st.error("Please make sure you've uploaded a valid WhatsApp chat export file.")

if __name__ == "__main__":
    main()
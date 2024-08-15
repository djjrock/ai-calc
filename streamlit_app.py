import streamlit as st
import pandas as pd
import math
import plotly.express as px

# --- Function to Calculate Costs ---
def calculate_costs(inputs):
    # --- Extract Inputs ---
    total_calls = inputs['total_calls']
    campaign_length_days = inputs['campaign_length_days']
    answer_rate = inputs['answer_rate']
    voicemail_rate = inputs['voicemail_rate']
    avg_call_length = inputs['avg_call_length']
    voicemail_length = inputs['voicemail_length']
    hours_per_day = inputs['hours_per_day']
    days_per_week = inputs['days_per_week']
    eleven_labs_tokens_per_minute = inputs['eleven_labs_tokens_per_minute']
    deepgram_rate_per_hour = inputs['deepgram_rate_per_hour']
    openai_input_tokens_per_min = inputs['openai_input_tokens_per_min']
    openai_output_tokens_per_min = inputs['openai_output_tokens_per_min']
    openai_bundle_cost = inputs['openai_bundle_cost']
    aws_server_cost = inputs['aws_server_cost']
    aws_server_capacity = inputs['aws_server_capacity']
    turn_off_servers_at_night = inputs['turn_off_servers_at_night']
    openai_peak_factor = inputs['openai_peak_factor']

    # --- Call Statistics ---
    calls_per_day = total_calls / campaign_length_days
    answered_calls = round(total_calls * (answer_rate / 100))
    voicemails = round(total_calls * (voicemail_rate / 100))
    unanswered_calls = total_calls - answered_calls - voicemails

    answered_minutes = answered_calls * avg_call_length
    voicemail_minutes = voicemails * voicemail_length
    total_minutes = answered_minutes + voicemail_minutes

    # Only answered calls use AI services
    ai_processed_minutes = answered_minutes

    answered_calls_per_day = answered_calls / campaign_length_days
    voicemails_per_day = voicemails / campaign_length_days

    # --- Average Concurrent Calls (for answered calls only) ---
    total_minutes_per_day = hours_per_day * 60
    calls_per_minute = answered_calls_per_day / total_minutes_per_day
    avg_concurrent_calls = calls_per_minute * avg_call_length

    # --- 11 Labs Cost (Only for Answered Calls) ---
    total_chars = ai_processed_minutes * eleven_labs_tokens_per_minute
    eleven_labs_tiers = [
        {"chars": 11000000, "cost": 550},
        {"chars": 20000000, "cost": 900},
        {"chars": 50000000, "cost": 2000},
        {"chars": 100000000, "cost": 3500},
        {"chars": 200000000, "cost": 6000},
        {"chars": 350000000, "cost": 8750},
        {"chars": 500000000, "cost": 10000},
    ]
    selected_tier = next((tier for tier in eleven_labs_tiers if tier['chars'] >= total_chars), eleven_labs_tiers[-1])
    eleven_labs_cost = selected_tier['cost']

    # --- Deepgram Cost (Only for Answered Calls) ---
    deepgram_cost = (ai_processed_minutes / 60) * deepgram_rate_per_hour

    # --- OpenAI Cost (Only for Answered Calls) ---
    openai_bundle_input_capacity = 20000  # tokens per minute
    openai_bundle_output_capacity = 2000  # tokens per minute

    total_input_tokens_per_day = answered_calls_per_day * openai_input_tokens_per_min * avg_call_length
    total_output_tokens_per_day = answered_calls_per_day * openai_output_tokens_per_min * avg_call_length

    minutes_per_day = hours_per_day * 60
    input_tokens_per_min = total_input_tokens_per_day / minutes_per_day
    output_tokens_per_min = total_output_tokens_per_day / minutes_per_day

    # Apply peak factor to OpenAI token usage
    input_tokens_per_min *= openai_peak_factor
    output_tokens_per_min *= openai_peak_factor

    input_bundles_needed = math.ceil(input_tokens_per_min / openai_bundle_input_capacity)
    output_bundles_needed = math.ceil(output_tokens_per_min / openai_bundle_output_capacity)

    openai_bundles_needed = max(input_bundles_needed, output_bundles_needed)

    openai_daily_cost = openai_bundle_cost / 30  # Assuming 30 days in a month
    openai_days_used = math.ceil(campaign_length_days * (days_per_week / 7))
    openai_cost = openai_bundles_needed * openai_daily_cost * openai_days_used

    # --- AWS Cost (Only for Answered Calls) ---
    servers_needed = math.ceil(avg_concurrent_calls / aws_server_capacity)
    aws_daily_cost = aws_server_cost / 30  # Daily cost per server

    if turn_off_servers_at_night:
        aws_hours_per_day = hours_per_day
    else:
        aws_hours_per_day = 24

    aws_cost = servers_needed * aws_daily_cost * campaign_length_days * (aws_hours_per_day / 24)

    # --- Twilio Cost ---
    twilio_cost_per_minute = 0.0140  # Outbound call cost
    twilio_cost = total_minutes * twilio_cost_per_minute

    # --- Total Cost ---
    total_cost = eleven_labs_cost + deepgram_cost + openai_cost + aws_cost + twilio_cost

    # --- Return Results ---
    return {
        "call_stats": {
            "total_calls": total_calls,
            "campaign_length_days": campaign_length_days,
            "calls_per_day": calls_per_day,
            "answered_calls": answered_calls,
            "voicemails": voicemails,
            "unanswered_calls": unanswered_calls,
            "total_minutes": total_minutes,
            "ai_processed_minutes": ai_processed_minutes,
            "answered_calls_per_day": answered_calls_per_day,
            "voicemails_per_day": voicemails_per_day,
            "avg_concurrent_calls": avg_concurrent_calls
        },
        "eleven_labs": {
            "total_chars": total_chars,
            "selected_tier": selected_tier['chars'],
            "cost": eleven_labs_cost
        },
        "deepgram": {
            "cost": deepgram_cost,
            "processed_minutes": ai_processed_minutes
        },
        "openai": {
            "input_tokens_per_min": input_tokens_per_min,
            "output_tokens_per_min": output_tokens_per_min,
            "input_bundles_needed": input_bundles_needed,
            "output_bundles_needed": output_bundles_needed,
            "bundles_needed": openai_bundles_needed,
            "daily_cost": openai_daily_cost,
            "days_used": openai_days_used,
            "cost": openai_cost
        },
        "aws": {
            "avg_concurrent_calls": avg_concurrent_calls,
            "servers_needed": servers_needed,
            "daily_cost_per_server": aws_daily_cost,
            "hours_per_day": aws_hours_per_day,
            "cost": aws_cost
        },
        "twilio": {
            "cost_per_minute": twilio_cost_per_minute,
            "cost": twilio_cost
        },
        "total_cost": total_cost,
        "price_per_minute": total_cost / total_minutes if total_minutes > 0 else 0,
        "price_per_hour": (total_cost / total_minutes) * 60 if total_minutes > 0 else 0
    }

# --- Streamlit App ---
st.title("AI Services Pricing Calculator")

# --- Input Fields ---
st.header("Campaign Parameters")
col1, col2 = st.columns(2)

with col1:
    total_calls = st.number_input("Total Calls", value=1000000, step=1000)
    campaign_length_days = st.number_input("Campaign Length (Days)", value=30, step=1)
    answer_rate = st.number_input("Answer Rate (%)", value=1.5, step=0.1)
    voicemail_rate = st.number_input("Voicemail Rate (%)", value=20.0, step=0.1)

with col2:
    avg_call_length = st.number_input("Average Call Length (Minutes)", value=5.0, step=0.1)
    voicemail_length = st.number_input("Voicemail Length (Minutes)", value=0.5, step=0.1)
    hours_per_day = st.number_input("Hours of Operation per Day", value=8, step=1)
    days_per_week = st.number_input("Days of Operation per Week", value=5, min_value=1, max_value=7, step=1)

st.header("Service Parameters")
col3, col4 = st.columns(2)

with col3:
    eleven_labs_tokens_per_minute = st.number_input("11 Labs Tokens/Minute", value=300, step=10)
    deepgram_rate_per_hour = st.number_input("Deepgram Rate per Hour ($)", value=0.25, step=0.01)
    openai_input_tokens_per_min = st.number_input("OpenAI Input Tokens/Minute", value=600, step=10)

with col4:
    openai_output_tokens_per_min = st.number_input("OpenAI Output Tokens/Minute", value=300, step=10)
    openai_bundle_cost = st.number_input("OpenAI Bundle Cost ($)", value=5000, step=100)
    aws_server_cost = st.number_input("AWS Server Cost per Month ($)", value=750, step=10)
    aws_server_capacity = st.number_input("AWS Server Capacity (Concurrent Calls)", value=20, step=1)
    turn_off_servers_at_night = st.checkbox("Turn off AWS Servers at Night", value=False)
    openai_peak_factor = st.number_input("OpenAI Peak Factor (Multiplier)", value=1.2, step=0.1)

# --- Calculate and Display Results ---
inputs = {
    'total_calls': total_calls,
    'campaign_length_days': campaign_length_days,
    'answer_rate': answer_rate,
    'voicemail_rate': voicemail_rate,
    'avg_call_length': avg_call_length,
    'voicemail_length': voicemail_length,
    'hours_per_day': hours_per_day,
    'days_per_week': days_per_week,
    'eleven_labs_tokens_per_minute': eleven_labs_tokens_per_minute,
    'deepgram_rate_per_hour': deepgram_rate_per_hour,
    'openai_input_tokens_per_min': openai_input_tokens_per_min,
    'openai_output_tokens_per_min': openai_output_tokens_per_min,
    'openai_bundle_cost': openai_bundle_cost,
    'aws_server_cost': aws_server_cost,
    'aws_server_capacity': aws_server_capacity,
    'turn_off_servers_at_night': turn_off_servers_at_night,
    'openai_peak_factor': openai_peak_factor
}

results = calculate_costs(inputs)

st.header("Results")

st.subheader("Call Statistics")
call_stats_df = pd.DataFrame([results['call_stats']]).T
call_stats_df.columns = ['Value']
st.table(call_stats_df)

st.subheader("11 Labs Cost")
st.write(pd.DataFrame([results['eleven_labs']]).T)

st.subheader("Deepgram Cost")
st.write(pd.DataFrame([results['deepgram']]).T)

st.subheader("OpenAI Cost")
openai_df = pd.DataFrame({
    'Input Tokens/Minute': [results['openai']['input_tokens_per_min']],
    'Output Tokens/Minute': [results['openai']['output_tokens_per_min']],
    'Input Bundles Needed': [results['openai']['input_bundles_needed']],
    'Output Bundles Needed': [results['openai']['output_bundles_needed']],
    'Total Bundles Needed': [results['openai']['bundles_needed']],
    'Daily Cost': [results['openai']['daily_cost']],
    'Days Used': [results['openai']['days_used']],
    'Total Cost': [results['openai']['cost']]
}).T
st.write(openai_df)

st.subheader("AWS Cost")
st.write(pd.DataFrame([results['aws']]).T)

st.subheader("Twilio Cost")
st.write(pd.DataFrame([results['twilio']]).T)

st.subheader("Total Cost & Pricing")
total_cost_df = pd.DataFrame({
    'Total Cost': [results['total_cost']],
    'Price per Minute': [results['price_per_minute']],
    'Price per Hour': [results['price_per_hour']]
}).T
st.write(total_cost_df)

# --- Detailed Calculations (Optional, can be hidden) ---
with st.expander("Detailed Calculations"):
    st.markdown("""
    ### Call Statistics
    - Calls per Day = Total Calls / Campaign Length (days)
    - Answered Calls = Total Calls * (Answer Rate / 100)
    - Voicemails = Total Calls * (Voicemail Rate / 100)
    - Unanswered Calls = Total Calls - Answered Calls - Voicemails
    - Total Minutes = (Answered Calls * Avg Call Length) + (Voicemails * Voicemail Length)
    - AI Processed Minutes = Answered Calls * Avg Call Length
    - Answered Calls per Day = Answered Calls / Campaign Length (days)
    - Voicemails per Day = Voicemails / Campaign Length (days)
    - Average Concurrent Calls = (Calls per Day / (Hours per Day * 60)) * Avg Call Length

    ### 11 Labs (Only for Answered Calls)
    - Total Characters = AI Processed Minutes * Tokens per Minute
    - Cost based on selected tier for Total Characters

    ### Deepgram (Only for Answered Calls)
    - Cost = (AI Processed Minutes / 60) * Live Streaming Rate per Hour

    ### OpenAI (Only for Answered Calls)
    - Total Input Tokens per Day = Answered Calls per Day * Input Tokens per Minute per Call * Avg Call Length
    - Total Output Tokens per Day = Answered Calls per Day * Output Tokens per Minute per Call * Avg Call Length
    - Input Tokens per Minute = Total Input Tokens per Day / (Hours per Day * 60)
    - Output Tokens per Minute = Total Output Tokens per Day / (Hours per Day * 60)
    - Input Tokens per Minute (Peak) = Input Tokens per Minute * OpenAI Peak Factor
    - Output Tokens per Minute (Peak) = Output Tokens per Minute * OpenAI Peak Factor
    - Input Bundles Needed = Ceiling(Input Tokens per Minute (Peak) / 20,000)
    - Output Bundles Needed = Ceiling(Output Tokens per Minute (Peak) / 2,000)
    - Total Bundles Needed = Max(Input Bundles Needed, Output Bundles Needed)
    - Daily Cost = Monthly Bundle Cost / 30
    - Days Used = Ceiling(Campaign Length * (Days per Week / 7))
    - Total Cost = Total Bundles Needed * Daily Cost * Days Used

    ### AWS (Only for Answered Calls)
    - Servers Needed = Ceiling(Average Concurrent Calls / Server Capacity)
    - Daily Cost per Server = Server Cost per Month / 30
    - AWS Hours per Day = Hours of Operation (if servers are turned off at night) or 24 (if servers run continuously)
    - Cost = Servers Needed * Daily Cost per Server * Campaign Length * (AWS Hours per Day / 24)

    ### Twilio
    - Cost = Total Minutes * Cost per Minute (using $0.0140/minute for outbound calls)

    ### Total Cost and Pricing
    - Total Cost = 11 Labs Cost + Deepgram Cost + OpenAI Cost + AWS Cost + Twilio Cost
    - Price per Minute = Total Cost / Total Minutes
    - Price per Hour = Price per Minute * 60
    """)


st.header("Visualizations")

# Cost Breakdown Chart
cost_breakdown = {
    '11 Labs': results['eleven_labs']['cost'],
    'Deepgram': results['deepgram']['cost'],
    'OpenAI': results['openai']['cost'],
    'AWS': results['aws']['cost'],
    'Twilio': results['twilio']['cost']
}
cost_df = pd.DataFrame(list(cost_breakdown.items()), columns=['Service', 'Cost'])
fig_cost = px.bar(cost_df, x='Service', y='Cost', title='Cost Breakdown by Service')
st.plotly_chart(fig_cost)

# Call Statistics Chart
call_stats = {
    'Answered Calls': results['call_stats']['answered_calls'],
    'Voicemails': results['call_stats']['voicemails'],
    'Unanswered Calls': results['call_stats']['unanswered_calls']
}
call_stats_df = pd.DataFrame(list(call_stats.items()), columns=['Call Type', 'Count'])
fig_calls = px.bar(call_stats_df, x='Call Type', y='Count', title='Call Statistics')
st.plotly_chart(fig_calls)

# Daily Metrics Chart
daily_metrics = {
    'Calls per Day': results['call_stats']['calls_per_day'],
    'Answered Calls per Day': results['call_stats']['answered_calls_per_day'],
    'Voicemails per Day': results['call_stats']['voicemails_per_day']
}
daily_metrics_df = pd.DataFrame(list(daily_metrics.items()), columns=['Metric', 'Value'])
fig_daily = px.bar(daily_metrics_df, x='Metric', y='Value', title='Daily Call Metrics')
st.plotly_chart(fig_daily)

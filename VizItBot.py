import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import schedule
import time

# Function to plot Monthly Cumulative Blood Donation Counts by State
def plot_monthly_cumulative(update: Update, context: CallbackContext):
    # Load the CSV file into a Pandas DataFrame
    donations_state = pd.read_csv("https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/donations_state.csv")

    # Convert 'date' column to datetime type if not already
    donations_state['date'] = pd.to_datetime(donations_state['date'])

    # Extract Year and Month
    donations_state['year_month'] = donations_state['date'].dt.to_period('M')

    # Calculate daily donations for each state and year_month
    daily_counts = donations_state.groupby(['state', 'year_month']).agg({'daily': 'sum'}).reset_index()

    # Reorder states list so that Malaysia is the first element
    states = daily_counts['state'].unique().tolist()
    states.remove('Malaysia')
    states.insert(0, 'Malaysia')

    # Create subplots grid
    num_states = len(states)
    rows = (num_states // 2) + (num_states % 2)  # Calculate number of rows dynamically
    cols = 2  # Fixed number of columns
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=[f"Monthly Cumulative Count - {state}" for state in states])

    # Add each state as a subplot
    for i, state in enumerate(states, start=1):
        state_data = daily_counts[daily_counts['state'] == state].copy()  # Make a copy to avoid SettingWithCopyWarning
        state_data['cumulative'] = state_data.groupby('year_month')['daily'].cumsum()
        row = ((i - 1) // 2) + 1  # Calculate row index dynamically
        col = ((i - 1) % 2) + 1   # Calculate column index dynamically
        fig.add_trace(go.Scatter(x=state_data['year_month'].astype(str),
                            y=state_data['cumulative'],
                            mode='lines',
                            name=f'Monthly Cumulative Count - {state}'),
                row=row, col=col)

    # Update x-axis ticks to show all years
        fig.update_xaxes(title_text="Month", row=row, col=col,
                tickvals=state_data['year_month'].dt.to_timestamp(how='start').dt.to_period('Y').unique().strftime('%Y-%m').tolist(),
                ticktext=state_data['year_month'].dt.to_timestamp(how='start').dt.to_period('Y').unique().strftime('%Y').tolist(),
                tickfont=dict(family='Helvetica', size=12))

    # Update y-axis title for all subplots
    fig.update_yaxes(title_text="Monthly Cumulative Count", row=rows, col=cols)

    # Update layout
    fig.update_layout(height=1500, width=1200, showlegend=False, font=dict(family="Helvetica"))

    # Add grand title
    fig.update_layout(title="Monthly Cumulative Blood Donation Counts by State", title_font=dict(family="Helvetica", size=24), title_x=0.5)

    # Save plot to file
    fig.write_image("monthly_plot.png")

    # Send the plot to the Telegram chat
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('monthly_plot.png', 'rb'))

# Function to plot Yearly Blood Donation Counts by State
def plot_yearly(update: Update, context: CallbackContext):
    # Load data
    donations_state = pd.read_csv("https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/donations_state.csv")

    # Extract year from the date column
    donations_state['year'] = pd.to_datetime(donations_state['date']).dt.year

    # Calculate yearly donations for each state
    yearly_counts = donations_state.groupby(['state', 'year'])['daily'].sum().reset_index()

    # Determine the number of unique states
    num_states = yearly_counts['state'].nunique()

    # Sort states with 'Malaysia' first
    states = list(yearly_counts['state'].unique())
    states.remove('Malaysia')
    states = ['Malaysia'] + states

    # Create subplots with two columns
    fig = make_subplots(rows=num_states // 2 + (num_states % 2), cols=2, subplot_titles=[f"Yearly Count - {state}" for state in states],
                        vertical_spacing=0.05)

    # Add each state's data as a subplot
    for i, state in enumerate(states, start=1):
        state_data = yearly_counts[yearly_counts['state'] == state]
        row = (i - 1) // 2 + 1
        col = (i - 1) % 2 + 1
        fig.add_trace(go.Scatter(x=state_data['year'], y=state_data['daily'], mode='markers+lines', name=f'Yearly Count - {state}', marker=dict(size=8)), row=row, col=col)

        # Update x-axis title and tick font for all subplots
        fig.update_xaxes(title_text="Year", row=row, col=col, tickmode='array', tickvals=state_data['year'].unique(), ticktext=state_data['year'].unique(), tickfont=dict(family='Helvetica', size=15))

        # Update y-axis title and tick font for all subplots
        fig.update_yaxes(title_text="Yearly Count", row=row, col=col, tickfont=dict(family='Helvetica', size=15))

        # Update plot title font size
        fig.update_layout(title_font=dict(size=30))  # Adjust font size as needed


    # Update layout for the entire figure
    fig.update_layout(
        title='Yearly Blood Donation Counts by State',
        title_font=dict(family='Helvetica', size=35),  # Set title font to Helvetica and adjust size
        title_x=0.5,  # Center title
        height=300 * (num_states // 2 + (num_states % 2)),  # Adjust height based on number of states
        width=1500,
        showlegend=False,
        font=dict(family="Helvetica")  # Set all other fonts to Helvetica
    )

    # Save plot to file
    fig.write_image("yearly_plot.png")

    # Send the plot to the Telegram chat
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('yearly_plot.png', 'rb'))

# Function to plot Yearly Donations Regular for Malaysia State
def plot_yearly_donations_regular(update: Update, context: CallbackContext):
    # Load the dataset
    donors = pd.read_parquet("https://dub.sh/ds-data-granular")

    # Convert date columns to datetime format
    donors['visit_date'] = pd.to_datetime(donors['visit_date'])
    donors['birth_date'] = pd.to_datetime(donors['birth_date'], format='%Y')

    # Calculate age at the time of donation
    donors['age_at_donation'] = (donors['visit_date'] - donors['birth_date']).dt.days // 365

    # Sort the data by 'donor_id' and 'visit_date' to ensure chronological order
    donors.sort_values(by=['donor_id', 'visit_date'], inplace=True)

    # Calculate the time difference between consecutive donations for each donor
    donors['time_diff'] = donors.groupby('donor_id')['visit_date'].diff().dt.days

    # Identify donors who donated twice within a 24-month period
    donors['returning_donor'] = donors.groupby('donor_id')['time_diff'].transform(lambda x: (x.shift(-1) <= 730) & (x <= 730))

    # Aggregate the data to count returning donors over time
    returning_donors_count = donors[donors['returning_donor']].copy()
    returning_donors_count['Year'] = returning_donors_count['visit_date'].dt.year
    returning_donors_yearly = returning_donors_count.groupby('Year').size().reset_index()
    returning_donors_yearly.columns = ['Year', 'Returning Donors']

    # Calculate the percentage change compared to the previous year
    returning_donors_yearly['Percentage Change'] = returning_donors_yearly['Returning Donors'].pct_change() * 100

    # Create a scatter plot using plotly.graph_objects
    fig = go.Figure()

    # Add the line plot
    fig.add_trace(go.Scatter(x=returning_donors_yearly['Year'], y=returning_donors_yearly['Returning Donors'], mode='lines', name='Returning Donors'))

    # Customize the markers to be red in color and larger in size
    fig.add_trace(go.Scatter(x=returning_donors_yearly['Year'], y=returning_donors_yearly['Returning Donors'], mode='markers',
                            marker=dict(color='red', size=10), showlegend=False))

    # Update layout
    fig.update_layout(title={'text': 'Trend of Returning Blood Donors in Malaysia (Yearly Count)', 'x': 0.5},
                    xaxis_title='Year',
                    yaxis_title='Number of Returning Donors',
                    xaxis=dict(tickmode='array', tickvals=returning_donors_yearly['Year']),
                    yaxis=dict(tickmode='linear', tickformat='d'),
                    font=dict(family="Helvetica"))

    # Add labels for number of returning donors above the plot point
    for index, row in returning_donors_yearly.iterrows():
        fig.add_annotation(x=row['Year'], y=row['Returning Donors'], text=str(row['Returning Donors']),
                        showarrow=False, yshift=20)

    # Add labels for percentage change compared to the previous year below the plot point
    for index, row in returning_donors_yearly.iterrows():
        if index > 0:
            change_text = f"{row['Percentage Change']:.2f}%"
            if row['Percentage Change'] > 0:
                change_text = "+" + change_text
            fig.add_annotation(x=row['Year'], y=row['Returning Donors'], text=change_text,
                            showarrow=False, yshift=-20)

    # Save plot to file
    fig.write_image("returning_donors_plot.png")

    # Send the plot to the Telegram chat
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('returning_donors_plot.png', 'rb'), timeout=500)

# Function to handle /start command
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Plot 1: Monthly Blood Donation Counts by State and Year", callback_data='plot_monthly_cumulative')],
        [InlineKeyboardButton("Plot 2: Yearly Blood Donation Counts by State", callback_data='plot_yearly')],
        [InlineKeyboardButton("Plot 3: Yearly Regular Donations for Malaysia", callback_data='plot_yearly_donations_regular')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose a plot:', reply_markup=reply_markup)

# Function to handle button callback
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'plot_monthly_cumulative':
        plot_monthly_cumulative(update, context)
    elif query.data == 'plot_yearly':
        plot_yearly(update, context)
    elif query.data == 'plot_yearly_donations_regular':
        plot_yearly_donations_regular(update, context)
# Function to run the script
def run_script(update: Update, context: CallbackContext):
    # Call your plotting functions here
    plot_monthly_cumulative(update, context)
    plot_yearly(update, context)
    plot_yearly_donations_regular(update, context)

# Main function
def main():
    updater = Updater("6752804307:AAHTCQ9l98R-bmgBn1JT-86GgSaBH2HAZTM", use_context=True)
    dp = updater.dispatcher

    # Add handlers for commands and callbacks
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    # Start the bot
    updater.start_polling()

    # Schedule the script to run every day at 8 am
    schedule.every().day.at("08:00").do(run_script, update=None, context=None)

    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()

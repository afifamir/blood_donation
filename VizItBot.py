import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
import telegram
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
    context.bot.send_photo(chat_id= GROUP_CHAT_ID, photo=open('monthly_plot.png', 'rb'))

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
    context.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=open('yearly_plot.png', 'rb'))

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
    donors_sorted = donors.sort_values(by=['donor_id', 'visit_date'])

    # Group by 'donor_id' for efficient calculation
    donors_grouped = donors_sorted.groupby('donor_id')

    # Calculate time differences within each donor group
    donors_sorted['time_diff'] = donors_grouped['visit_date'].diff().dt.days

    # Identify donors who donated twice within a 24-month period
    time_diff_threshold = 730  # 24 months in days
    within_24_months = (donors_sorted['time_diff'] <= time_diff_threshold) & (donors_sorted['time_diff'].shift(-1) <= time_diff_threshold)
    donors_sorted['returning_donor'] = within_24_months

    # Update the original DataFrame
    donors = donors_sorted.sort_index()

    # Aggregate the data to count returning donors over time
    returning_donors_count = donors[donors['returning_donor']].copy()
    returning_donors_count['Year'] = returning_donors_count['visit_date'].dt.year
    returning_donors_yearly = returning_donors_count.groupby('Year').size().reset_index()
    returning_donors_yearly.columns = ['Year', 'Returning Donors']

    # Calculate the percentage change compared to the previous year
    returning_donors_yearly['Percentage Change'] = returning_donors_yearly['Returning Donors'].pct_change() * 100

    # Set the style
    sns.set(style="whitegrid")

    # Create the Seaborn line plot
    plt.figure(figsize=(12, 6))  # Adjust the figure size as needed
    sns.lineplot(data=returning_donors_yearly, x='Year', y='Returning Donors', marker='o', color='red')

    # Add labels for number of returning donors above the point plot
    for index, row in returning_donors_yearly.iterrows():
        plt.text(row['Year'], row['Returning Donors'] + 10, str(int(row['Returning Donors'])), ha='center', va='bottom', fontsize=12, fontfamily='Helvetica')

    # Add labels for percentage change compared to the previous year below the point plot
    for index, row in returning_donors_yearly.iterrows():
        if index > 0:
            change_text = f"{row['Percentage Change']:.2f}%"
            if row['Percentage Change'] > 0:
                change_text = "+" + change_text
            plt.text(row['Year'], row['Returning Donors'] - 10, change_text, ha='center', va='top', fontsize=12, fontfamily='Helvetica')

    # Add labels and title
    plt.title('Trend of Returning Blood Donors in Malaysia (Yearly Count)', fontsize=14, fontfamily='Helvetica')
    plt.xlabel('Year', fontsize=12, fontfamily='Helvetica')
    plt.ylabel('Number of Returning Donors', fontsize=12, fontfamily='Helvetica')

    # Save plot to file

    plot_filename = "returning_donors_plot.png"
    plt.savefig(plot_filename)

    # Send the plot to the Telegram chat
    context.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=open(plot_filename, 'rb'))



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
def run_script():
    # Create dummy update and context objects
    class DummyUpdate:
        effective_chat = type('EffectiveChat', (), {'id': GROUP_CHAT_ID})  

    class DummyContext:
        def __init__(self):
            # Simulate the bot object
            self.bot = telegram.Bot(token="API_TOKEN")  

    # Instantiate dummy objects
    dummy_update = DummyUpdate()
    dummy_context = DummyContext()

    # Call your plotting functions with the dummy objects
    plot_monthly_cumulative(dummy_update, dummy_context)
    plot_yearly(dummy_update, dummy_context)
    plot_yearly_donations_regular(dummy_update, dummy_context)


# Main function
def main():
    updater = Updater("API_TOKEN", use_context=True)  
    dp = updater.dispatcher

    # Add handlers for commands and callbacks
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    # Start the bot
    updater.start_polling()

    # Schedule the script to run every day at 10.30 am
    schedule.every().day.at("10:30").do(run_script)

    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Function to plot Monthly Cumulative Blood Donation Counts by State
def plot_monthly_cumulative(update: Update, context: CallbackContext):
    # Load data
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
        state_data = daily_counts[daily_counts['state'] == state]
        state_data['cumulative'] = state_data.groupby('year_month')['daily'].cumsum()
        row = ((i - 1) // 2) + 1  # Calculate row index dynamically
        col = ((i - 1) % 2) + 1   # Calculate column index dynamically
        fig.add_trace(go.Scatter(x=state_data['year_month'].astype(str), 
                                 y=state_data['cumulative'], 
                                 mode='lines', 
                                 name=f'Monthly Cumulative Count - {state}'), 
                      row=row, col=col)

    # Update x-axis title for all subplots
    fig.update_xaxes(title_text="Month", row=rows, col=cols)

    # Update y-axis title for all subplots
    fig.update_yaxes(title_text="Monthly Cumulative Count", row=rows, col=cols)

    # Update layout
    fig.update_layout(height=1500, width=1000, showlegend=False, font=dict(family="Helvetica"))

    # Add grand title
    fig.update_layout(title="Monthly Cumulative Blood Donation Counts by State", title_font=dict(family="Helvetica", size=24), title_x=0.5)

    # Save plot to file
    fig.write_image("monthly_cumulative_plot.png")

    # Send the plot to the Telegram chat
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('monthly_cumulative_plot.png', 'rb'))

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
        fig.update_xaxes(title_text="Year", row=row, col=col, tickmode='array', tickvals=state_data['year'].unique(), ticktext=state_data['year'].unique(), tickfont=dict(family='Helvetica'))

        # Update y-axis title and tick font for all subplots
        fig.update_yaxes(title_text="Yearly Count", row=row, col=col, tickfont=dict(family='Helvetica'))

    # Update layout for the entire figure
    fig.update_layout(
        title='Yearly Blood Donation Counts by State',
        title_font=dict(family='Helvetica', size=24),  # Set title font to Helvetica and adjust size
        title_x=0.5,  # Center title
        height=400 * (num_states // 2 + (num_states % 2)),  # Adjust height based on number of states
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
    # Load data
    donations_state = pd.read_csv("https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/donations_state.csv")

    # Filter data for Malaysia state only
    malaysia_data = donations_state[donations_state['state'] == 'Malaysia']

    # Extract year from the date column
    malaysia_data['year'] = pd.to_datetime(malaysia_data['date']).dt.year

    # Group by year and calculate the sum of donations_regular
    yearly_donations = malaysia_data.groupby('year')['donations_regular'].sum().reset_index()

    # Calculate percentage change
    yearly_donations['percentage_change'] = yearly_donations['donations_regular'].pct_change() * 100

    # Create the plot
    fig = go.Figure()

    # Add a trace for yearly donations_regular
    fig.add_trace(go.Scatter(x=yearly_donations['year'], y=yearly_donations['donations_regular'], mode='lines', name='Yearly Donations Regular', marker_color='blue'))

    # Add red markers for each data point
    fig.add_trace(go.Scatter(x=yearly_donations['year'], y=yearly_donations['donations_regular'], mode='markers', marker=dict(color='red'), showlegend=False))

    # Add annotations for each data point
    for i, row in yearly_donations.iterrows():
        if i > 0:
            # Calculate percentage change label
            change_label = f"{row['percentage_change']:.2f}%"
            if row['percentage_change'] > 0:
                change_label = '+' + change_label  # Add '+' sign for positive change
            
            # Add annotation for number of regular donations above the marker
            fig.add_annotation(x=row['year'], y=row['donations_regular'], text=str(row['donations_regular']),
                                showarrow=False,
                                font=dict(family='Helvetica', size=10),
                                yshift=30 if i == 1 else 10)  # Increase yshift for the first label to avoid overlap
            
            # Add annotation for percentage change below the marker
            fig.add_annotation(x=row['year'], y=row['donations_regular'], text=change_label,
                                showarrow=False,
                                font=dict(family='Helvetica', size=10),
                                yshift=-20)

    # Update layout
    fig.update_layout(title='Yearly Donations Regular for Malaysia State',
                      xaxis_title='Year',
                      yaxis_title='Total Donations Regular',
                      font=dict(family='Helvetica'),
                      title_x=0.5,  # Set title's x position to center
                      width=1300,   # Increase the width of the plot
                      xaxis=dict(tickmode='array', tickvals=yearly_donations['year']))  # Set tick values for x-axis

    # Save plot to file
    fig.write_image("yearly_donations_regular_plot.png")

    # Send the plot to the Telegram chat
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('yearly_donations_regular_plot.png', 'rb'))

# Function to handle /start command
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Plot 1: Monthly Cumulative Blood Donation Counts", callback_data='plot_monthly_cumulative')],
        [InlineKeyboardButton("Plot 2: Yearly Blood Donation Counts by State", callback_data='plot_yearly')],
        [InlineKeyboardButton("Plot 3: Yearly Donations Regular for Malaysia State", callback_data='plot_yearly_donations_regular')],
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

# Main function
def main():
    updater = Updater("API_token", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

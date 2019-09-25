from app.models import User, Rating
import plotly
import numpy as np
import pandas as pd
import plotly.graph_objs as go

def datetime(x):
    return np.array(x, dtype=np.datetime64)

def get_ratings(shortname, rating_type='elo'):
    user = User.query.filter_by(shortname=shortname).first()
    ratings = Rating.query \
        .filter_by(rating_type=rating_type) \
        .filter_by(user_id=user.id) \
        .order_by(Rating.timestamp).all()
    values = [r.rating_value for r in ratings]
    dates = datetime([r.timestamp for r in ratings])
    match_ids = [r.match_id for r in ratings]
    source = pd.DataFrame(dict(
        date=dates,
        rating=values,
        match_id=match_ids
    ))

    return source

def plot_ratings(shortname, rating_type, resample_interval):
    """
    Gather the ratings for a user, construct a plot and return the ´div´ element holding the plot
    """
    source = get_ratings(shortname, rating_type=rating_type)
    MIN_MATCHES_FOR_CANDLESTICK = 7
    if len(source) < MIN_MATCHES_FOR_CANDLESTICK:
        # Plot scatterplot if we have few observations
        data = get_scatter_plot(source)
    else:
        # Plot candlestick if we have enough observations
        data = get_candlestick_plot(source, resample_interval=resample_interval)

    data_comp = [data]
    layout_comp = go.Layout(
        title='Performance over time',
        xaxis=dict(
            title='Time',
        ),
        yaxis=dict(
            title='Rating',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    fig_comp = go.Figure(data=data_comp, layout=layout_comp)
    div = plotly.offline.plot(fig_comp, show_link=False, output_type="div", include_plotlyjs=False)
    return div

def get_scatter_plot(source):
    hover_text = []
    for index, row in source.iterrows():
        match_id = row['match_id']
        if pd.isnull(match_id):
            # To allow formatting of ids laters
            match_id = 0
        hover_text.append((
            "Match ID: {match_id}<br>"+
            "Time: {date}<br>"+
            "Rating: {rating}<br>").format(
                match_id = format(match_id, "1.0f") ,
                date = row["date"].ctime(),
                rating = format(row["rating"], "1.0f")
            ))
    
    data = go.Scatter(
            x = source.loc[:,"date"],
            y = source.loc[:,"rating"],
            text = hover_text,
            hoverinfo = 'text',
            marker = dict(
                color = 'green'
            ),
            showlegend = False
        )
    return data
    
def get_candlestick_plot(source, resample_interval='D'):
    # (1) Resample source dataframe so that there is one entry for every resample interval.
    # (2) Convert the source dataframe to a dataframe with four columns: open, high, low, close.
    # (3) Fill in empty rows.
    series = source.set_index("date").loc[:,"rating"]
    resampled = series.resample(resample_interval)
    df_new = resampled.last()
    df_new = df_new.to_frame("close")
    df_new.loc[:,"high"] = resampled.max()
    df_new.loc[:,"low"] = resampled.min()
    df_new.loc[:,"open"] = resampled.first()
    df_new.close.fillna(method = "ffill", inplace = True)
    df_new.fillna(axis = "columns", method = "ffill", inplace = True)
    # TODO: What is going on here?
    # I assume this is to ensure that close on day 1 is equal to open on day 2?
    open_series = df_new.close.shift()
    open_series[0] = df_new.open[0]
    df_new.open = open_series
    df_new.low = np.minimum(df_new.low, df_new.open)
    df_new.high = np.maximum(df_new.high, df_new.open)
    
    hover_text = []
    for index, row in df_new.iterrows():
        hover_text.append((
            "Open: {open_v}<br>"+
            "High: {high}<br>"+
            "Low: {low}<br>"+
            "Close: {close}<br>").format(
                open_v = format(row["open"], "1.0f") , # TODO: Why open_v?
                high = format(row["high"], "1.0f") ,
                low = format(row["low"], "1.0f") ,
                close = format(row["close"], "1.0f"),
            ))

    data = go.Candlestick(x=df_new.index,
                open=df_new.open.values,
                high=df_new.high.values,
                low=df_new.low.values,
                close=df_new.close.values,
                text = hover_text,
                hoverinfo = 'text',
                    )
    return data
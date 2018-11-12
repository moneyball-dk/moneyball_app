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

def plot_ratings(shortname, rating_type):
    source = get_ratings(shortname, rating_type=rating_type)
    hover_text = []
    for index, row in source.iterrows():
        hover_text.append((
            "Match ID: {match_id}<br>"+
            "Time: {date}<br>"+
            "Rating: {rating}<br>").format(
                match_id = format(row["match_id"], "1.0f") ,
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
    data_comp = [data]

    layout_comp = go.Layout(
        title='Performance over time',
        hovermode='closest',
        xaxis=dict(
            title='Time',
        ),
        yaxis=dict(
            title='Rating',
    ))

    fig_comp = go.Figure(data=data_comp, layout=layout_comp)
    div = plotly.offline.plot(fig_comp, show_link=False, output_type="div", include_plotlyjs=False)

    return div

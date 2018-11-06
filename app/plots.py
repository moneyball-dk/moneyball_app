from bokeh.plotting import figure, ColumnDataSource
from bokeh.embed import components
from bokeh.models import HoverTool

from app.models import User, Rating

import numpy as np

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
    source = ColumnDataSource(data=dict(
        date=dates,
        rating=values,
        match_id=match_ids
    ))
    return source

def plot_ratings(shortname, rating_type):
    source = get_ratings(shortname, rating_type=rating_type)
    p = figure(x_axis_type="datetime", tools="",)
    p.line('date', 'rating', source=source)

    p.add_tools(HoverTool(
        tooltips=[
            ('match_id', '@match_id'),
            ('rating', '@rating{0.2f}'),
            ('date', '@date{%F}'),
        ],
        formatters={
            'date':'datetime'
        },
        mode='vline',
    ))
    return p

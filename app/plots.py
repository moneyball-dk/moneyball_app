from bokeh.plotting import figure
from bokeh.embed import components

from app.models import User, Rating

import numpy as np

def datetime(x):
    return np.array(x, dtype=np.datetime64)

def get_ratings(shortname, rating_type='elo'):
    user = User.query.filter_by(shortname=shortname).first()
    ratings = Rating.query \
        .filter_by(rating_type=rating_type) \
        .filter_by(user_id=user.id) \
        .order_by(Rating.timestamp)
    values = [r.rating_value for r in ratings.all()]
    dates = datetime([r.timestamp for r in ratings.all()])
    return dates, values

def plot_ratings(shortname, rating_type):
    dates, values = get_ratings(shortname, rating_type=rating_type)
    p = figure(x_axis_type="datetime")
    p.line(dates, values)
    return p

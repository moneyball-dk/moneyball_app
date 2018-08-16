# Moneyball website

A webapp to track results of foosball games in financial institutions. 
It is a very niche market!

It is mostly a copy of the [Flask tutorial](http://flask.pocoo.org/docs/1.0/tutorial/), with some small changes.

## Prerequisites

Python 3

## Installation

Create a new `venv` with either `python` or `conda`:
```
conda create -n flask python=3 flask
source activate flask
```

Download the source code
```
git clone https://github.com/KPLauritzen/moneyball_app.git
cd moneyball_app
pip install -e .
```

Set enviroment variables (on OSX/linux)
```
export FLASK_APP=moneyball
export FLASK_ENV=development
```

Or set enviroment variables (on Windows `cmd`)
```
set FLASK_APP=moneyball
set FLASK_ENV=development
```

Reset the database
```
flask init-db
```

Start the webserver
```
flask run
```

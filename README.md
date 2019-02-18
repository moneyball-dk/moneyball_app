master: [![Build Status: master](https://travis-ci.org/moneyball-dk/moneyball_app.svg?branch=master)](https://travis-ci.org/moneyball-dk/moneyball_app)
develop: [![Build Status: develop](https://travis-ci.org/moneyball-dk/moneyball_app.svg?branch=develop)](https://travis-ci.org/moneyball-dk/moneyball_app)
# Moneyball website

A webapp to track results of foosball games in financial institutions. 
It is a very niche market!

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
git clone https://github.com/moneyball-dk/moneyball_app.git
cd moneyball_app
```

Install the required packages
```
pip install -r requirements.txt
```

Start the database
```
flask db upgrade
```

Start the webserver
```
flask run
```

Run the tests
```
pytest
```


## Notes for developers

### How to copy DB from moneyball-develop to review app on heroku:
Get list of backups
```
heroku pg:backups --app moneyball-develop
```

Copy a restore a backup from develop to a review app
```
heroku pg:backups:restore moneyball-develop::<backup-id> DATABASE_URL --app <review-app-name>
```
For example:
```
heroku pg:backups:restore moneyball-develop::b003 DATABASE_URL --app moneyball-develop-pr-74
```
After this you will be asked to type in the name of the app you are copying TO to confirm.
If the review app was already running, you need to restart the app. You do this inside the Heroku web UI.
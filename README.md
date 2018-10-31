master: [![Build Status: master](https://travis-ci.org/KPLauritzen/moneyball_app.svg?branch=master)](https://travis-ci.org/KPLauritzen/moneyball_app)
develop: [![Build Status: develop](https://travis-ci.org/KPLauritzen/moneyball_app.svg?branch=develop)](https://travis-ci.org/KPLauritzen/moneyball_app)
# Moneyball website

A webapp to track results of foosball games in financial institutions. 
It is a very niche market!

It is mostly a copy of the [Flask tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world), with some small changes.

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

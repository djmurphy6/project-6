"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)

"""

import os
import logging
import requests
import flask
from flask import request
import acp_times  # Brevet time calculations
import config




###
# Globals
###
app = flask.Flask(__name__)
CONFIG = config.configuration()

##################################################
################### API Callers ################## 
##################################################

API_ADDR = os.environ.get("API_ADDR", "localhost") # set default address to localhost
API_PORT = os.environ["API_PORT"]
API_URL = f"http://{API_ADDR}:{API_PORT}/api/"

def get_brevet():
    """
    Obtains the newest document in the "lists" collection in database
    by calling the RESTful API.

    Returns title (string) and items (list of dictionaries) as a tuple.
    """
    # Get documents (rows) in our collection (table),
    # Sort by primary key in descending order and limit to 1 document (row)
    # This will translate into finding the newest inserted document.

    brevets = requests.get(f"{API_URL}/Brevets").json()

    # lists should be a list of dictionaries.
    # we just need the last one:
    brevet = brevets[-1]
    return brevet["length"], brevet["start_time"], brevet["checkpoints"]


def insert_brevet(length, start_time, checkpoints):
    """
    Inserts a new brevet into the database by calling the API.
    
    Inputs: brevet distance, start time, and checkpoints
    """
    _id = requests.post(f"{API_URL}/Brevets", json={"length": length, "start_time": start_time, "checkpoints": checkpoints}).json()
    return _id

def db_insert(doc):
    # Insert the document into the 'controls' collection in brevets
    # output = db.controls.insert_one(doc)
    # _id = output.inserted_id 
    return "hello"

def db_fetch():
    # fetch the brevet timing information from the 'controls' collection in brevetes
    # output = db.controls.find_one(sort=[('_id', pymongo.DESCENDING)])

    # Convert ObjectId to string
    #if output:
    #    output['_id'] = str(output['_id'])

    return "hello"

###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('calc.html') 
                    # items=list(db.controls.find()))


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('404.html'), 404


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', 0, type=float)
    app.logger.debug("km={}".format(km))

    # get starting time
    time = request.args.get('time', type = str)
    app.logger.debug("time={}".format(time))

    # get brevet distance
    dist = flask.request.args.get("dist", type=int)
    app.logger.debug("dist={}".format(dist))

    # if checkpoint is further than distance, set km to distance
    # if km > dist:
    #    km = dist

    app.logger.debug("request.args: {}".format(request.args))
    


    open_time = acp_times.open_time(km, dist, time).format('YYYY-MM-DDTHH:mm')
    close_time = acp_times.close_time(km, dist, time).format('YYYY-MM-DDTHH:mm')
    result = {"open": open_time, "close": close_time}
    return flask.jsonify(result=result)

@app.route("/submit", methods=["POST"])
def submit():
    # Get the JSON data from the request
    data = request.get_json()
    

    # Extract data from the JSON data
    brevet_distance = data.get('brevetDistance')
    # app.logger.debug("brevet_distance={}".format(brevet_distance))
    begin_date = data.get('beginDate')
    # app.logger.debug("begin_date={}".format(begin_date))
    controls = data.get('tableData', [])
    # app.logger.debug("controls={}".format(controls))

    # Call API
    insert_brevet(brevet_distance, begin_date, controls)
    
    return "recieved and sent document to db_insert"

@app.route("/display")
def display():
    # call db_fetch
    # argument makes it fetch most recent
    # sort=[('_id', pymongo.DESCENDING)]
    data = db_fetch()
    
    # Log the fetched data
    app.logger.debug("Data: {}".format(data))

    # Return the data as JSON
    return flask.jsonify(result=data)

#############

app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0")

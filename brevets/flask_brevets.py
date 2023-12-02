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



###
# Globals
###

#setup Flask app
app = flask.Flask(__name__)
app.debug = True if "DEBUG" not in os.environ else os.environ["DEBUG"]
port_num = True if "PORT" not in os.environ else os.environ["PORT"]
app.logger.setLevel(logging.DEBUG)

##################################################
################### API Callers ################## 
##################################################

API_ADDR = os.environ["API_ADDR"]
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
    app.logger.debug("inside inster_brevets 1 ")
    _id = requests.post(f"{API_URL}/brevets", json={"length": length, "start_time": start_time, "checkpoints": checkpoints}).json()
    app.logger.debug("inside inster_brevets 2 ")
    return _id

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
    try:
        # Get the JSON data from the request
        data = request.json
        if not data:
            raise ValueError("Empty JSON data")

        # Extract data from the JSON data
        brevet_distance = data["brevetDistance"]
        begin_date = data["beginDate"]
        controls = data["tableData"]

        app.logger.debug("brevet_distance: " + brevet_distance)
        app.logger.debug("begin_date: " + begin_date)
        app.logger.debug("controls: " + format(controls))

        # Call API
        brevet_id = insert_brevet(brevet_distance, begin_date, controls)

        return flask.jsonify(result={},
                        message="Inserted!", 
                        status=1,
                        mongo_id=brevet_id)
    except Exception as e:
        app.logger.error("Error submitting data: %s", str(e))
        return flask.jsonify(result={},
                        message="Oh no! Server error!", 
                        status=0, 
                        mongo_id='None')

@app.route("/display")
def display():
    # Call get_brevet
    brevet_data = get_brevet()
    
    # Log the fetched data
    app.logger.debug("Data: {}".format(brevet_data))

    # Return the data as JSON
    return flask.jsonify(result=brevet_data)

#############

if __name__ == "__main__":
    print("Opening for global access on port {}".format(port_num))
    app.run(port=port_num, host="0.0.0.0")

from flask import Flask, request, jsonify, render_template
import redis
import geohash as gh
import proximityhash as ph
from voluptuous import Schema, Required, Coerce

# Connect to database
r = redis.Redis(host='redis', port=6379, db=0)
r.ping()

app = Flask(__name__)

# Handle exceptions and errors
class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

# API Documentation
@app.route('/docs')
def get_docs():
    return render_template('swaggerui.html')


# Calculate population
@app.route('/population')
def population():
    # Define input schema
    parameters = Schema({
        Required('place'): Coerce(str),
        Required('radius'): Coerce(int)
    })
    
    try:
        parameters(request.args.to_dict())
    except Exception as e:
        raise InvalidUsage(str(e), status_code=500)
    
    # Set input parameters
    place = request.args.get('place', type=str)
    radius = request.args.get('radius', type=int)

    # The service is unable to handle over 1000km, the max radius is limited for safety
    if radius > 500:
        raise InvalidUsage('Radius greater than allowed threshold', status_code=500)

    # Find the record for given place
    try:
        geolocation = r.get('pl-'+place.upper())
    except:
        raise InvalidUsage('Unable to connect to database', status_code=500)
    
    # Check if there is a matched place
    if geolocation == None:
        raise InvalidUsage('Location not found in database', status_code=500)
    else:
        try:
            # Seperate latitude and longitude values
            geolocation_decoded = geolocation.decode().split(',')
            # Get geohash list for a given geolocation and radius
            geohash_list = ph.create_geohash(float(geolocation_decoded[0]), float(geolocation_decoded[1]), int(radius*1000), 4)

            # Find the set of all unique populations in the selected geohash list
            geohash_set = r.sunion(geohash_list.split(","))

            # Sum all unique population values to get total
            total_population = sum([int(g) for g in geohash_set])
        except:
            raise InvalidUsage('Unable to process selected location', status_code=500)

    response = {'population': total_population}

    return jsonify(response), 200

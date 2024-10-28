# Import necessary libraries
from flask import Flask, jsonify  # Flask for API creation, jsonify for JSON responses
from sqlalchemy import create_engine, func  # SQLAlchemy for database connection and functions
from sqlalchemy.orm import Session  # Session to handle transactions
from sqlalchemy.ext.automap import automap_base  # Automap for reflecting database tables
import datetime as dt  # DateTime for handling date calculations

# Initialize Flask app
app = Flask(__name__)

# Connect to your database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the existing database into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)  # Reflect tables to use ORM

# Reference tables to make them accessible as Python classes
Measurement = Base.classes.measurement
Station = Base.classes.station

# Function to get the minimum and maximum dates in the dataset
def get_date_range():
    # Start a session to interact with the database
    session = Session(engine)
    # Query the earliest and latest dates
    min_date = session.query(func.min(Measurement.date)).scalar()
    max_date = session.query(func.max(Measurement.date)).scalar()
    # Close session to free resources
    session.close()
    return min_date, max_date

# Define the main route of the API
@app.route("/")
def welcome():
    # Retrieve date range for display purposes
    min_date, max_date = get_date_range()
    # Return available API routes as HTML
    return (
        f"Welcome to the Climate App API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
    )

# Route to get precipitation data for the last 12 months
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Start a session for querying
    session = Session(engine)
    
    # Get the latest date in the dataset
    recent_date = session.query(func.max(Measurement.date)).first()[0]
    recent_date = dt.datetime.strptime(recent_date, "%Y-%m-%d")
    # Calculate the date 12 months back from the latest date
    last_12_months = recent_date - dt.timedelta(days=365)
    
    # Query precipitation data within the last 12 months
    prcp_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= last_12_months).all()
    
    # Close session
    session.close()
    
    # Convert query results to a dictionary format {date: prcp}
    prcp_dict = {date: prcp for date, prcp in prcp_data}
    # Return JSON response
    return jsonify(prcp_dict)

# Route to get the list of stations
@app.route("/api/v1.0/stations")
def stations():
    # Start a session for querying
    session = Session(engine)
    # Query all station IDs
    station_data = session.query(Station.station).all()
    session.close()
    
    # Convert query result tuples to a list of station IDs
    stations_list = [station[0] for station in station_data]
    return jsonify(stations_list)

# Route to get temperature observations (TOBS) for the last 12 months
@app.route("/api/v1.0/tobs")
def tobs():
    # Start a session for querying
    session = Session(engine)
    
    # Get the latest date in the dataset
    recent_date = session.query(func.max(Measurement.date)).first()[0]
    recent_date = dt.datetime.strptime(recent_date, "%Y-%m-%d")
    # Calculate the date 12 months back from the latest date
    last_12_months = recent_date - dt.timedelta(days=365)
    
    # Query temperature observations within the last 12 months
    temp_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= last_12_months).all()
    
    session.close()
    
    # Convert query results to a dictionary format {date: tobs}
    temps_dict = {date: tobs for date, tobs in temp_data}
    return jsonify(temps_dict)

# Route to get temperature statistics (TMIN, TAVG, TMAX) for a given start date and optional end date
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start, end=None):
    # Start a session for querying
    session = Session(engine)
 
    # Define a query selection for minimum, average, and maximum temperature
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    # Conditional logging for date range
    print(f"Start Date: {start}")
    if end:
        print(f"End Date: {end}")
    
    # Perform query based on whether an end date is provided
    if not end:
        # Only start date provided
        temps = session.query(*sel).filter(Measurement.date >= start).all()
    else:
        # Both start and end date provided
        temps = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    
    print(f"Temps Query Result: {temps}")
    session.close()
    
    # Check if the result contains data
    if temps[0][0] is None:
        return jsonify({"error": "No data found for the specified date range."}), 404
    
    # Unpack the result and round the values
    tmin, tavg, tmax = temps[0]
    temp_data = {
        "TMIN": round(tmin, 2),
        "TAVG": round(tavg, 2),
        "TMAX": round(tmax, 2)
    }

    # Return JSON response with temperature statistics
    return jsonify(temp_data)

# Run the application
if __name__ == "__main__":
    app.run(debug=True)

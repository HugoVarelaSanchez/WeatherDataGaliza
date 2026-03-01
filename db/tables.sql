DROP TABLE IF EXISTS WeatherObservation;

/*
Weather Observations:
Store the temperature, wind and precipitation forecasts for a specific
location.
*/
CREATE TABLE WeatherObservation(
    num INTEGER,
    date DATE NOT NULL,
    time TIME NOT NULL,
    sky_state VARCHAR NOT NULL,
    temperature NUMERIC NOT NULL,
    wind NUMERIC NOT NULL,
    precipitation_amount NUMERIC NOT NULL,
    relative_humidity NUMERIC NOT NULL,
    air_pressure_at_sea NUMERIC NOT NULL,

    CONSTRAINT pk_wobs PRIMARY KEY (num)
)

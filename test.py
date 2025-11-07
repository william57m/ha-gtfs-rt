import argparse
import asyncio
import logging
import sys
import yaml

from schema import Optional, Schema, SchemaError

from custom_components.gtfs_rt.const import (
    CONF_API_KEY,
    CONF_API_KEY_HEADER_NAME,
    CONF_DEPARTURES,
    CONF_DIRECTION_ID,
    CONF_ENABLE_STATIC_FALLBACK,
    CONF_ICON,
    CONF_NEXT_BUS_LIMIT,
    CONF_ROUTE,
    CONF_ROUTE_DELIMITER,
    CONF_SERVICE_TYPE,
    CONF_STATIC_GTFS_URL,
    CONF_STOP_ID,
    CONF_TRIP_UPDATE_URL,
    CONF_UPDATE_INTERVAL,
    CONF_VEHICLE_POSITION_URL,
    DEFAULT_UPDATE_INTERVAL,
)
from custom_components.gtfs_rt.sensor import PublicTransportData, SensorFactory

CONF_NAME = "name"

sys.path.append("lib")

PLATFORM_SCHEMA = Schema(
    {
        CONF_TRIP_UPDATE_URL: str,
        Optional(CONF_API_KEY): str,
        Optional(CONF_API_KEY_HEADER_NAME): str,
        Optional(CONF_VEHICLE_POSITION_URL): str,
        Optional(CONF_ROUTE_DELIMITER): str,
        Optional(CONF_UPDATE_INTERVAL): int,
        Optional(CONF_STATIC_GTFS_URL): str,
        Optional(CONF_ENABLE_STATIC_FALLBACK): bool,
        CONF_DEPARTURES: [
            {
                CONF_NAME: str,
                CONF_STOP_ID: str,
                CONF_ROUTE: str,
                Optional(CONF_DIRECTION_ID): str,
                Optional(CONF_SERVICE_TYPE): str,
                Optional(CONF_ICON): str,
                Optional(CONF_NEXT_BUS_LIMIT): int,
            }
        ],
    }
)


def initialize_logging(args) -> None:
    if args["debug"] is None:
        DEBUG_LEVEL = "INFO"
    elif args["debug"].upper() == "INFO" or args["debug"].upper() == "DEBUG":
        DEBUG_LEVEL = args["debug"].upper()
    else:
        raise ValueError("Debug level must be INFO or DEBUG")

    logging.basicConfig(level=DEBUG_LEVEL)


async def main():
    parser = argparse.ArgumentParser(description="Test script for ha-gtfs-rt-v2")
    parser.add_argument(
        "-f", "--file", dest="file", help="Config file to use", metavar="FILE"
    )
    parser.add_argument(
        "-d",
        "--debug",
        dest="debug",
        help="Debug level: INFO (default) or DEBUG",
    )
    args = vars(parser.parse_args())

    if args["file"] is None:
        raise ValueError("Config file spec required.")

    initialize_logging(args)

    with open(args["file"], "r") as test_yaml:
        configuration = yaml.safe_load(test_yaml)

    try:
        PLATFORM_SCHEMA.validate(configuration)
        logging.info("Input file configuration is valid.")

        data = PublicTransportData(
            configuration.get(CONF_TRIP_UPDATE_URL),
            configuration.get(CONF_VEHICLE_POSITION_URL),
            configuration.get(CONF_ROUTE_DELIMITER),
            configuration.get(CONF_API_KEY, None),
            configuration.get(CONF_API_KEY_HEADER_NAME, None),
            configuration.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            configuration.get(CONF_STATIC_GTFS_URL),
            configuration.get(CONF_ENABLE_STATIC_FALLBACK, False),
        )
        await data.load_gtfs_static_data()

        sensors = SensorFactory.create_sensors_from_config(configuration, data)
        for sensor in sensors:
            sensor.update()

    except SchemaError as se:
        logging.info("Input file configuration invalid: {}".format(se))


if __name__ == "__main__":
    asyncio.run(main())

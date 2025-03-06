# General
# =======
#
# The original API specification can be found online as a PDF
# https://www.powerfox.energy/wp-content/uploads/2020/05/powerfox-Kunden-API.pdf
# (in German only).
#
# This document presupposes revision 1.6 from 2021-05-21 of the powerfox API
# version `2.0`. (Actually, no idea what this means.)
#
# In the following, the API is typed and a little bit documented / explained.
#
# Warning concerning the API stability
# ====================================
#
# The actual API differs from the offical specification.
# I tried my best to document the actual behavior of the API and to provide
# accurate types. However, I could not test it to all extent because I only have
# access to a single smart meter device of a certain type among the many supported
# by the API as well as my specific usage scenario.
#
#
# Authentication
# ==============
#
# The customer REST API uses HTTP basic authentication to access the data
# (i.e., your username and password used in the app).
#
#
# Notes
# =====
#
# - Note that the type qualifier `Optional` is used to indicate that the
#   field is not always present in the response.
#

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
from enum import Enum


type Watt = float | int
type Wh = float | int
type kWh = float
type Timestamp = int
""" UNIX UTC timestamp """


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Base Operation: retrieve information about your associated devices
# - endopoint: GET /api/2.0/my/all/devices → list[Device]
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class MeterType(Enum):
    """Type of your Powerfox smart meter"""

    NOT_SPECIFIED = -1
    POWER_METER = 0
    COLD_WATER_METER = 1
    WARM_WATER_METER = 2
    WARMTH_METER = 3
    GAS_METER = 4
    COLD_AND_WARM_WATER_METER = 5


@dataclass
class Device:
    """Metadata about a single Powerfox device."""

    account_associated_since: datetime
    """Timestamp when the device was associated with the account."""
    id: str
    """Unique identifier of the device."""
    division: MeterType
    """Device type."""
    is_main_device: bool
    """Devices that measure consumption or additionally feed-in,
    but not feed-in alone."""
    name: str
    """Name of the device (specified in the app)."""
    prosumer: bool
    """True if bidirectional meter (measures consumption and feed-in),
    false otherwise (only consumption)."""

    def __str__(self) -> str:
        return f"Device({self.name} {self.id})"


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Base Operation: retrieve historical data, i.e., deltas of all devices in kWh
# - includes consumption, feed-in and optionally generation/production (?)
# - deltas are aggregated by 1 hour intervals
# - includes the last 24 hours of deltas
# - endpoint (all devices summed): GET /api/2.0/my/all/report
#   - ?year=yyyy → montly values, starting from yyyy-1-1 to yyyy-12-31
#       - &month=mm → daily values of the specified month in the specified year
#           - &day=dd → hourly values of the specified day …
#               - &fromhour=hh → 15-minute values starting from the specified hour
#                 for 6 hours (= 24 values)
# - endpoint (single device): GET /api/2.0/my/:DeviceId/report
#   - the above URL parameters can also be used for a single device
# - endpoint (CSV of 15-minute aggregated deltas for the last 31 days):
#   GET /api/2.0/my/:DeviceId/reportcsv → CSV file
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@dataclass
class Delta:
    """A single delta value.

    A delta is an aggregated value of the energy consumption or production
    over a certain time interval (e.g., 2 minutes or 1 hour).

    For example: a 1-hour aggregated delta may have a value of 3.5, which
    means that the energy consumption or production was 3.5 kWh in the last hour.

    A timestamp is provided to mark the start of the interval.
    - full hour: a delta with the timestamp '10 a.m.' means from 10:00 to 10:59
    - quarter hour: '09:15' is from 09:15 to 09:29
    - etc.
    """

    delta: kWh
    """The aggregated energy consumption or production in kWh."""
    timestamp: datetime
    """The start of the interval."""
    complete: bool
    """True if the value was measured, false if calculated."""

    # --- undocumented fields ---
    delta_currency: int
    device_id: str
    values_type: int
    # --- end of undocumented fields ---

    delta_ht: Optional[kWh] = None
    """Energy consumption or production during high tariff period.
    Only available for 2-tariff meters."""
    delta_nt: Optional[kWh] = None
    """Energy consumption or production during low tariff period.
    Only available for 2-tariff meters."""


@dataclass
class EnergyFigures:
    """List of deltas and metadata about the deltas in a certain time range.

    The time range can, for example, be the last 24 hours. Depending on the
    aggregation interval of the deltas, the number of deltas in the list may vary.
    For example: 1-hour deltas for the last 24 hours result in a list of 24 deltas.

    Specific to a certain type of energy (e.g., consumption, feed-in, generation).
    """

    sum: kWh
    """Sum of all deltas."""
    max: kWh
    """Maximum value of the deltas."""
    report_values: list[Delta]
    """List of deltas."""

    # --- undocumented fields ---
    start_time: datetime
    start_time_currency: int
    sum_currency: int
    max_currency: int
    meter_readings: list[Any]


@dataclass
class HistoricalData:
    """Historical energy consumption and production (kWh).

    Reports consumption, feed_in and generation, depending on the device type.
    Varying time resolutions / aggregations, depending on the query paramezers.
    """

    consumption: EnergyFigures
    feed_in: EnergyFigures
    generation: Optional[EnergyFigures] = None


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Base Operation: retrieve current energy consumption (Watt) and current meter
# status (Wh or kWh)
# - endpoint: GET /api/2.0/my/main/current → LiveMeterReading
#   - ?unit=kWh (instead of the default Wh)
#   - for the main device
# - endpoint: GET /api/2.0/my/:DeviceId/current → LiveMeterReading
#   - ?unit=kWh (instead of the default Wh)
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@dataclass
class LiveMeterReading:
    """Current power consumption.

    Note that the unit – either Watt hours or kilo Watt hours – can be specified
    through the query parameter `unit`. The default unit is Watt hours.

    The type distinction between Wh and kWh here is only used for documentational purposes.
    """

    watt: Watt
    """Current energy consumption in Watt."""
    timestamp: datetime
    """Timestamp of the reading."""
    a_plus: kWh | Wh
    """Current energy consumption in Wh or kWh."""
    a_minus: kWh | Wh
    outdated: bool
    """True if the data's timestamp is > 60 seconds in the past.
    Can be used for third-party integration.
    """

    a_plus_HT: Optional[kWh | Wh] = None
    """Current energy consumption during high tariff period.
    Only available for 2-tariff meters."""
    a_plus_NT: Optional[kWh | Wh] = None
    """Current energy consumption during low tariff period.
    Only available for 2-tariff meters."""


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Base Operation: retrieve historical energy consumption (Watt)
# - values are aggregated by 2 minutes, last 60 minutes
# - endpoint: GET /api/2.0/my/main/operating → HistoricalWork
# - endpoint: GET /api/2.0/my/:DeviceId/operating → HistoricalWork
# - endpoint: GET /api/2.0/my/:DeviceId/operatingcsv → CSV file
#   - last 7 days
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@dataclass
class Power:
    """Momentary measure of the meter / current power draw."""

    timestamp: datetime
    value: Watt


@dataclass
class HistoricalMeterReading:
    """Power draw readings of the last hour, aggregated in 2 minutes."""

    max: Watt
    min: Watt
    values: list[Power]

    # --- undocumented fields ---
    device_id: str
    avg: Watt

    # values_minus: list[EnergyConsumption]
    # values_plus: list[EnergyConsumption]

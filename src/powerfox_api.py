from model import (
    HistoricalData,
    Device,
    Delta,
    EnergyFigures,
    HistoricalMeterReading,
    LiveMeterReading,
    Power,
)
import requests
from datetime import date, datetime
from typing import Literal, Optional, Any


type JSON = dict[str, Any]


class Parser:
    """Helper class to parse the JSON responses of the API into Python objects."""

    def parse_device(self, json: JSON) -> Device:
        return Device(
            account_associated_since=datetime.fromtimestamp(
                json["AccountAssociatedSince"]
            ),
            id=json["DeviceId"],
            division=json["Division"],
            is_main_device=json["MainDevice"],
            name=json["Name"],
            prosumer=json["Prosumer"],
        )

    def parse_delta(self, json: JSON) -> Delta:
        return Delta(
            delta=json["Delta"],
            timestamp=datetime.fromtimestamp(json["Timestamp"]),
            complete=json["Complete"],
            delta_currency=json["DeltaCurrency"],
            device_id=json["DeviceId"],
            values_type=json["ValuesType"],
            delta_ht=json.get("DeltaHT") if "DeltaHT" in json else None,
            delta_nt=json.get("DeltaNT") if "DeltaNT" in json else None,
        )

    def parse_energy_figures(self, json: JSON) -> EnergyFigures:
        return EnergyFigures(
            sum=json["Sum"],
            max=json["Max"],
            report_values=[self.parse_delta(delta) for delta in json["ReportValues"]],
            start_time=datetime.fromtimestamp(json["StartTime"]),
            start_time_currency=json["StartTimeCurrency"],
            sum_currency=json["SumCurrency"],
            max_currency=json["MaxCurrency"],
            meter_readings=json["MeterReadings"],
        )

    def parse_historical_data(self, json: JSON) -> HistoricalData:
        return HistoricalData(
            consumption=self.parse_energy_figures(json["Consumption"]),
            feed_in=self.parse_energy_figures(json["FeedIn"]),
            generation=self.parse_energy_figures(json["Generation"])
            if "Generation" in json
            else None,
        )

    def parse_live_meterreading(self, json: JSON) -> LiveMeterReading:
        return LiveMeterReading(
            watt=json["Watt"],
            timestamp=datetime.fromtimestamp(json["Timestamp"]),
            a_plus=json["A_Plus"],
            a_minus=json["A_Minus"],
            outdated=json["Outdated"],
            a_plus_HT=json.get("A_Plus_HT") if "A_Plus_HT" in json else None,
            a_plus_NT=json.get("A_Plus_NT") if "A_Plus_NT" in json else None,
        )

    def parse_power(self, json: JSON) -> Power:
        return Power(
            timestamp=datetime.fromtimestamp(json["Timestamp"]),
            value=json["Value"],
        )

    def parse_historical_meterreading(self, json: JSON) -> HistoricalMeterReading:
        return HistoricalMeterReading(
            max=json["Max"],
            min=json["Min"],
            values=[self.parse_power(reading) for reading in json["Values"]],
            avg=json["Avg"],
            device_id=json["DeviceId"],
        )


class PowerfoxAPI:
    """Python client to fetch the powerfox API.

    For detailed information about the API see `model.py` or the README.

    Examples:
    >>> api = PowerfoxAPI("username", "password")
    >>> devices = api.get_devices()
    >>> historical_energy = api.get_historical_data()
    """

    def __init__(
        self,
        username: str,
        password: str,
        *,
        api_url: str = "https://backend.powerfox.energy/api/2.0",
    ):
        """Initialize a new client.

        Args:
            username (str): Username used in the Powerfox app.
            password (str): Password used in the Powerfox app.
            api_url (str, optional): API root URL.
                Defaults to https://backend.powerfox.energy/api/2.0.
        """
        self.username = username
        self.password = password
        self.api_url = api_url
        self._parser = Parser()

    def get_devices_raw(self) -> list[JSON]:
        """Equivalent to `get_devices` but returns the raw JSON response."""
        response = requests.get(
            f"{self.api_url}/my/all/devices", auth=(self.username, self.password)
        )
        response.raise_for_status()
        return response.json()

    def get_devices(self) -> list[Device]:
        """Get a list of devices associated with your account.

        If you prefer the original JSON response, use `get_devices_raw`,
        which returns the unparsed original response.

        Returns:
            list[Device]: The list of devices.
        """
        json = self.get_devices_raw()
        return [self._parser.parse_device(device) for device in json]

    def get_historical_data_raw(
        self,
        device_id: Optional[str] = None,
        *,
        day: Optional[date] = None,
    ) -> JSON:
        """Equivalent to `get_historical_data` but returns the raw JSON response."""
        device_id = device_id or "main"
        day_param = f"?year={day.year}&month={day.month}&day={day.day}" if day else ""

        response = requests.get(
            f"{self.api_url}/my/{device_id}/report{day_param}",
            auth=(self.username, self.password),
        )
        response.raise_for_status()
        return response.json()

    def get_historical_data(
        self,
        device_id: Optional[str] = None,
        *,
        day: Optional[date] = None,
    ) -> HistoricalData:
        """Get historical data of your energy consumption, feed-in and generation.

        The data is returned as a `HistoricalData` object. See the type for more details.
        This is especially important since the data might be aggregated in different ways
        depending on the time frame.

        Note that the API allows other params, for example only yearly reports instead
        of daily ones. However, this is not implemented at the moment.

        Args:
            device_id (Optional[str], optional): Specific device, otherwise main device.
            Defaults to None.
            day (Optional[date], optional): Specific date, otherwise last 24h.
            Defaults to None.

        Returns:
            HistoricalData: The historical data.
        """
        json = self.get_historical_data_raw(device_id=device_id, day=day)
        return self._parser.parse_historical_data(json)

    def get_live_meterreading_raw(
        self,
        device_id: Optional[str] = None,
        *,
        unit: Literal["Wh", "kWh"] = "Wh",
    ) -> JSON:
        """Equivalent to `get_live_meterreading` but returns the raw JSON response."""
        device_id = device_id or "main"
        unit_param = f"?unit={unit}" if unit == "kWh" else ""
        response = requests.get(
            f"{self.api_url}/my/{device_id}/current{unit_param}",
            auth=(self.username, self.password),
        )
        response.raise_for_status()
        return response.json()

    def get_live_meterreading(
        self,
        device_id: Optional[str] = None,
        *,
        unit: Literal["Wh", "kWh"] = "Wh",
    ) -> LiveMeterReading:
        """Get the live power reading of your device.

        The data is returned as a `LiveMeterReading` object. See the type for more details.

        Args:
            device_id (Optional[str], optional): Specific device. Defaults to None.
            unit (Literal[&quot;Wh&quot;, &quot;kWh&quot;], optional): Unit of the returned data.
            Defaults to "Wh".

        Returns:
            LiveMeterReading: The live meter reading (current power draw).
        """
        json = self.get_live_meterreading_raw(device_id=device_id, unit=unit)
        return self._parser.parse_live_meterreading(json)

    def get_historical_meterreading_raw(self, device_id: Optional[str] = None) -> JSON:
        """Equivalent to `get_historical_meterreading` but returns the raw JSON response."""
        device_id = device_id or "main"
        response = requests.get(
            f"{self.api_url}/my/{device_id}/operating",
            auth=(self.username, self.password),
        )
        response.raise_for_status()
        return response.json()

    def get_historical_meterreading(
        self, device_id: Optional[str] = None
    ) -> HistoricalMeterReading:
        """Get the historical meter readings of your device.

        The data is returned as a `HistoricalMeterReading` object. See the type for more details.
        Data is in Watt.

        Args:
            device_id (Optional[str], optional): Specific device. Defaults to None.

        Returns:
            HistoricalMeterReading: Historical meter readings (power draw over time).
        """
        json = self.get_historical_meterreading_raw(device_id=device_id)
        return self._parser.parse_historical_meterreading(json)

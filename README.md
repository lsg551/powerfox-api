# Powerfox API Client

> [!WARNING]
> I am not using the poweropti anymore and therefore will not maintain this
> repository. I will accept pull requests and fixes, though.

This repository provides an <b><u>unofficial Python client</u></b> to scrape the
public Powerfox API.

_powerfox Energy GmbH_, located in Germany, creates smart meter reading devices,
such as the **poweropti**: an IR-based smart meter reader that attaches to your
smart power meter and allows you to monitor your energy consumption and
production in real-time. The device is connected to their cloud, but the data
can be accessed through their public REST API.

## Installation

The library only depends on `requests` and Python >= 3.12. Because it has only
two files, just clone the repository and copy the files as you like.

```bash
$ git clone git@github.com:lsg551/powerfox-api.git
```

## Usage

Make yourself familiar with their API by quickly reading
[`model.py`](src/model.py).

Sorry for the unintuitive API of the client. It adheres to the terminology of
Powerfox's REST API, which can be quite confusing at first.

The `PowerfoxAPI` class is the only class needed. Pass your credentials and you
are good to go.

```python
from powerfox_api import PowerfoxAPI

# usename / password that you also use in your app ...
api = PowerfoxAPI("your_username", "your_password")

# --- to get a list of your devices ---

devices = api.get_devices()

# usually not required, because your account
# has one main devices that is assumed by default
device = devices[0].id

# --- (historica) energy (Wh) consumption and production ---

historical_energy = api.get_historical_data(devices[0].id)

# --- (live OR historical) power draw (Watt) readings ---

live_power = api.get_live_data(devices[0].id)
historical_power = api.get_historical_power(devices[0].id)
```

Note that all these methods parse the returned JSON data into typed objects. The
`PowerfoxAPI` also provides access to the unparsed JSON data via duplicated
methods with a `_raw` suffix – e.g. instead of `get_devices` use
`get_devices_raw`.

Be aware that the powerfox API limits the number of requests per time unit. If
you exceed this limit, you will be blocked for a certain time.

## Creating a Backup of Your Data

You can run the notebook [`backup.ipynb`](./src/backup.ipynb) to create a backup
of your energy consumption. It outputs a JSON Lines file with daily readings of
15-minute aggregated values. Unfortunately, a backup of your power draw data can
not be created, because the REST API does not provide this data.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file.

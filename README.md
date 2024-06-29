# Homeconnect  - hcpy for Bosch Dishwasher

[![License][license-shield]][license]
[![Open in Visual Studio Code][open-in-vscode-shield]][open-in-vscode]
[![Python 3.11.9](https://img.shields.io/badge/python-3.11.9-blue.svg)](https://www.python.org/downloads/release/python-3119/)
[![Support author][donate-me-shield]][donate-me]

[license-shield]: https://img.shields.io/static/v1?label=License&message=MIT&color=orange&logo=license
[license]: https://opensource.org/licenses/MIT

[open-in-vscode-shield]: https://img.shields.io/static/v1?label=+&message=Open+in+VSCode&color=blue&logo=visualstudiocode
[open-in-vscode]: https://open.vscode.dev/zibous/homeconnect-hcpy

[donate-me-shield]: https://img.shields.io/static/v1?label=+&color=orange&message=Buy+me+a+coffee
[donate-me]: https://www.buymeacoff.ee/zibous


Python tool to talk to Home Connect appliances over the local network (no cloud required)

## Device

Dishwasher Bosch SMV4HCX48E/24

![Dishwasher Bosch SMV4HCX48E/24](images/dishwasher.png "Dishwasher Bosch SMV4HCX48E/24")

## Interface with Home Connect appliances in Python

This is a very, very beta interface for Bosch-Siemens Home Connect
devices through their local network connection.  Unlike most
IoT devices that have a reputation for very bad security, BSG seem to have
done a decent job of designing their system, especially since
they allow a no-cloud local control configuration.  The protocols
seem sound, use well tested cryptographic libraries (TLS PSK with
modern ciphres) or well understood primitives (AES-CBC with HMAC),
and should prevent most any random attacker on your network from being able to
[take over your appliances to mine cryptocurrency](http://www.antipope.org/charlie/blog-static/2013/12/trust-me.html).

*WARNING: This tool not ready for prime time and is still beta!*

**More Information for details see**: <br/>
[![](https://img.shields.io/badge/Info_hcpy_lib-orange?style=for-the-badge)](https://github.com/hcpy2-0/hcpy)

## Setup

To avoid running into issues later with your default python installs, it's recommended to use a py virtual env for doing this.
I have had good experiences with `pyenv` With `pyenv` you can use your own Python versions / virtual environment for each application.<br/>

[![](https://img.shields.io/badge/see_PYENV_Install-orange?style=for-the-badge)](https://github.com/pyenv/pyenv)


Go to your desired test directory, and:

```bash
pyenv --version
pyenv install 3.10.14
pyenv virtualenv 3.10.14 apps
pyenv local apps
git clone https://github.com/hcpy2-0/hcpy
cd hcpy
pip install -r requirements.txt
pip install pipreqs
pip install pyclean
```

## Docker APP
The application can also be installed with a Docker installation. A local Docker image is created with `build.sh` and then installed.

```bash
 #!/bin/bash

DOCKERIMAGE="homeconnect"
CONTAINERLABEL="homeconnect"
DOCKER_TIMEZONE=Europe/Berlin

# persistant applications dir
APPSDATA=/dockerapps/_lab/homeconnect

echo "Clean Python app ${DOCKERIMAGE}..."
pyclean . --debris --verbose

echo "Try to remove previuos installation..."
docker stop ${CONTAINERLABEL} >/dev/null 2>&1
docker rm ${CONTAINERLABEL} >/dev/null 2>&1

echo "Build Docker Image ${DOCKERIMAGE}..."
docker build -t ${DOCKERIMAGE} .

echo "Install Docker Image ${DOCKERIMAGE}..."
docker run -it --detach  \
           --name ${CONTAINERLABEL} \
           --volume ${APPSDATA}/config:/app/config  \
           --env TZ=${DOCKER_TIMEZONE} \
           --restart unless-stopped \
           ${DOCKERIMAGE}

echo "Docker App ${DOCKERIMAGE} ready..."

```
<br/><br/>


## Create device devices.json
The `hc-login.py ` script perfoms the OAuth process to login to your
Home Connect account with your usename and password.  It
receives a bearer token that can then be used to retrieves
a list of all the connected devices, their authentication
and encryption keys, and XML files that describe all of the
features and options.

### Requirements:

  - Valid singlekey-id account (username, password)
  - Device registered with singlekey-id account

<br/>

```bash
python hc-login.py singlekey.id.email singlekey.id.password >config/devices.json
```

This only needs to be done once or when you add new devices;
the resulting configuration JSON file *should* be sufficient to
connect to the devices on your local network, assuming that
your mDNS or DNS server resolves the names correctly.

<br/><br/>

## Home Connect to MQTT

Use the following ./config/config.json example:

```json
{
    "devices_file": "./config/devices.json",
    "mqtt_host": "localhost",
    "mqtt_username": "<redakted>",
    "mqtt_password": "<redakted>",
    "mqtt_port": 1883,
    "mqtt_prefix": "homeconnect/",
    "mqtt_ssl": false,
    "mqtt_cafile": null,
    "mqtt_certfile": null,
    "mqtt_keyfile": null,
    "mqtt_clientname": "lab.hcapp",
    "domain_suffix":"",
    "debug": false,
    "locale": "de",
    "LOGLEVEL": "DEBUG"
}
```

<br/><br/>

## Start Application

After the config.json and devices.json are in the ./config directory, the application can be started with the python command

<br/>

```bash
user@linux /dockerapps/homeconnect:  python bosch.app
```

### Application logging

```ini
2024-06-27 18:02:51.103730 MQTT connection established: 0
2024-06-27 18:02:51.103879 dishwasher set topic: homeconnect/dishwasher/set
2024-06-27 18:02:51.103987 dishwasher program topic: homeconnect/dishwasher/activeProgram
2024-06-27 18:02:54.099795 dishwasher connecting to bosch-dishwasher.local
2024-06-27 18:02:55.360850 DEBUGGER: WebSocketApp wss://bosch-dishwasher.local:443/homeconnect
2024-06-27 18:02:55.570076 dishwasher Message resource: /ei/initialValues
2024-06-27 18:02:55.675895 dishwasher Message resource: /ci/services
2024-06-27 18:02:56.654911 dishwasher Message resource: /iz/info
2024-06-27 18:02:56.655067 dishwasher publish state data to homeconnect/dishwasher/state
2024-06-27 18:02:57.219164 dishwasher Message resource: /ci/registeredDevices
2024-06-27 18:02:57.875598 dishwasher Message resource: /ni/info
2024-06-27 18:02:57.875773 dishwasher publish state data to homeconnect/dishwasher/state
2024-06-27 18:02:57.876867 dishwasher Message resource: /ni/config
2024-06-27 18:02:57.880480 dishwasher Message resource: /ro/allMandatoryValues
2024-06-27 18:02:57.881098 dishwasher Calc the water and energy usage
2024-06-27 18:02:58.238171 dishwasher is currently not consuming any energy
2024-06-27 18:02:58.791692 dishwasher does not need water at the moment
2024-06-27 18:02:58.791904 dishwasher publish state data to homeconnect/dishwasher/state
2024-06-27 18:02:58.792590 dishwasher Message resource: /ro/allDescriptionChanges
2024-06-27 18:02:58.792657 dishwasher Access change for 555 to NONE
2024-06-27 18:02:58.792745 dishwasher Access change for 558 to READWRITE
2024-06-27 18:02:58.792810 dishwasher Access change for 5136 to READ
.... more will come here
```

<br/><br/>

## What's Changed

- **h2mqtt.py**
   - `bosch.app` instead of `h2mqtt.py`
   -  loading `settings.json` instead of `settings.ini`
   -  simple dishwascher state manager
   -  `onStateChanged` to get the energie- and water consumption

- **HCDevice.py**

  -  **Modified** <br/>
     - self.device_id = base64url_encode(get_random_bytes(6)).decode("UTF-8")

  - **<span>Disabled Error 404,400</span>**

     -  dishwasher Message **<i>Error: 404</i>**: ***/ci/authentication***<br/>
    	 `self.get("/ci/authentication", version=2, data={"nonce": self.token})` <br/>

     - dishwasher Message **<i>Error: 404</i>**: ***/ci/info***<br/>
	     `self.get("/ci/info")  # clothes washer` <br/>

     - dishwasher Message **<i>Error: 404</i>**: ***/ci/tzInfo***<br/>
		 `self.get("/ci/tzInfo")` <br/>

	  - dishwasher Message **<i>Error: 404</i>**: ***/ni/config***<br/>
		 `self.get("/ni/config", data={"interfaceID": 0})`<br/>

     - dishwasher Message **<i>Error: 400</i>** ***/ro/values***<br/>
	     `self.get("/ro/values")` <br/>

-  **paho-mqtt Version: 2.1.0** <br>
    [MQTT version 5.0 client](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html)



<br/><br/>


## devices.json

The devices.json created via `hc-login.py` looks like this

```json
 [
    {
        "name": "dishwasher",
        "host": "bosch-dishwasher.local",
        "key": "<redakted>",
        "description": {
            "type": "Dishwasher",
            "brand": "BOSCH",
            "model": "SMV4HCX48E",
            "version": "3",
            "revision": "1"
        },
        "features": {
            "512": {
                "name": "BSH.Common.Command.AbortProgram",
                "access": "none",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "6": {
                "name": "BSH.Common.Command.AcknowledgeEvent",
                "access": "writeOnly",
                "available": "true",
                "refCID": "15",
                "refDID": "81"
            },
            "594": {
                "name": "BSH.Common.Command.AllowSoftwareDownload",
                "access": "writeOnly",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "611": {
                "name": "BSH.Common.Command.AllowSoftwareUpdate",
                "access": "writeOnly",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "575": {
                "name": "BSH.Common.Command.AllowSoftwareUpdateLocalWiFi",
                "access": "writeOnly",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "553": {
                "name": "BSH.Common.Command.ApplyFactoryReset",
                "access": "writeOnly",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "555": {
                "name": "BSH.Common.Command.DeactivateRemoteControlStart",
                "access": "writeOnly",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "1": {
                "name": "BSH.Common.Command.DeactivateWiFi",
                "access": "writeOnly",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "16": {
                "name": "BSH.Common.Command.RejectEvent",
                "access": "writeOnly",
                "available": "true",
                "refCID": "15",
                "refDID": "81"
            },
            "556": {
                "name": "BSH.Common.Command.SetWaterHardness",
                "access": "writeOnly",
                "available": "true",
                "refCID": "18",
                "refDID": "81"
            },
            "525": {
                "name": "BSH.Common.Event.AquaStopOccured",
                "handling": "none",
                "level": "critical",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "46": {
                "name": "BSH.Common.Event.ConfirmPermanentRemoteStart",
                "handling": "none",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "577": {
                "name": "BSH.Common.Event.ConnectLocalWiFi",
                "handling": "none",
                "level": "warning",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "543": {
                "name": "BSH.Common.Event.LowWaterPressure",
                "handling": "none",
                "level": "alert",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "545": {
                "name": "BSH.Common.Event.ProgramAborted",
                "handling": "acknowledge",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "540": {
                "name": "BSH.Common.Event.ProgramFinished",
                "handling": "none",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "593": {
                "name": "BSH.Common.Event.SoftwareDownloadAvailable",
                "handling": "acknowledge",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "21": {
                "name": "BSH.Common.Event.SoftwareUpdateAvailable",
                "handling": "acknowledge",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "595": {
                "name": "BSH.Common.Event.SoftwareUpdateSuccessful",
                "handling": "acknowledge",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "32773": {
                "name": "BSH.Common.Option.BaseProgram"
            },
            "561": {
                "name": "BSH.Common.Option.EnergyForecast"
            },
            "32772": {
                "name": "BSH.Common.Option.ProgramName"
            },
            "542": {
                "name": "BSH.Common.Option.ProgramProgress"
            },
            "544": {
                "name": "BSH.Common.Option.RemainingProgramTime"
            },
            "549": {
                "name": "BSH.Common.Option.RemainingProgramTimeIsEstimated"
            },
            "558": {
                "name": "BSH.Common.Option.StartInRelative"
            },
            "562": {
                "name": "BSH.Common.Option.WaterForecast"
            },
            "32828": {
                "name": "BSH.Common.Program.Favorite.001"
            },
            "256": {
                "name": "BSH.Common.Root.ActiveProgram"
            },
            "261": {
                "name": "BSH.Common.Root.CommandList"
            },
            "260": {
                "name": "BSH.Common.Root.EventList"
            },
            "262": {
                "name": "BSH.Common.Root.OptionList"
            },
            "263": {
                "name": "BSH.Common.Root.ProgramGroup"
            },
            "257": {
                "name": "BSH.Common.Root.SelectedProgram"
            },
            "259": {
                "name": "BSH.Common.Root.SettingList"
            },
            "258": {
                "name": "BSH.Common.Root.StatusList"
            },
            "3": {
                "name": "BSH.Common.Setting.AllowBackendConnection",
                "access": "readWrite",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "32824": {
                "name": "BSH.Common.Setting.Favorite.001.Functionality",
                "access": "readWrite",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Program"
                }
            },
            "32825": {
                "name": "BSH.Common.Setting.Favorite.001.Name",
                "access": "readWrite",
                "available": "true",
                "max": "30",
                "min": "0",
                "refCID": "05",
                "refDID": "8B"
            },
            "32826": {
                "name": "BSH.Common.Setting.Favorite.001.Program",
                "access": "readWrite",
                "available": "true",
                "max": "1",
                "min": "0",
                "refCID": "A8",
                "refDID": "408D"
            },
            "539": {
                "name": "BSH.Common.Setting.PowerState",
                "access": "readWrite",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "1": "Off",
                    "2": "On"
                }
            },
            "15": {
                "name": "BSH.Common.Setting.RemoteControlLevel",
                "access": "readWrite",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Monitoring",
                    "1": "ManualRemoteStart",
                    "2": "PermanentRemoteStart"
                }
            },
            "5": {
                "name": "BSH.Common.Status.BackendConnected",
                "access": "read",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "527": {
                "name": "BSH.Common.Status.DoorState",
                "access": "read",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Open",
                    "1": "Closed"
                }
            },
            "614": {
                "name": "BSH.Common.Status.ErrorCodesList",
                "access": "read",
                "available": "true",
                "refCID": "85",
                "refDID": "408B"
            },
            "32771": {
                "name": "BSH.Common.Status.Favorite.Handling",
                "access": "read",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "AsList",
                    "1": "AsButtons"
                }
            },
            "552": {
                "name": "BSH.Common.Status.OperationState",
                "access": "read",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Inactive",
                    "1": "Ready",
                    "2": "DelayedStart",
                    "3": "Run",
                    "4": "Pause",
                    "5": "ActionRequired",
                    "6": "Finished",
                    "7": "Error",
                    "8": "Aborting"
                }
            },
            "615": {
                "name": "BSH.Common.Status.Program.All.Count.Started",
                "access": "read",
                "available": "false",
                "refCID": "02",
                "refDID": "81"
            },
            "523": {
                "name": "BSH.Common.Status.RemoteControlActive",
                "access": "read",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "517": {
                "name": "BSH.Common.Status.RemoteControlStartAllowed",
                "access": "read",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "592": {
                "name": "BSH.Common.Status.SoftwareUpdateTransactionID",
                "access": "read",
                "available": "true",
                "refCID": "26",
                "refDID": "83"
            },
            "4609": {
                "name": "Dishcare.Dishwasher.Event.CheckFilterSystem",
                "handling": "none",
                "level": "alert",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4611": {
                "name": "Dishcare.Dishwasher.Event.DrainPumpBlocked",
                "handling": "none",
                "level": "alert",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4610": {
                "name": "Dishcare.Dishwasher.Event.DrainingNotPossible",
                "handling": "none",
                "level": "alert",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4608": {
                "name": "Dishcare.Dishwasher.Event.InternalError",
                "handling": "none",
                "level": "alert",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4613": {
                "name": "Dishcare.Dishwasher.Event.LowVoltage",
                "handling": "none",
                "level": "alert",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4655": {
                "name": "Dishcare.Dishwasher.Event.MachineCareAndFilterCleaningReminder",
                "handling": "acknowledge",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4628": {
                "name": "Dishcare.Dishwasher.Event.MachineCareReminder",
                "handling": "acknowledge",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4625": {
                "name": "Dishcare.Dishwasher.Event.RinseAidLack",
                "handling": "none",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4627": {
                "name": "Dishcare.Dishwasher.Event.RinseAidNearlyEmpty",
                "handling": "none",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4624": {
                "name": "Dishcare.Dishwasher.Event.SaltLack",
                "handling": "none",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4626": {
                "name": "Dishcare.Dishwasher.Event.SaltNearlyEmpty",
                "handling": "none",
                "level": "hint",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "4612": {
                "name": "Dishcare.Dishwasher.Event.WaterheaterCalcified",
                "handling": "none",
                "level": "alert",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Present",
                    "2": "Confirmed"
                }
            },
            "5121": {
                "name": "Dishcare.Dishwasher.Option.ExtraDry"
            },
            "5124": {
                "name": "Dishcare.Dishwasher.Option.HalfLoad"
            },
            "5136": {
                "name": "Dishcare.Dishwasher.Option.SilenceOnDemand"
            },
            "5127": {
                "name": "Dishcare.Dishwasher.Option.VarioSpeedPlus"
            },
            "8195": {
                "name": "Dishcare.Dishwasher.Program.Auto2"
            },
            "8196": {
                "name": "Dishcare.Dishwasher.Program.Eco50"
            },
            "8192": {
                "name": "Dishcare.Dishwasher.Program.Intensiv70"
            },
            "8215": {
                "name": "Dishcare.Dishwasher.Program.MachineCare"
            },
            "8202": {
                "name": "Dishcare.Dishwasher.Program.NightWash"
            },
            "8200": {
                "name": "Dishcare.Dishwasher.Program.PreRinse"
            },
            "8203": {
                "name": "Dishcare.Dishwasher.Program.Quick65"
            },
            "4363": {
                "name": "Dishcare.Dishwasher.Setting.EcoAsDefault",
                "access": "readWrite",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "LastProgram",
                    "1": "EcoAsDefault"
                }
            },
            "4356": {
                "name": "Dishcare.Dishwasher.Setting.ExtraDry",
                "access": "readWrite",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "4357": {
                "name": "Dishcare.Dishwasher.Setting.HotWater",
                "access": "readWrite",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "ColdWater",
                    "1": "HotWater"
                }
            },
            "4378": {
                "name": "Dishcare.Dishwasher.Setting.InfoLight",
                "access": "readWrite",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "4354": {
                "name": "Dishcare.Dishwasher.Setting.RinseAid",
                "access": "readWrite",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "R01",
                    "2": "R02",
                    "3": "R03",
                    "4": "R04",
                    "5": "R05",
                    "6": "R06"
                }
            },
            "4355": {
                "name": "Dishcare.Dishwasher.Setting.SensitivityTurbidity",
                "access": "readWrite",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Standard",
                    "1": "Sensitive",
                    "2": "VerySensitive"
                }
            },
            "4382": {
                "name": "Dishcare.Dishwasher.Setting.SilenceOnDemandDefaultTime",
                "access": "readWrite",
                "available": "true",
                "max": "1800",
                "min": "60",
                "refCID": "10",
                "refDID": "82",
                "stepSize": "60"
            },
            "4364": {
                "name": "Dishcare.Dishwasher.Setting.SoundLevelSignal",
                "access": "readWrite",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "Off",
                    "1": "Low",
                    "2": "Medium",
                    "3": "High"
                }
            },
            "4384": {
                "name": "Dishcare.Dishwasher.Setting.SpeedOnDemand",
                "access": "read",
                "available": "true",
                "refCID": "01",
                "refDID": "00"
            },
            "4367": {
                "name": "Dishcare.Dishwasher.Setting.WaterHardness",
                "access": "readWrite",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "H00",
                    "1": "H01",
                    "2": "H02",
                    "3": "H03",
                    "4": "H04",
                    "5": "H05",
                    "6": "H06",
                    "7": "H07"
                }
            },
            "4096": {
                "name": "Dishcare.Dishwasher.Status.ProgramPhase",
                "access": "read",
                "available": "true",
                "refCID": "03",
                "refDID": "80",
                "values": {
                    "0": "None",
                    "1": "PreRinse",
                    "2": "MainWash",
                    "3": "FinalRinse",
                    "4": "Drying"
                }
            },
            "4101": {
                "name": "Dishcare.Dishwasher.Status.SilenceOnDemandRemainingTime",
                "access": "read",
                "available": "true",
                "refCID": "10",
                "refDID": "82"
            },
            "8213": {
                "name": "Dishcare.Dishwasher.Program.Kurz60"
            },
            "8199": {
                "name": "Dishcare.Dishwasher.Program.Quick45"
            }
        }
    }
]
```
<br/>

## Optional add `addons` to devices.json

With the entries in the `addons` section, additional components can be created.
For example, to record the energy and water consumption per session, a Sonoff device is used as
a `power meter` and an `ESP water meter` is used for water consumption.

```json
        ....
        "description": {
            "type": " Dishwasher",
            "brand": "BOSCH",
            "model": "SMV4HCX48E",
            "version": "3",
            "revision": "1"
        },
        "addons": {
            "installed": "2022-09-06 12:00:00",
            "powermeter":"http://sonoff-dishwasher.siebler.home/cm?cmnd=status+8",
            "watermeter":"http://water-meter-esp.local/sensor/wasseruhr_anzeige",
            "taps": 20,
            "taps_min": 5
        },
        "features": {
        .....
        }
```

<br/><br/><br/>

## MQTT Payload

The application always sends an MQTT message when something has changed in the `states`.

```json
{
    "AllowBackendConnection": true,
    "BackendConnected": true,
    "RemoteControlLevel": "PermanentRemoteStart",
    "SoftwareUpdateAvailable": "Off",
    "ConfirmPermanentRemoteStart": "Off",
    "ActiveProgram": 0,
    "SelectedProgram": 8195,
    "RemoteControlStartAllowed": true,
    "520": "2024-06-28T11:22:24",
    "RemoteControlActive": true,
    "AquaStopOccured": "Off",
    "DoorState": "Closed",
    "535": false,
    "PowerState": "Off",
    "ProgramFinished": "Off",
    "ProgramProgress": 0,
    "LowWaterPressure": "Off",
    "RemainingProgramTime": 8400,
    "ProgramAborted": "Off",
    "547": false,
    "RemainingProgramTimeIsEstimated": true,
    "OperationState": "Ready",
    "StartInRelative": 0,
    "EnergyForecast": 57,
    "WaterForecast": 54,
    "ConnectLocalWiFi": "Off",
    "SoftwareUpdateTransactionID": 0,
    "SoftwareDownloadAvailable": "Off",
    "SoftwareUpdateSuccessful": "Off",
    "ErrorCodesList": {
        "length": 0,
        "list": []
    },
    "Started": 155,
    "ProgramPhase": "None",
    "SilenceOnDemandRemainingTime": 0,
    "RinseAid": "Off",
    "SensitivityTurbidity": "Standard",
    "ExtraDry": false,
    "HotWater": "ColdWater",
    "EcoAsDefault": "LastProgram",
    "SoundLevelSignal": "High",
    "WaterHardness": "H00",
    "InfoLight": true,
    "SilenceOnDemandDefaultTime": 1800,
    "SpeedOnDemand": false,
    "InternalError": "Off",
    "CheckFilterSystem": "Off",
    "DrainingNotPossible": "Off",
    "DrainPumpBlocked": "Off",
    "WaterheaterCalcified": "Off",
    "LowVoltage": "Off",
    "SaltLack": "Off",
    "RinseAidLack": "Off",
    "SaltNearlyEmpty": "Off",
    "RinseAidNearlyEmpty": "Off",
    "MachineCareReminder": "Off",
    "4632": 0,
    "4641": 0,
    "4654": 0,
    "MachineCareAndFilterCleaningReminder": "Off",
    "HalfLoad": false,
    "VarioSpeedPlus": false,
    "SilenceOnDemand": false,
    "Handling": "AsButtons",
    "Functionality": "Off",
    "Name": "dishwasher",
    "Program": {
        "length": 0,
        "list": []
    },
    "lastupdate": "2024-06-28 13:22:27.964811",
    "isrunning": false,
    "powermeter": {
        "StatusSNS": {
            "Time": "2024-06-28T12:22:27",
            "ENERGY": {
                "TotalStartTime": "2022-09-03T13:02:25",
                "Total": 167.861,
                "Yesterday": 0.065,
                "Today": 0.033,
                "Power": 4,
                "ApparentPower": 14,
                "ReactivePower": 13,
                "Factor": 0.27,
                "Voltage": 227,
                "Current": 0.061
            }
        }
    },
    "powerdisplay": 167.861,
    "energy_used": 0.0,
    "watermeter": {
        "id": "sensor-wasseruhr_anzeige",
        "value": 7.648,
        "state": "7.648 m\u00b3"
    },
    "watermeterdisplay": 7648.0,
    "water_used": 0.0
}
```
<br/>
<hr size="1">

## Homeassisant

Instead of MQTT Discovery, I use an MQTT template (see directory `/homeassistant/dishwasher.yaml`) to use the device with the settings in Homeassistant.

- [Homeassistant Template for Bosch Dishwasher](./homeassistant/dishwasher.yaml)

<br/>
<br/>

## Additional Informations


- [Python tool to talk to Home Connect appliances osresearch/hcpy](https://github.com/osresearch/hcpy)
- [Python tool to talk to Home Connect appliances hcpy2-0/hcpy](https://github.com/hcpy2-0/hcpy)
- [SingleKey ID, One Digital Key for Many Brands](https://singlekey-id.com)
- [Bosch Products Homepage](https://www.bosch-home.at)
- [Home Connect – Connect your household](https://api-docs.home-connect.com/quickstart/)
- [Connect Developer Program](https://developer.home-connect.com/)

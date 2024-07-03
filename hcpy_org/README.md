# Testcase Interface with Home Connect appliances in Python

is a very, very beta interface for Bosch-Siemens Home Connect
devices through their local network connection.  Unlike most
IoT devices that have a reputation for very bad security, BSG seem to have
done a decent job of designing their system, especially since
they allow a no-cloud local control configuration.  The protocols
seem sound, use well tested cryptographic libraries (TLS PSK with
modern ciphres) or well understood primitives (AES-CBC with HMAC),
and should prevent most any random attacker on your network from being able to
[take over your appliances to mine cryptocurrency](http://www.antipope.org/charlie/blog-static/2013/12/trust-me.html).

*WARNING: This tool not ready for prime time and is still beta!*

More see: [Python tool to talk to Home Connect appliances hcpy2-0/hcpy](https://github.com/hcpy2-0/hcpy)

## Setup

To avoid running into issues later with your default python installs, it's recommended to use a py virtual env for doing this. Go to your desired test directory, and:

```bash
⚡ user@linux: pyenv --version
⚡ user@linux: pyenv virtualenv 3.11.9 hcpytest
⚡ user@linux: pyenv local hcpytest
⚡ user@linux: pip install -r requirements.txt
```

### Installed packages

```log
Package            Version
------------------ --------
beautifulsoup4     4.12.3
bs4                0.0.2
certifi            2024.6.2
charset-normalizer 3.3.2
click              8.1.7
click-config-file  0.6.0
configobj          5.0.8
idna               3.7
lxml               5.2.2
paho-mqtt          1.6.1
pip                24.1.1
pycryptodome       3.20.0
requests           2.32.3
setuptools         65.5.0
six                1.16.0
soupsieve          2.5
sslpsk             1.0.0
urllib3            2.2.2
websocket-client   1.8.0
```


## Authenticate to the cloud servers

```bash
cd hcpy_org
python hc-login.py $USERNAME $PASSWORD > config/devices.json
cat config/devices.json
```

The `hc-login.py` script perfoms the OAuth process to login to your
Home Connect account with your usename and password.  It
receives a bearer token that can then be used to retrieves
a list of all the connected devices, their authentication
and encryption keys, and XML files that describe all of the
features and options.

This only needs to be done once or when you add new devices;
the resulting configuration JSON file *should* be sufficient to
connect to the devices on your local network, assuming that
your mDNS or DNS server resolves the names correctly.

### Results

```log
loginpage_url='https://api.home-connect.com/security/oauth/authorize?response_type=code&prompt=login&code_challenge=...'
next preauth_url='https://singlekey-id.com/auth/connect/authorize?client_id ...'
next preauth_url='https://singlekey-id.com/auth/login?ReturnUrl=%2Fauth%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id ...'
next preauth_url='https://singlekey-id.com/auth/login?ReturnUrl=%2Fauth%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id ...'
next preauth_url='https://singlekey-id.com/auth/en-gb/login?ReturnUrl=%2Fauth%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id ...'
return_url='/auth/connect/authorize/callback?client_id ...'
return_url='https://singlekey-id.com/auth/connect/authorize/callback?client_id... <Response [302]>'
return_url='https://api.home-connect.com/security/oauth/redirect_target?code=... <Response [302]>'
return_url='hcauth://auth/prod?code=...'
token_url='https://api.home-connect.com/security/oauth/token...'
Received access token='....'
fetching 'https://prod.reu.rest.homeconnectegw.com/api/...: ********.zip'
```
</br>

## Home Connect to MQTT `hc2mqtt.py`

This tool will establish websockets to the local devices and
transform their messages into MQTT JSON messages.  The exact
format is likely to change; it is currently a thin translation
layer over the XML retrieved from cloud servers during the
initial configuration.


- If the `hc-login.py` has worked and a `devices.json` is available, then adjust the config.ini file:<br/>
  Use the following ./config/config.ini example:
    ```
    devices_file = "./config/devices.json"
    mqtt_host = "localhost"
    mqtt_username = ""
    mqtt_password = ""
    mqtt_port = 1883
    mqtt_prefix = "homeconnect/"
    mqtt_ssl = False
    mqtt_cafile = None
    mqtt_certfile = None
    mqtt_keyfile = None
    mqtt_clientname="hcpy"
    ```
    <br/>

- After that, the application `hc2mqtt.py` can be started and if everything works, the MQTT Brocker messages will be sent
    ```bash
    cd hcpy_org
    python hc2mqtt.py --config config/config.ini
    ```
<br/>


## Notes
- Sometimes when the device is off, there is the error `ERROR [ip] [Errno 113] No route to host`
- There is a lot more information available, like the status of a program that is currently active. This needs to be integrated if possible. For now only the values that relate to the `config.json` are published

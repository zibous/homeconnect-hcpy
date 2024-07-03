#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Sourcecode from:
# url: https://github.com/hcpy2-0/hcpy
# maintainer: pmagyar, Meatballs1

# This directly follows the OAuth login flow that is opaquely described
# https://github.com/openid/AppAuth-Android
# A really nice walk through of how it works is:
# https://auth0.com/docs/get-started/authentication-and-authorization-flow/call-your-api-using-the-authorization-code-flow-with-pkce
import sys
import io
import json
import os
import re
from base64 import urlsafe_b64encode as base64url_encode
from urllib.parse import parse_qs, urlencode, urlparse
from zipfile import ZipFile

import requests
from bs4 import BeautifulSoup
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

## all for logging
from loguru import logger

from .HCxml2json import xml2json


class HomeconnecAccount:
    """## Homeconnect Account"""

    email: str = None
    password: str = None
    configdir: str = "./config"
    devicesfile: str = "./config/devices.json"
    ready: bool = False
    deviceconfigs: str = None

    def __init__(self, email: str = None, password: str = None, configdir="./config"):
        """## Connect to homeconnect Account
        ### Args:
        - `email (str)`: account email address
        - `password (str)`: single key passord
        - `configdir (str, optional)`: config directory, defaults to "./config".
        """
        self.email = email
        self.password = password
        self.configdir = configdir
        self.devicesfile = f"{self.configdir}/devices.json"
        self.ready = self.__checkDevicesData__()

    def __checkDevicesData__(self) -> bool:
        if os.path.isfile(self.devicesfile):
            if os.path.isfile(self.devicesfile):
                with open(self.devicesfile, "r", encoding="utf8") as f:
                    data = json.load(f)
                if data:
                    return True
        else:
            return getConfig(email=self.email, password=self.password, devices_file=self.devicesfile)

        return False



# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.

# http_client.HTTPConnection.debuglevel = 1


def getConfig(email: str, password: str, devices_file=None) -> bool:
    """## _summary_
    ### Args:
        - `email (str)`: account email address
        - `password (str)`: single key passord
        - `devices_file (str, optional)`: config devices file.

    ### Returns:
        - `bool`: True or False
    """
    try:

        if not email or not password:
            logger.critical("No account email or password found!")
            return False
        else:
            logger.debug(f"Try Login with user {email} and password {password}")

        if not devices_file:
            devices_file = os.path.dirname(os.path.abspath("./config/devices.json"))

        configdir = os.path.dirname(os.path.abspath(devices_file))

        headers = {"User-Agent": "hc-login/1.0"}

        session = requests.Session()
        session.headers.update(headers)

        base_url = "https://api.home-connect.com/security/oauth/"
        asset_urls = [
            "https://prod.reu.rest.homeconnectegw.com/",  # EU
            "https://prod.rna.rest.homeconnectegw.com/",  # US
        ]

        #
        # Start by fetching the old login page, which gives
        # us the verifier and challenge for getting the token,
        # even after the singlekey detour.
        #
        # The app_id and scope are hardcoded in the application
        app_id = "9B75AC9EC512F36C84256AC47D813E2C1DD0D6520DF774B020E1E6E2EB29B1F3"
        scope = [
            "ReadAccount",
            "Settings",
            "IdentifyAppliance",
            "Control",
            "DeleteAppliance",
            "WriteAppliance",
            "ReadOrigApi",
            "Monitor",
            "WriteOrigApi",
            "Images",
        ]
        scope = [
            "ReadOrigApi",
        ]

        def b64(b):
            return re.sub(r"=", "", base64url_encode(b).decode("UTF-8"))

        def b64random(num):
            return b64(base64url_encode(get_random_bytes(num)))

        verifier = b64(get_random_bytes(32))

        login_query = {
            "response_type": "code",
            "prompt": "login",
            "code_challenge": b64(SHA256.new(verifier.encode("UTF-8")).digest()),
            "code_challenge_method": "S256",
            "client_id": app_id,
            "scope": " ".join(scope),
            "nonce": b64random(16),
            "state": b64random(16),
            "redirect_uri": "hcauth://auth/prod",
            "redirect_target": "icore",
        }

        loginpage_url = base_url + "authorize?" + urlencode(login_query)
        token_url = base_url + "token"

        logger.debug(f"Login url: {loginpage_url}")
        r = session.get(loginpage_url)
        if r.status_code != requests.codes.ok:
            logger.critical(f"Error fetching login url {loginpage_url}, Response: {r.text}")
            logger.critical("Login ended!")
            exit()

        # get the session from the text
        if not (match := re.search(r'"sessionId" value="(.*?)"', r.text)):
            logger.critical(f"Unable to find session id in login page, Response {r.text}")
            logger.critical("Login ended!")
            exit(1)
        session_id = match[1]
        if not (match := re.search(r'"sessionData" value="(.*?)"', r.text)):
            logger.critical(f"Unable to find session data in login page, Response {r.text}")
            logger.critical("Login ended!")
            exit(1)
        session_data = match[1]

        # now that we have a session id, contact the
        # single key host to start the new login flow
        singlekey_host = "https://singlekey-id.com"
        login_url = singlekey_host + "/auth/en-us/log-in/"

        preauth_url = singlekey_host + "/auth/connect/authorize"
        preauth_query = {
            "client_id": "11F75C04-21C2-4DA9-A623-228B54E9A256",
            "redirect_uri": "https://api.home-connect.com/security/oauth/redirect_target",
            "response_type": "code",
            "scope": "openid email profile offline_access homeconnect.general",
            "prompt": "login",
            "style_id": "bsh_hc_01",
            "state": '{"session_id":"' + session_id + '"}',  # important: no spaces!
        }

        # fetch the preauth state to get the final callback url
        preauth_url += "?" + urlencode(preauth_query)

        # loop until we have the callback url
        while True:
            logger.debug(f"next {preauth_url}")
            r = session.get(preauth_url, allow_redirects=False)
            if r.status_code == 200:
                logger.info("Login valid")
                break
            if r.status_code > 300 and r.status_code < 400:
                preauth_url = r.headers["location"]
                # Make relative locations absolute
                if not bool(urlparse(preauth_url).netloc):
                    preauth_url = singlekey_host + preauth_url
                continue
            logger.critical(f"{preauth_url} failed to fetch {r} {r.text}")
            logger.critical("Login ended!")
            exit(1)

        # get the Return Url from the response
        query = parse_qs(urlparse(preauth_url).query)
        return_url = query["ReturnUrl"][0]
        logger.debug(f"return url: {return_url}")

        if "X-CSRF-FORM-TOKEN" in r.cookies:
            headers["RequestVerificationToken"] = r.cookies["X-CSRF-FORM-TOKEN"]
        session.headers.update(headers)

        soup = BeautifulSoup(r.text, "html.parser")
        requestVerificationToken = soup.find("input", {"name": "__RequestVerificationToken"}).get("value")

        # set the username for thr request
        r = session.post(
            preauth_url,
            data={
                "UserIdentifierInput.EmailInput.StringValue": email,
                "__RequestVerificationToken": requestVerificationToken,
            },
            allow_redirects=False,
        )

        password_url = r.headers["location"]

        if not bool(urlparse(password_url).netloc):
            password_url = singlekey_host + password_url

        r = session.get(password_url, allow_redirects=False)
        soup = BeautifulSoup(r.text, "html.parser")
        requestVerificationToken = soup.find("input", {"name": "__RequestVerificationToken"}).get("value")

        # set the password for thr request
        r = session.post(
            password_url,
            data={
                "Password": password,
                "RememberMe": "false",
                "__RequestVerificationToken": requestVerificationToken,
            },
            allow_redirects=False,
        )

        while True:
            if return_url.startswith("/"):
                return_url = singlekey_host + return_url
            r = session.get(return_url, allow_redirects=False)
            logger.debug(f"{return_url}, {r} {r.text}")
            if r.status_code != 302:
                break
            return_url = r.headers["location"]
            if return_url.startswith("hcauth://"):
                break

        logger.debug(f" return url: {return_url}")

        url = urlparse(return_url)
        query = parse_qs(url.query)

        if query.get("ReturnUrl") is not None:
            logger.critical("Wrong credentials.")
            logger.info("If you forgot your login/password, you can restore them by opening " "https://singlekey-id.com/auth/en-us/login in browser")
            logger.critical("Login ended!")
            exit(1)

        code = query.get("code")[0]
        state = query.get("state")[0]
        grant_type = query.get("grant_type")[0]  # "authorization_code"

        logger.debug(f"{code} {grant_type} {state}")

        auth_url = base_url + "login"
        token_url = base_url + "token"

        token_fields = {
            "grant_type": grant_type,
            "client_id": app_id,
            "code_verifier": verifier,
            "code": code,
            "redirect_uri": login_query["redirect_uri"],
        }

        logger.debug(f"Token url: {token_url}, Tocken Fields: {token_fields}")

        r = requests.post(token_url, data=token_fields, allow_redirects=False)
        if r.status_code != requests.codes.ok:
            logger.critical("Bad code?")
            logger.debug(f"Headers: {r.headers}")
            logger.debug(f"Response: {r.text}")
            logger.critical("Login ended!")
            exit(1)

        logger.success("got token page")
        token = json.loads(r.text)["access_token"]
        logger.debug(f"Received access {token}")
        headers = {
            "Authorization": "Bearer " + token,
        }

        logger.info("Try to request account details from all geos. Whichever works, we'll use next.")
        for asset_url in asset_urls:
            r = requests.get(asset_url + "account/details", headers=headers)
            if r.status_code == requests.codes.ok:
                break

        # now we can fetch the rest of the account info
        if r.status_code != requests.codes.ok:
            logger.critical("unable to fetch account details")
            logger.debug(f"Headers: {r.headers}")
            logger.debug(f"Response: {r.text}")
            logger.critical("Login ended!")
            exit(1)

        account = json.loads(r.text)
        logger.debug(f"Account: {account}")

        if account:
            _accountFile = f"{configdir}/account.json"
            os.makedirs(os.path.dirname(_accountFile), exist_ok=True)
            with open(_accountFile, 'w', encoding='utf8') as f:
                f.write(json.dumps(obj=account, indent=4, ensure_ascii=True))
        else:
            logger.critical("No Valid account data found !")
            return False

        configs = []
        for app in account["data"]["homeAppliances"]:

            app_brand = app["brand"]
            app_type = app["type"]
            app_id = app["identifier"]
            config = {
                "name": app_type.lower(),
            }

            configs.append(config)

            if "tls" in app:
                # fancy machine with TLS support
                config["host"] = app_brand + "-" + app_type + "-" + app_id
                config["key"] = app["tls"]["key"]
            else:
                # less fancy machine with HTTP support
                config["host"] = app_id
                config["key"] = app["aes"]["key"]
                config["iv"] = app["aes"]["iv"]

            # Fetch the XML zip file for this device
            app_url = asset_url + "api/iddf/v1/iddf/" + app_id
            logger.info(f"fetching:  {app_url}")
            r = requests.get(app_url, headers=headers)
            if r.status_code != requests.codes.ok:
                logger.error(f"APP Id: {app_id}, unable to fetch machine description?")
                next

            logger.info("we now have a zip file with XML, let's unpack them")
            content = r.content
            logger.info(f"{app_url}: {app_id}.zip")
            with open(f"{configdir}/{app_id}.zip", "wb") as f:
                f.write(content)
            logger.success(f"Data zip file {configdir}/{app_id}-zip saved")

            z = ZipFile(io.BytesIO(content))
            features = z.open(app_id + "_FeatureMapping.xml").read()
            description = z.open(app_id + "_DeviceDescription.xml").read()

            machine = xml2json(features, description)
            config["description"] = machine["description"]
            config["features"] = machine["features"]

        if configs and devices_file:
            os.makedirs(os.path.dirname(devices_file), exist_ok=True)
            with open(devices_file, 'w', encoding='utf8') as f:
                f.write(json.dumps(obj=configs, indent=4, ensure_ascii=True))
            return True
        else:
            logger.critical("No valid decices data found !")

    except BaseException as e:
        logger.critical(f"FATAL ERROR  {str(e)}, line {sys.exc_info()[-1].tb_lineno}")
        return False

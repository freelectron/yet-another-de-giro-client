"""
Initialize custom De Giro client.
Uses a combination of packages:
 - Uses selenium (https://selenium-python.readthedocs.io/)
 - Uses request (https://docs.python-requests.org/en/master/index.html)
 - Uses pandas
Selenium is mainly used to login to DeGiro and receive appropriate cookies.
"""

from typing import Dict, Optional, Mapping
from time import sleep

import pendulum
import yaml
from pendulum import Date
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import pandas as pd

from de_giro_client.client import DE_GIRO_WEB_TRADER_DOMAIN_URL

# FIXME: find better way to specify config path
with open("./de_giro_client/configs/selenium_config.yaml") as f:
    SELENIUM_CONFIG = yaml.load(f, Loader=yaml.Loader)

# FIXME: find better way to specify config path
with open("./de_giro_client/configs/requests_config.yaml") as f:
    REQUESTS_CONFIG = yaml.load(f, Loader=yaml.Loader)


class DeGiroSession:
    domain_url: str = DE_GIRO_WEB_TRADER_DOMAIN_URL
    login_url: str = f"{domain_url}/login"

    def __init__(
        self,
        de_giro_account_id: str,
        browser_name: str = SELENIUM_CONFIG["browser"]["name"],
        webdriver_filepath: str = SELENIUM_CONFIG["browser"]["driver"]["path"],
        requests_headers: Optional[Dict] = REQUESTS_CONFIG.get("headers", None),
        session_id: Optional[str] = None,
    ):
        """
        Create a browser session by:
         - Create a new instance of a browser-driver (e.g., GeckoDriver) remote service proxy.
           - a browser-driver provides a HTTP interface speaking the W3C WebDriver
         - instantiating a selenium session that will be used to login to De Giro
         - specifying a path to browser web drives to use
         - creating a requests session

        Optionally:
         - headers to use for the requests session
         - specify a degGiro web trader session id if already available
        """
        self.account_id = de_giro_account_id
        self.web_service = Service(webdriver_filepath)
        self.browser_session = getattr(webdriver, browser_name)(
            service=self.web_service
        )
        self.requests_session = requests.session()
        self.requests_session.headers.update(
            requests_headers
        ) if requests_headers else None
        self.session_id = session_id

    def connect(self, username: str, password: str):
        """
        Login to deGiro web trader app.
        TODO: introduce logging in with the requests library
        """
        self.browser_session.get(self.login_url)
        sleep(0.5)
        self.browser_session.find_element(by=By.ID, value="username").send_keys(
            username
        )
        self.browser_session.find_element(by=By.ID, value="password").send_keys(
            password
        )
        self.browser_session.find_element(
            by=By.NAME, value="loginButtonUniversal"
        ).click()

        for cookie in self.browser_session.get_cookies():
            c = {cookie["name"]: cookie["value"]}
            self.requests_session.cookies.update(c)

        self.session_id = [
            cookie["value"]
            for cookie in self.browser_session.get_cookies()
            if cookie.get("name") == "JSESSIONID"
        ].pop()

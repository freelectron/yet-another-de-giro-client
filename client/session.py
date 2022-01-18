"""
Initialize custom De Giro client.
Uses a combination of packages:
 - Uses selenium (https://selenium-python.readthedocs.io/)
 - Uses request (https://docs.python-requests.org/en/master/index.html)
 - Uses pandas
Selenium is mainly used to login to DeGiro and receive appropriate cookies.
Request is for performing specific actions e.g., historical data download, portfolio information.
Uses pandas to output tabular/time-series data from DeGiro.

TODO: Create translator
TODO: Create pandera schemas
"""

from io import StringIO
from typing import Dict, Optional
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
    portfolio_url: str = f"{domain_url}/reporting/secure/v3/positionReport"
    date_string_format: str = "%d/%m/%Y"
    country: str = "NL"
    language: str = "nl"

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

    def _get_portfolio_performance_results_daily(self, date: Date) -> pd.DataFrame:
        """
        Get portfolio returns in % and monetary units for a single day.
        """
        date_str = date.strftime(self.date_string_format)
        query_url = (
            f"{self.portfolio_url}/csv?"
            f"intAccount={self.account_id}"
            f"&sessionId={self.session_id}"
            f"&country={self.country}"
            f"&lang={self.language}"
            f"&toDate={date_str}"
        )
        response = self.requests_session.get(query_url)
        df = pd.read_csv(StringIO(str(response.content.decode("utf-8"))), decimal=",")
        df.index = pd.to_datetime([date.to_date_string()] * len(df))

        # Manually parse a column that has string & float in it
        df["Lokale valuta"] = df["Lokale waarde"].apply(lambda x: x.split()[0])
        df["Lokale waarde"] = (
            df["Lokale waarde"].apply(lambda x: x.split()[1]).astype(float)
        )

        return df

    def get_portfolio_performance_results(
        self, period: pendulum.Period
    ) -> pd.DataFrame:
        """
        Fetch portfolio results information for a period and assemble it in one table.
        """
        df_results = pd.DataFrame()
        for date in period.range("days"):
            df_results = df_results.append(
                self._get_portfolio_performance_results_daily(date)
            )

        return df_results

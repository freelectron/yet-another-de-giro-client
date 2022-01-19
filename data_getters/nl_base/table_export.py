from abc import ABC
from typing import Mapping, Union, List

import pandas as pd
from pandera import DataFrameSchema
from pendulum import Period

from client import DE_GIRO_WEB_TRADER_DOMAIN_URL
from client.session import DeGiroSession
from translators import CASH_FUNDS_PRODUCT_NAME, PRODUCT_NAME_COLUMN_NAME
from translators.nl_to_en.translator import DAILY_PORTFOLIO_RESULTS_DUTCH_TO_ENGLISH_COLUMNS


class DeGiroDataGetterNL(ABC):
    """
    A nl_base class to load data from DeGiro's web trader.
    Describes the flow of retrieving tabular data from the online.

    Main functions:
        1. Load raw data: e.g., bu querying an endpoint
        2. Preprocess/Clean: convert to data frame, specify data types
        3. Translate from Dutch to English
        4. Validate data schema
    """
    encoding: str = "utf-8"
    domain_url: str = DE_GIRO_WEB_TRADER_DOMAIN_URL
    country: str = "NL"
    language: str = "nl"
    timezone: str = "Europe/Amsterdam"
    date_string_format: str = "%d/%m/%Y"
    translator_mapping: Mapping[str, str] = DAILY_PORTFOLIO_RESULTS_DUTCH_TO_ENGLISH_COLUMNS
    query_url: Union[str, None] = None
    data_schema: DataFrameSchema = None

    @classmethod
    def translate(cls, df):
        """
        Translate names of the columns in the dataframe from Dutch to English.
        """
        return df.rename(columns=cls.translator_mapping)

    @classmethod
    def validata(cls, df: pd.DataFrame) -> pd.DataFrame:
        if not cls.data_schema:
            raise ValueError("Validate the resulting dataframe table against a data schema."
                              "Data schema is not specified")
        else:
            cls.data_schema.validate(df)

    @staticmethod
    def clean(df: pd.DataFrame) -> DataFrameSchema:
        return df[df[PRODUCT_NAME_COLUMN_NAME] != CASH_FUNDS_PRODUCT_NAME]

    def __init__(self, session: DeGiroSession):
        self.session = session

    def load_raw_data(self, period: Period) -> Union[str, list]:
        raise NotImplementedError("Load a raw stream of bytes. Decode to python understandable format.")

    def preprocess(self, raw_data: Union[str, List]) -> pd.DataFrame:
        raise NotImplementedError("Functions such as set formats & deduplicate.")

    def get_dataframe(self, period: Period):
        """
        Execute the  flow for getting tabular formatted data.
        """
        raw_data = self.load_raw_data(period=period)
        df = self.preprocess(raw_data)
        df = self.translate(df=df)
        # Do not display 'CASH & CASH FUND & FTX CASH (EUR)' aka not invested funds
        df = self.clean(df=df)
        self.validata(df=df)

        return df

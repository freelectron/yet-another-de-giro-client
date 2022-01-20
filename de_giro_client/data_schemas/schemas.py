"""
Contains pandera dataframe schemas.
To be used for checking correctness of input and outputs for dataframe manipulations.
"""
import pandas as pd
from pandera import DataFrameSchema, Column, Index

from ..translators import PRODUCT_NAME_COLUMN_NAME, ISIN_COLUMN_NAME, QUANTITY_COLUMN_NAME, CLOSING_PRICE_COLUMN_NAME, \
    LOCAL_CURRENCY_VALUE_COLUMN_NAME, LOCAL_CURRENCY_NAME_COLUMN_NAME, EURO_VALUE_COLUMN_NAME

PORTFOLIO_RESULTS_SCHEMA_NL = DataFrameSchema(
    index=Index(
        pd.DatetimeTZDtype(tz='Europe/Amsterdam')
    ),
    columns={
        PRODUCT_NAME_COLUMN_NAME: Column(str),
        ISIN_COLUMN_NAME: Column(str),
        QUANTITY_COLUMN_NAME: Column(float),
        CLOSING_PRICE_COLUMN_NAME: Column(float),
        LOCAL_CURRENCY_VALUE_COLUMN_NAME: Column(float),
        LOCAL_CURRENCY_NAME_COLUMN_NAME: Column(str),
        EURO_VALUE_COLUMN_NAME: Column(float),
    }
)

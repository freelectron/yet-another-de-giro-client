import io
from io import StringIO
from typing import Dict

import pandas as pd
from pendulum import Period, Date

from ..client.session import DeGiroSession
from ..data_getters.base_classes.table_export import DeGiroDataGetterNL
from ..data_schemas.schemas import PORTFOLIO_RESULTS_SCHEMA_NL


class DailyPortfolioResults(DeGiroDataGetterNL):
    portfolio_url: str = f"{DeGiroDataGetterNL.domain_url}/reporting/secure/v3/positionReport"
    raw_data_format = "csv"
    index_name: str = "closing_date"
    data_schema = PORTFOLIO_RESULTS_SCHEMA_NL

    def __init__(self, session: DeGiroSession):
        super().__init__(session=session)

    def construct_query_url(self, date_string):
        return (
            f"{self.portfolio_url}/{self.raw_data_format}?"
            f"intAccount={self.session.account_id}"
            f"&sessionId={self.session.session_id}"
            f"&country={self.country}"
            f"&lang={self.language}"
            f"&toDate={date_string}"
        )

    def _fetch_single_day_raw_stats(self, date: Date):
        date_str = date.strftime(self.date_string_format)
        query_url = self.construct_query_url(date_string=date_str)
        response = self.session.requests_session.get(query_url)

        return StringIO(str(response.content.decode(self.encoding)))

    def load_raw_data(self, period: Period) -> Dict:
        return {
            date: self._fetch_single_day_raw_stats(date)
            for date in period.range("days")
        }

    def preprocess(self, raw_data: Dict[Date, io.StringIO]) -> pd.DataFrame:
        df_period = pd.DataFrame()

        for date, raw_data_file_handle in raw_data.items():
            df_date = pd.read_csv(raw_data_file_handle, decimal=",")
            df_date.index = pd.to_datetime([date.to_date_string()] * len(df_date)).tz_localize(self.timezone)
            df_date.index.name = self.index_name

            # Manually parse a column that has string & float in it
            df_date["Lokale valuta"] = df_date["Lokale waarde"].apply(lambda x: x.split()[0])
            df_date["Lokale waarde"] = (
                df_date["Lokale waarde"].apply(lambda x: x.split()[1]).astype(float)
            )
            df_period = df_period.append(df_date)

        return df_period

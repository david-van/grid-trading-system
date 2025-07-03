import requests
from efinance.utils import search_quote
from datetime import datetime
import pandas as pd
from efinance.utils import to_numeric


@to_numeric
def get_quote_history_1_minute(stock_code: str,
                               date: str) -> pd.DataFrame:

    """
    获取股票、债券的指定日期的 1 分钟 K 线数据

    Parameters
    ----------
    stock_code : str
        股票代码 或者股票代码列表
    date : str
        日期

    Returns
    -------
    DataFrame

    Examples
    --------
    >>> stock_code = '600519'
    >>> date = '20220304'
    >>> get_quote_history_1_minute(stock_code,date)
            股票名称    股票代码          日期     时间      最新价        均价   成交量    昨收    开盘
        0    贵州茅台  600519  2022-03-04  09:30   1772.0    1772.0   571  1800  1772
        1    贵州茅台  600519  2022-03-04  09:31   1770.0  1770.818  1039  1800  1772
        2    贵州茅台  600519  2022-03-04  09:32  1773.53  1770.957   453  1800  1772
        3    贵州茅台  600519  2022-03-04  09:33  1779.98  1772.293   496  1800  1772
        4    贵州茅台  600519  2022-03-04  09:34   1773.0   1773.12   505  1800  1772
        ..    ...     ...         ...    ...      ...       ...   ...   ...   ...
        236  贵州茅台  600519  2022-03-04  14:56  1779.23  1774.363   154  1800  1772
        237  贵州茅台  600519  2022-03-04  14:57  1781.61  1774.401   181  1800  1772
        238  贵州茅台  600519  2022-03-04  14:58  1781.88  1774.401     2  1800  1772
        239  贵州茅台  600519  2022-03-04  14:59  1781.88  1774.401     0  1800  1772
        240  贵州茅台  600519  2022-03-04  15:00   1780.5  1774.456   276  1800  1772
        [241 rows x 9 columns]
    """
    q = search_quote(stock_code)
    df = pd.DataFrame(columns=['股票名称', '股票代码', '日期', '时间',
                               '最新价', '均价', '成交量', '昨收', '开盘'])
    if not q:
        return df
    data = {
        'Day': date,
        'PhoneOSNew': '2',
        'StockID': q.code,
        'Token': '0',
        'UserID': '0',
        'VerSion': '5.2.1.0',
        'a': 'GetStockTrend',
        'apiv': 'w28',
        'c': 'StockL2History'
    }
    url = 'https://apphis.longhuvip.com/w1/api/index.php'
    response = requests.post(url, data=data)

    try:
        js = response.json()
    except:
        return df
    if not js.get('trend'):
        return df
    trend = pd.DataFrame(js['trend'])
    df[['时间', '最新价', '均价', '成交量']] = trend.values[:, :4]
    df['日期'] = datetime.strptime(
        js['day'], '%Y%m%d').strftime('%Y-%m-%d')
    df['昨收'] = js['preclose_px']
    df['开盘'] = js['begin_px']
    df['股票代码'] = q.code
    df['股票名称'] = q.name
    return df
df = get_quote_history_1_minute('600519', '20220304')

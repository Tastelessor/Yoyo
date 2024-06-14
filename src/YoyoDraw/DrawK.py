from matplotlib.axes import Axes
from matplotlib.figure import Figure
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from YoyoData import Data
from Draw import Draw

class DrawK(Draw):
    def __init__(self):
        pass

    def scatter_points(self, ohlcv: pd.DataFrame, points: list, ax: Axes, point_color='blue') -> None:
        """scatter points onto the k-line plot

        Args:
            points (list): the scatter points
            ax (Axes): subplot of a figure
        """
        for transc_info in points:
            if transc_info['date'] in ohlcv.index:
                try:
                    transc_info['date'] = pd.to_datetime(transc_info['date'])
                    ax.scatter(transc_info['date'], transc_info['price'], color=point_color, marker='o', zorder=5, s=50)
                except Exception as e:
                    raise(f"ERROR: {e}")

    def draw_k_line(self, stock_code: str, buy_records: list = [], sell_records: list = []):
        """plot k-line chart, use plt.show to make it visible :D

        Args:
            stock_code (str): stock code like: HK.09866
            buy_records (list, optional): [{'date': '2022-01-01', 'price': 100}, {...}]. Defaults to []
            sell_records (list, optional): [{'date': '2022-01-01', 'price': 100}, {...}]. Defaults to [].
        """
        ohlcv = pd.read_csv(Data.get_filename_by_code(stock_code), parse_dates=True)
        ohlcv = Data.rename_futu_table_head(ohlcv)
        kwargs = {
            'type': 'candle',
            'volume': True,
            'show_nontrading': True,
            'style': 'charles',
            'title': 'K-Line',
            'ylabel_lower': 'Deal',
            'ylabel': 'Price',
            'returnfig': True
        }

        fig, ax = mpf.plot(ohlcv, **kwargs)
        for line in ax[0].get_lines():
            line.set_linewidth(10)
        ax[0].set_xlim(ohlcv.index.min(), ohlcv.index.max())
        ax[0].set_ylim(ohlcv['Low'].min(), ohlcv['High'].max())
        ax[0].yaxis.labelpad=30
        ax[0].yaxis.set_label_position("left")
        self.scatter_points(ohlcv, buy_records, ax[0], point_color='red')
        self.scatter_points(ohlcv, sell_records, ax[0], point_color='green')
        return fig

    def draw_asset_line(self, fig: Figure, asset_records: list[dict]) -> None:
        asset_records = pd.DataFrame(asset_records)
        asset_records['date'] = asset_records['date'].apply(lambda x: x.split(' ')[0])
        asset_records['date'] = pd.to_datetime(asset_records['date'])
        ax = fig.get_axes()[0].twinx()
        ax.yaxis.set_label_position("right")
        ax.plot(asset_records['date'], asset_records['asset'], 'r', linewidth=1)
        ax.set_title('Total Asset in HKD')
        ax.set_ylabel('Asset(w)')
        ax.yaxis.labelpad = 30

    def show_plot(self):
        # plt.tight_layout()
        # plt.savefig('hbuy5_lsell0.svg', format='svg')
        plt.show()
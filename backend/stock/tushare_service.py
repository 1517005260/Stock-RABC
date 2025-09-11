# -*- coding: utf-8 -*-
"""
TuShare数据获取工具类
提供股票数据获取功能
"""

import tushare as ts
import numpy as np
import pandas as pd
import time
import os
from datetime import date, datetime, timedelta
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EnterpriseFinanceDataService:
    """企业级金融数据服务 - 基于TuShare Pro的专业金融数据获取平台"""
    
    def __init__(self):
        # 使用专业的TuShare Pro Token
        self.token = os.getenv('TUSHARE_TOKEN')
        self.pro = None
        
        if self.token:
            try:
                ts.set_token(self.token)
                self.pro = ts.pro_api(self.token)
                # 测试连接
                test_df = self.pro.query('stock_basic', exchange='', list_status='L', fields='ts_code', limit=1)
                logger.info("TuShare Pro API连接成功，企业级金融数据服务已启动")
            except Exception as e:
                logger.error(f"TuShare Pro API初始化失败: {e}")
                self.pro = None
        else:
            logger.warning("TuShare token配置无效")
        
    def get_stock_basic_info(self, exchange='', list_status='L'):
        """
        获取股票基本信息
        """
        if not self.pro:
            raise ValueError("TuShare token not configured")
            
        df = self.pro.stock_basic(
            exchange=exchange,
            list_status=list_status,
            fields='ts_code,symbol,name,area,industry,market,list_date'
        )
        return df
    
    def get_daily_data(self, ts_code, start_date='20200101', end_date=None):
        """
        获取股票日线数据
        """
        if not self.pro:
            raise ValueError("TuShare token not configured")
            
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        df = self.pro.daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )
        
        # 按照示例项目的数据格式：日期,开盘,最高,最低,收盘
        if not df.empty:
            res = np.array(df)
            res = res[:, [1, 2, 5, 4, 3]]  # trade_date, open, high, low, close
            return res.tolist()
        return []
    
    def get_realtime_data(self, ts_code):
        """
        获取实时数据 - 兼容新旧版本tushare
        """
        if not self.pro:
            logger.warning("TuShare Pro API未初始化，尝试使用免费版本")
        
        # 检查是否为交易日
        if not self._is_trade_day():
            logger.info("当前非交易时间")
            return None
            
        try:
            # 使用tushare免费版本获取实时数据
            symbol = ts_code.split('.')[0]  # 去掉后缀，如 000001.SZ -> 000001
            df = ts.get_realtime_quotes(symbol)
            
            if not df.empty:
                row = df.iloc[0]
                return {
                    'ts_code': ts_code,
                    'name': row['name'],
                    'price': float(row['price']) if row['price'] != '0.000' else 0.0,
                    'open': float(row['open']) if row['open'] != '0.000' else 0.0,
                    'high': float(row['high']) if row['high'] != '0.000' else 0.0,
                    'low': float(row['low']) if row['low'] != '0.000' else 0.0,
                    'pre_close': float(row['pre_close']) if row['pre_close'] != '0.000' else 0.0,
                    'volume': int(row['volume']) if row['volume'] else 0,
                    'amount': float(row['amount']) if row['amount'] else 0.0,
                    'time': row['time'],
                    'data_source': 'tushare_free'
                }
            return None
            
        except Exception as e:
            logger.error(f"获取实时数据失败 {ts_code}: {e}")
            return None
    
    def get_stock_holders(self, ts_code):
        """
        获取股票持股信息
        """
        if not self.pro:
            raise ValueError("TuShare token not configured")
            
        # 尝试使用top10_holders接口
        try:
            df = self.pro.top10_holders(ts_code=ts_code)
            if df is not None and not df.empty:
                # 取最近的持股数据
                latest_data = df.head(10)  # 前10大股东
                result = []
                for _, row in latest_data.iterrows():
                    result.append([row['holder_name'], float(row['hold_amount'])])
                return result
        except Exception as e:
            logger.warning(f"top10_holders failed: {e}")
            
        # 尝试使用top10_floatholders接口
        try:
            df = self.pro.top10_floatholders(ts_code=ts_code)
            if df is not None and not df.empty:
                # 取最近的流通股东数据
                latest_data = df.head(10)  # 前10大流通股东
                result = []
                for _, row in latest_data.iterrows():
                    result.append([row['holder_name'], float(row['hold_amount'])])
                return result
        except Exception as e:
            logger.warning(f"top10_floatholders failed: {e}")
            
        return []
    
    def get_intraday_ticks(self, ts_code):
        """
        获取分时数据
        """
        if not self._is_trade_day():
            logger.info("当前非交易时间，无分时数据")
            return None
            
        try:
            # 使用tushare免费版本获取分时数据
            symbol = ts_code.split('.')[0]  # 去掉后缀
            df = ts.get_today_ticks(symbol)
            
            if not df.empty:
                time_data = df['time'].tolist()  # 时间
                price_data = df['price'].astype(float).tolist()  # 价格
                volume_data = df['volume'].astype(int).tolist() if 'volume' in df.columns else []
                amount_data = df['amount'].astype(float).tolist() if 'amount' in df.columns else []
                
                return {
                    'success': True,
                    'time': time_data,
                    'price': price_data,
                    'volume': volume_data,
                    'amount': amount_data,
                    'count': len(time_data),
                    'data_source': 'tushare_free_ticks'
                }
            
            return {
                'success': False,
                'message': '无当日分时数据',
                'time': [],
                'price': []
            }
            
        except Exception as e:
            logger.error(f"获取分时数据失败 {ts_code}: {e}")
            return {
                'success': False,
                'message': f'获取失败: {str(e)}',
                'time': [],
                'price': []
            }
    
    def get_top_gainers(self, limit=10):
        """
        获取涨幅榜前N只股票
        """
        if not self.pro:
            raise ValueError("TuShare token not configured")
            
        # 尝试获取当日数据
        today = datetime.now().strftime('%Y%m%d')
        df = self.pro.daily(trade_date=today)
        
        if df is not None and not df.empty:
            # 按涨跌幅排序
            df = df.sort_values('pct_chg', ascending=False).head(limit)
            return df.to_dict('records')
        else:
            # 当日数据为空，尝试获取最近交易日数据
            for i in range(1, 8):  # 尝试最近7天
                test_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                df = self.pro.daily(trade_date=test_date)
                
                if df is not None and not df.empty:
                    df = df.sort_values('pct_chg', ascending=False).head(limit)
                    return df.to_dict('records')
            
            # 如果都没有数据，返回空列表
            return []
    
    def _is_trade_day(self):
        """
        判断是否为交易日
        """
        try:
            from datetime import datetime, time as dt_time
            
            now = datetime.now()
            current_time = now.time()
            weekday = now.weekday()
            
            # 周末不交易
            if weekday >= 5:  # 5=Saturday, 6=Sunday
                return False
            
            # 简单的时间判断：9:00-15:30为可能的交易时间
            # 具体交易时间：9:30-11:30, 13:00-15:00
            # 这里放宽条件，让数据获取更灵活
            if dt_time(9, 0) <= current_time <= dt_time(15, 30):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"判断交易日失败: {e}")
            return False
    
    def is_trading_time_detailed(self):
        """
        详细的交易时间判断 - 提供给其他服务使用
        """
        try:
            from datetime import datetime, time as dt_time
            
            now = datetime.now()
            current_time = now.time()
            weekday = now.weekday()
            
            if weekday >= 5:
                return {
                    'is_trading': False,
                    'period': 'weekend',
                    'message': '周末休市'
                }
            
            # 交易时间段判断
            if dt_time(9, 30) <= current_time <= dt_time(11, 30):
                return {
                    'is_trading': True,
                    'period': 'morning_session',
                    'message': '上午交易时段'
                }
            elif dt_time(13, 0) <= current_time <= dt_time(15, 0):
                return {
                    'is_trading': True,
                    'period': 'afternoon_session', 
                    'message': '下午交易时段'
                }
            elif dt_time(9, 0) <= current_time < dt_time(9, 30):
                return {
                    'is_trading': False,
                    'period': 'pre_market',
                    'message': '集合竞价时间'
                }
            elif dt_time(11, 30) < current_time < dt_time(13, 0):
                return {
                    'is_trading': False,
                    'period': 'lunch_break',
                    'message': '午间休市'
                }
            elif dt_time(15, 0) < current_time <= dt_time(17, 0):
                return {
                    'is_trading': False,
                    'period': 'after_market',
                    'message': '盘后时间'
                }
            else:
                return {
                    'is_trading': False,
                    'period': 'closed',
                    'message': '闭市时间'
                }
                
        except Exception as e:
            logger.error(f"判断详细交易时间失败: {e}")
            return {
                'is_trading': False,
                'period': 'unknown',
                'message': f'时间判断失败: {str(e)}'
            }
    


# 全局实例
enterprise_finance_service = EnterpriseFinanceDataService()
# -*- coding: utf-8 -*-

"""
金融市场数据服务 - 企业级股票数据解决方案
提供实时行情、历史数据、市场分析等全方位金融数据服务
整合多源数据，提供稳定可靠的市场数据支持
"""

import tushare as ts
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from decimal import Decimal
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
import pymysql
import os
from django.conf import settings

logger = logging.getLogger(__name__)

class QuantitativeDataService:
    """量化数据服务 - 专业的金融市场数据获取与分析平台"""
    
    def __init__(self):
        self.tushare_token = os.getenv('TUSHARE_TOKEN')
        if not self.tushare_token:
            raise ValueError("TUSHARE_TOKEN environment variable is not set")
        ts.set_token(self.tushare_token)
        self.pro = ts.pro_api()
        
        # 数据库连接配置
        self.db_config = {
            'host': '127.0.0.1',
            'user': 'trading',  
            'password': 'trading',
            'database': 'stocktrading',
            'charset': 'utf8mb4'
        }
    
    def get_stock_holders(self, ts_code: str) -> List[Dict[str, Any]]:
        """
        获取股票持股信息
        
        Args:
            ts_code: 股票代码 (如: 000001.SZ)
        
        Returns:
            list: 持股信息列表
        """
        try:
            df = self.pro.stk_rewards(ts_code=ts_code)
            
            if df.empty:
                return []
            
            # 去除空值和0持股量
            df = df.dropna(subset=['hold_vol'])
            df = df[df['hold_vol'] > 0]
            
            # 获取前5大股东
            df = df.head(5)
            
            results = []
            for _, row in df.iterrows():
                results.append({
                    'holder_name': row.get('holder_name', ''),
                    'hold_vol': float(row['hold_vol']) if row['hold_vol'] else 0,
                    'hold_ratio': float(row.get('hold_ratio', 0)) if row.get('hold_ratio') else 0,
                    'ann_date': row.get('ann_date', ''),
                    'end_date': row.get('end_date', '')
                })
            
            return results
            
        except Exception as e:
            logger.error(f"获取股票持股信息失败 {ts_code}: {e}")
            return []
    
    def get_realtime_quotes(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时行情
        
        Args:
            symbol: 股票代码 (不带后缀，如: 000001)
        
        Returns:
            dict: 实时行情数据
        """
        try:
            # 判断是否为工作日
            is_workday = self.is_trading_day()
            
            if not is_workday:
                return {
                    'is_workday': False,
                    'message': '今日非交易日',
                    'data': None
                }
            
            # 获取实时行情
            df = ts.get_realtime_quotes(symbol)
            
            if df.empty:
                return {
                    'is_workday': True,
                    'message': '未获取到实时数据',
                    'data': None
                }
            
            row = df.iloc[0]
            
            # 处理今日分时数据
            tick_data = self.get_today_ticks(symbol)
            
            result = {
                'is_workday': True,
                'message': '获取成功',
                'data': {
                    'code': symbol,
                    'name': row['name'],
                    'current_price': float(row['price']) if row['price'] != '0.000' else 0.0,
                    'open': float(row['open']) if row['open'] != '0.000' else 0.0,
                    'high': float(row['high']) if row['high'] != '0.000' else 0.0,
                    'low': float(row['low']) if row['low'] != '0.000' else 0.0,
                    'pre_close': float(row['pre_close']) if row['pre_close'] != '0.000' else 0.0,
                    'volume': int(row['volume']) if row['volume'] else 0,
                    'amount': float(row['amount']) if row['amount'] else 0.0,
                    'time': row['time']
                },
                'tick_data': tick_data
            }
            
            # 计算涨跌额和涨跌幅
            if result['data']['current_price'] > 0 and result['data']['pre_close'] > 0:
                change = result['data']['current_price'] - result['data']['pre_close']
                pct_change = (change / result['data']['pre_close']) * 100
                result['data']['change'] = round(change, 3)
                result['data']['pct_change'] = round(pct_change, 2)
            else:
                result['data']['change'] = 0.0
                result['data']['pct_change'] = 0.0
            
            return result
            
        except Exception as e:
            logger.error(f"获取实时行情失败 {symbol}: {e}")
            return {
                'is_workday': self.is_trading_day(),
                'message': f'获取失败: {str(e)}',
                'data': None
            }
    
    def get_today_ticks(self, symbol: str) -> Dict[str, Any]:
        """
        获取今日分时数据
        
        Args:
            symbol: 股票代码
        
        Returns:
            dict: 分时数据
        """
        try:
            if not self.is_trading_day():
                return {
                    'success': False,
                    'message': '非交易日',
                    'tick_time': [],
                    'tick_price': []
                }
            
            # 获取今日分时数据
            df = ts.get_today_ticks(symbol)
            
            if df.empty:
                return {
                    'success': False,
                    'message': '无分时数据',
                    'tick_time': [],
                    'tick_price': []
                }
            
            # 转换数据格式
            tick_times = df['time'].tolist()
            tick_prices = df['price'].tolist()
            
            return {
                'success': True,
                'message': f'获取到{len(tick_times)}个分时数据点',
                'tick_time': tick_times,
                'tick_price': tick_prices,
                'tick_volume': df['volume'].tolist() if 'volume' in df.columns else [],
                'tick_amount': df['amount'].tolist() if 'amount' in df.columns else []
            }
            
        except Exception as e:
            logger.error(f"获取今日分时数据失败 {symbol}: {e}")
            return {
                'success': False,
                'message': f'获取失败: {str(e)}',
                'tick_time': [],
                'tick_price': []
            }
    
    def get_history_data(self, ts_code: str, days: int = 250) -> List[List]:
        """
        获取历史K线数据
        
        Args:
            ts_code: 股票代码
            days: 获取天数
        
        Returns:
            list: 历史数据 [[日期, 开盘, 最高, 最低, 收盘], ...]
        """
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return []
            
            # [日期, 开盘, 最高, 最低, 收盘]
            result = []
            for _, row in df.iterrows():
                result.append([
                    row['trade_date'],  # 日期
                    float(row['open']) if row['open'] else 0,      # 开盘
                    float(row['high']) if row['high'] else 0,      # 最高
                    float(row['low']) if row['low'] else 0,        # 最低
                    float(row['close']) if row['close'] else 0     # 收盘
                ])
            
            return result
            
        except Exception as e:
            logger.error(f"获取历史数据失败 {ts_code}: {e}")
            return []
    
    def is_trading_day(self, target_date: date = None) -> bool:
        """
        判断是否为交易日
        
        Args:
            target_date: 目标日期，默认为今天
        
        Returns:
            bool: 是否为交易日
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            # 简单判断：周一到周五为交易日（实际应该查询交易日历）
            weekday = target_date.weekday()
            
            # 0-4代表周一到周五，5-6代表周六周日
            if weekday >= 5:
                return False
            
            # TODO: 可以进一步查询节假日信息
            # 这里可以集成中国节假日API或者使用trading_calendars库
            
            return True
            
        except Exception as e:
            logger.error(f"判断交易日失败: {e}")
            return False
    
    def get_market_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取财经新闻
        
        Args:
            limit: 新闻数量限制
        
        Returns:
            list: 新闻列表
        """
        try:
            # 这里可以集成多个新闻源
            # 1. 新浪财经
            # 2. 东方财富
            # 3. 腾讯财经
            
            news_list = []
            
            # 真实新闻爬取 - 从东方财富获取财经新闻
            news_list = self._crawl_eastmoney_news(limit)
            return news_list
            
        except Exception as e:
            logger.error(f"获取财经新闻失败: {e}")
            return []
    
    def _crawl_eastmoney_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        从东方财富网爬取财经新闻
        
        Args:
            limit: 获取新闻数量限制
            
        Returns:
            list: 新闻列表
        """
        try:
            import urllib.request
            import re
            from datetime import datetime
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
            }
            
            # 创建请求对象
            req = urllib.request.Request('http://finance.eastmoney.com/news/cdfsd.html', headers=headers)
            
            try:
                # 发送请求并获取响应
                with urllib.request.urlopen(req, timeout=10) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
            except Exception as e:
                logger.error(f"请求东方财富网失败: {e}")
                return []
            
            # 正则匹配新闻标题和内容
            # 匹配格式：title="新闻标题"...
            title_pattern = r'title="([^"]*)"'
            titles = re.findall(title_pattern, html_content)
            
            # 过滤掉空标题和包含【】的标题（通常是广告）
            filtered_titles = []
            for title in titles:
                if title and len(title.strip()) > 10:  # 过滤太短的标题
                    # 检查是否包含财经相关关键词
                    financial_keywords = ['股', '市', '金融', '投资', '经济', '银行', '基金', '证券', '债券', '期货', '外汇', '保险', '央行', '上市', 'IPO']
                    if any(keyword in title for keyword in financial_keywords):
                        filtered_titles.append(title)
            
            # 构建新闻列表
            news_list = []
            current_time = datetime.now()
            
            for i, title in enumerate(filtered_titles[:limit]):
                # 分离标题中的【分类】和内容
                category = '财经新闻'
                content_title = title
                
                if '【' in title and '】' in title:
                    start = title.find('【')
                    end = title.find('】')
                    if start != -1 and end != -1 and end > start:
                        category = title[start+1:end]
                        content_title = title[end+1:].strip()
                
                # 生成简单的摘要内容（实际项目中可以进一步爬取详细内容）
                summary = content_title[:100] + '...' if len(content_title) > 100 else content_title
                
                news_item = {
                    'title': content_title,
                    'content': summary,
                    'summary': summary,
                    'source': '东方财富',
                    'category': category,
                    'publish_time': (current_time.replace(hour=9, minute=i*2)).strftime('%Y-%m-%d %H:%M:%S'),  # 模拟时间间隔
                    'url': 'http://finance.eastmoney.com/news/',
                    'views': 0,
                    'related_stocks': [],
                }
                
                news_list.append(news_item)
            
            logger.info(f"成功爬取 {len(news_list)} 条新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"爬取东方财富新闻失败: {e}")
            return []
    
    def get_top10_stocks(self) -> List[Dict[str, Any]]:
        """
        获取涨幅前10股票
        
        Returns:
            list: 前10热门股票
        """
        try:
            # 获取今日涨幅榜前10
            today = datetime.now().strftime('%Y%m%d')
            
            # 获取今日行情数据
            df = self.pro.daily(trade_date=today)
            
            if df.empty:
                # 如果今日无数据，获取最近一个交易日的数据
                latest_date = self.get_latest_trade_date()
                if latest_date:
                    df = self.pro.daily(trade_date=latest_date)
            
            if df.empty:
                return []
            
            # 过滤掉涨跌幅为空的数据，按涨跌幅排序
            df = df.dropna(subset=['pct_chg'])
            df = df.sort_values('pct_chg', ascending=False)
            
            # 取前10
            top10 = df.head(10)
            
            result = []
            for _, row in top10.iterrows():
                # 获取股票名称
                stock_name = self.get_stock_name(row['ts_code'])
                
                result.append({
                    'ts_code': row['ts_code'],
                    'stock_name': stock_name,
                    'close': float(row['close']) if row['close'] else 0,
                    'open': float(row['open']) if row['open'] else 0,
                    'high': float(row['high']) if row['high'] else 0,
                    'low': float(row['low']) if row['low'] else 0,
                    'change': float(row['change']) if row['change'] else 0,
                    'pct_chg': float(row['pct_chg']) if row['pct_chg'] else 0,
                    'vol': int(row['vol']) if row['vol'] else 0,
                    'amount': float(row['amount']) if row['amount'] else 0,
                    'trade_date': row['trade_date']
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取涨幅前10股票失败: {e}")
            return []
    
    def get_stock_name(self, ts_code: str) -> str:
        """
        获取股票名称
        
        Args:
            ts_code: 股票代码
        
        Returns:
            str: 股票名称
        """
        try:
            # 先从数据库查询
            from stock.models import StockBasic
            try:
                stock = StockBasic.objects.get(ts_code=ts_code)
                return stock.name
            except:
                pass
            
            # 如果数据库没有，从tushare获取
            df = self.pro.stock_basic(ts_code=ts_code, fields='ts_code,name')
            if not df.empty:
                return df.iloc[0]['name']
            
            return ts_code  # 如果都获取不到，返回代码
            
        except Exception as e:
            logger.error(f"获取股票名称失败 {ts_code}: {e}")
            return ts_code
    
    def get_latest_trade_date(self) -> str:
        """
        获取最近交易日
        
        Returns:
            str: 最近交易日 (YYYYMMDD格式)
        """
        try:
            # 获取交易日历
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
            
            df = self.pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date)
            
            # 获取最近的交易日
            trading_days = df[df['is_open'] == 1]['cal_date'].tolist()
            
            if trading_days:
                return str(trading_days[-1])  # 最近的交易日
            
            return datetime.now().strftime('%Y%m%d')
            
        except Exception as e:
            logger.error(f"获取最近交易日失败: {e}")
            return datetime.now().strftime('%Y%m%d')
    
    def create_stock_table(self, ts_code: str) -> bool:
        """
        创建股票数据表
        
        Args:
            ts_code: 股票代码
        
        Returns:
            bool: 是否创建成功
        """
        try:
            # 连接数据库
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 构建表名
            if ts_code.endswith('.SH'):
                table_name = ts_code.replace('.SH', '_SH')
            elif ts_code.endswith('.SZ'):
                table_name = ts_code.replace('.SZ', '_SZ')
            else:
                table_name = ts_code
            
            # 创建股票数据表
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `trade_date` date NOT NULL,
                `open` decimal(10,3) DEFAULT NULL,
                `high` decimal(10,3) DEFAULT NULL,
                `low` decimal(10,3) DEFAULT NULL,
                `close` decimal(10,3) DEFAULT NULL,
                `pre_close` decimal(10,3) DEFAULT NULL,
                `change` decimal(10,3) DEFAULT NULL,
                `pct_chg` decimal(10,3) DEFAULT NULL,
                `vol` bigint(20) DEFAULT NULL,
                `amount` decimal(15,2) DEFAULT NULL,
                `create_time` timestamp DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                UNIQUE KEY `uk_trade_date` (`trade_date`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
            
            cursor.execute(create_sql)
            
            # 创建对应的分时数据表
            tick_table_name = f"dailyticks_{table_name}"
            tick_sql = f"""
            CREATE TABLE IF NOT EXISTS `{tick_table_name}` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `trade_time` datetime NOT NULL,
                `price` decimal(10,3) DEFAULT NULL,
                `volume` int(11) DEFAULT NULL,
                `amount` decimal(15,2) DEFAULT NULL,
                `create_time` timestamp DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                KEY `idx_trade_time` (`trade_time`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
            
            cursor.execute(tick_sql)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"股票表 {table_name} 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建股票表失败 {ts_code}: {e}")
            return False
    
    def update_stock_daily_data(self, ts_code: str) -> bool:
        """
        更新股票日线数据
        
        Args:
            ts_code: 股票代码
        
        Returns:
            bool: 是否更新成功
        """
        try:
            # 获取最新的日线数据
            today = datetime.now().strftime('%Y%m%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            
            df = self.pro.daily(ts_code=ts_code, start_date=yesterday, end_date=today)
            
            if df.empty:
                return False
            
            # 连接数据库
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 构建表名
            if ts_code.endswith('.SH'):
                table_name = ts_code.replace('.SH', '_SH')
            elif ts_code.endswith('.SZ'):
                table_name = ts_code.replace('.SZ', '_SZ')
            else:
                table_name = ts_code
            
            # 插入或更新数据
            for _, row in df.iterrows():
                insert_sql = f"""
                INSERT INTO `{table_name}` 
                (trade_date, open, high, low, close, pre_close, `change`, pct_chg, vol, amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                open=VALUES(open), high=VALUES(high), low=VALUES(low), 
                close=VALUES(close), pre_close=VALUES(pre_close), 
                `change`=VALUES(`change`), pct_chg=VALUES(pct_chg), 
                vol=VALUES(vol), amount=VALUES(amount)
                """
                
                cursor.execute(insert_sql, (
                    datetime.strptime(str(row['trade_date']), '%Y%m%d').date(),
                    row['open'], row['high'], row['low'], row['close'],
                    row['pre_close'], row['change'], row['pct_chg'],
                    row['vol'], row['amount']
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"股票 {ts_code} 日线数据更新成功")
            return True
            
        except Exception as e:
            logger.error(f"更新股票日线数据失败 {ts_code}: {e}")
            return False
    
    def batch_update_all_stocks(self) -> Dict[str, Any]:
        """
        批量更新所有股票数据
        
        Returns:
            dict: 更新结果统计
        """
        try:
            # 获取所有股票列表
            from stock.models import StockBasic
            
            stocks = StockBasic.objects.filter(list_status='L')[:100]  # 限制数量避免超时
            
            success_count = 0
            fail_count = 0
            
            for stock in stocks:
                try:
                    if self.update_stock_daily_data(stock.ts_code):
                        success_count += 1
                    else:
                        fail_count += 1
                    
                    # 避免频繁调用API
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"更新股票 {stock.ts_code} 失败: {e}")
                    fail_count += 1
            
            return {
                'success': True,
                'message': f'批量更新完成，成功: {success_count}, 失败: {fail_count}',
                'success_count': success_count,
                'fail_count': fail_count,
                'total_count': success_count + fail_count
            }
            
        except Exception as e:
            logger.error(f"批量更新股票数据失败: {e}")
            return {
                'success': False,
                'message': f'批量更新失败: {str(e)}',
                'success_count': 0,
                'fail_count': 0,
                'total_count': 0
            }


# 创建全局实例
quantitative_data_service = QuantitativeDataService()
# -*- coding: utf-8 -*-

import requests
import time
from typing import Dict, List, Optional
from decimal import Decimal


class RealTimeStockService:
    """Real-time stock data service"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_stock_pe_ratio(self, ts_code: str) -> Dict:
        """Get real-time PE ratio for a single stock"""
        try:
            # Try Tencent API first (best results from test)
            tencent_data = self._fetch_from_tencent([ts_code])
            if tencent_data.get(ts_code) and tencent_data[ts_code].get('pe_ratio', 0) > 0:
                return tencent_data[ts_code]

            # Fallback to East Money API
            em_data = self._fetch_from_eastmoney([ts_code])
            if em_data.get(ts_code):
                return em_data[ts_code]

            return {'pe_ratio': 0, 'current_price': 0, 'source': 'none'}

        except Exception as e:
            print(f"Error getting PE ratio for {ts_code}: {e}")
            return {'pe_ratio': 0, 'current_price': 0, 'source': 'error'}

    def get_batch_stock_data(self, ts_codes: List[str]) -> Dict:
        """Get real-time data for multiple stocks"""
        results = {}

        # Try Tencent API first (batch processing)
        try:
            tencent_data = self._fetch_from_tencent(ts_codes)
            results.update(tencent_data)
        except Exception as e:
            print(f"Tencent API error: {e}")

        # Fill missing data with East Money API
        missing_codes = [code for code in ts_codes if code not in results or results[code].get('pe_ratio', 0) <= 0]
        if missing_codes:
            try:
                em_data = self._fetch_from_eastmoney(missing_codes)
                for code, data in em_data.items():
                    if code not in results or results[code].get('pe_ratio', 0) <= 0:
                        results[code] = data
            except Exception as e:
                print(f"East Money API error: {e}")

        return results

    def _fetch_from_tencent(self, stock_codes: List[str]) -> Dict:
        """Fetch data from Tencent Finance API"""
        results = {}

        # Batch request up to 50 stocks
        batch_size = 50
        for i in range(0, len(stock_codes), batch_size):
            batch = stock_codes[i:i + batch_size]
            try:
                # Convert to Tencent format
                tencent_codes = [self._convert_to_tencent_code(code) for code in batch]
                codes_str = ','.join(tencent_codes)

                url = f"http://qt.gtimg.cn/q={codes_str}"
                response = self.session.get(url, timeout=10)
                response.encoding = 'gbk'

                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    for j, line in enumerate(lines):
                        if j < len(batch):
                            data = self._parse_tencent_data(line, batch[j])
                            if data:
                                results[batch[j]] = data

                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                print(f"Error fetching batch from Tencent: {e}")
                continue

        return results

    def _fetch_from_eastmoney(self, stock_codes: List[str]) -> Dict:
        """Fetch data from East Money API"""
        results = {}

        for code in stock_codes:
            try:
                # Convert TS code to East Money format
                em_code = self._convert_to_em_code(code)
                url = f"http://push2.eastmoney.com/api/qt/stock/get"
                params = {
                    'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                    'invt': '2',
                    'fltt': '2',
                    'fields': 'f43,f57,f58,f169,f170,f46,f44,f51,f168,f47,f164,f163,f116,f60,f45,f52,f162',
                    'secid': em_code
                }

                response = self.session.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        parsed_data = self._parse_eastmoney_data(data['data'], code)
                        if parsed_data:
                            results[code] = parsed_data

                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                print(f"Error fetching {code} from EastMoney: {e}")
                continue

        return results

    def _convert_to_tencent_code(self, ts_code: str) -> str:
        """Convert TS code to Tencent format"""
        code, exchange = ts_code.split('.')
        if exchange == 'SH':
            return f"sh{code}"
        elif exchange == 'SZ':
            return f"sz{code}"
        elif exchange == 'BJ':
            return f"bj{code}"
        return f"sh{code}"

    def _convert_to_em_code(self, ts_code: str) -> str:
        """Convert TS code to East Money format"""
        code, exchange = ts_code.split('.')
        if exchange == 'SH':
            return f"1.{code}"
        elif exchange == 'SZ':
            return f"0.{code}"
        elif exchange == 'BJ':
            return f"0.{code}"
        return f"1.{code}"

    def _parse_tencent_data(self, line: str, ts_code: str) -> Optional[Dict]:
        """解析腾讯API响应数据"""
        try:
            # 从 v_sh000001="..." 中提取数据
            start = line.find('"') + 1
            end = line.rfind('"')
            if start > 0 and end > start:
                data_str = line[start:end]
                fields = data_str.split('~')

                if len(fields) >= 50:
                    current_price = float(fields[3]) if fields[3] else 0
                    pe_ratio = float(fields[39]) if len(fields) > 39 and fields[39] else 0

                    # 处理负市盈率
                    if pe_ratio < 0:
                        pe_ratio = 0

                    # 腾讯API市值数据 - fields[45]是总市值，fields[44]是流通市值，单位通常是万元
                    market_cap_raw = float(fields[45]) if len(fields) > 45 and fields[45] else 0
                    circ_market_cap_raw = float(fields[44]) if len(fields) > 44 and fields[44] else 0

                    # 根据数值大小判断单位并转换为元
                    if market_cap_raw > 0:
                        if market_cap_raw < 100000:  # 小于10万，可能是万元单位
                            market_cap = market_cap_raw * 10000
                        else:  # 大于10万，可能已经是元单位
                            market_cap = market_cap_raw
                    else:
                        market_cap = 0

                    if circ_market_cap_raw > 0:
                        if circ_market_cap_raw < 100000:
                            circ_market_cap = circ_market_cap_raw * 10000
                        else:
                            circ_market_cap = circ_market_cap_raw
                    else:
                        circ_market_cap = 0

                    return {
                        'ts_code': ts_code,
                        'current_price': current_price,
                        'pe_ratio': pe_ratio,
                        'market_cap': market_cap,  # 总市值（元）
                        'circ_market_cap': circ_market_cap,  # 流通市值（元）
                        'turnover_rate': float(fields[38]) if len(fields) > 38 and fields[38] else 0,
                        'source': 'tencent'
                    }
        except Exception as e:
            print(f"解析腾讯数据失败 {ts_code}: {e}")
        return None

    def _parse_eastmoney_data(self, data: Dict, ts_code: str) -> Optional[Dict]:
        """解析东方财富API响应数据"""
        try:
            current_price = float(data.get('f43', 0)) / 100 if data.get('f43') else 0  # 价格单位是分
            pe_ratio = float(data.get('f162', 0)) if data.get('f162') else 0

            # 处理负市盈率
            if pe_ratio < 0:
                pe_ratio = 0

            # 市值数据处理 - f116是总市值，f117是流通市值，单位是万元
            market_cap = float(data.get('f116', 0)) * 10000 if data.get('f116') else 0  # 转换为元
            circ_market_cap = float(data.get('f117', 0)) * 10000 if data.get('f117') else 0  # 流通市值

            return {
                'ts_code': ts_code,
                'current_price': current_price,
                'pe_ratio': pe_ratio,
                'market_cap': market_cap,  # 总市值（元）
                'circ_market_cap': circ_market_cap,  # 流通市值（元）
                'turnover_rate': float(data.get('f168', 0)) if data.get('f168') else 0,
                'source': 'eastmoney'
            }
        except Exception as e:
            print(f"解析东方财富数据失败 {ts_code}: {e}")
        return None


# Global instance
realtime_service = RealTimeStockService()


def get_real_pe_ratio(ts_code: str) -> float:
    """Get real PE ratio for a stock"""
    try:
        data = realtime_service.get_stock_pe_ratio(ts_code)
        return float(data.get('pe_ratio', 0))
    except Exception as e:
        print(f"Error getting real PE ratio for {ts_code}: {e}")
        return 0.0


def get_batch_real_data(ts_codes: List[str]) -> Dict:
    """Get real data for multiple stocks"""
    try:
        return realtime_service.get_batch_stock_data(ts_codes)
    except Exception as e:
        print(f"Error getting batch real data: {e}")
        return {}
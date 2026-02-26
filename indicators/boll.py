"""
布林带指标 (Bollinger Bands)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


class BOLLIndicator:
    """布林带指标计算器"""
    
    def __init__(self, period: int = 20, std_dev: float = 2):
        """
        初始化布林带指标
        
        Args:
            period: 移动平均周期 (默认20)
            std_dev: 标准差倍数 (默认2)
        """
        self.period = period
        self.std_dev = std_dev
    
    def calculate(self, df: pd.DataFrame, price_col: str = 'close') -> pd.DataFrame:
        """
        计算布林带
        
        Args:
            df: 包含价格数据的DataFrame
            price_col: 价格列名
        
        Returns:
            添加了布林带数据的DataFrame
        """
        df = df.copy()
        
        # 计算中轨 (MB - Middle Band)
        df['boll_mid'] = df[price_col].rolling(window=self.period).mean()
        
        # 计算标准差
        std = df[price_col].rolling(window=self.period).std()
        
        # 计算上轨 (UP - Upper Band)
        df['boll_upper'] = df['boll_mid'] + (std * self.std_dev)
        
        # 计算下轨 (DN - Lower Band)
        df['boll_lower'] = df['boll_mid'] - (std * self.std_dev)
        
        # 计算 %B 指标
        df['boll_pctb'] = (df[price_col] - df['boll_lower']) / (df['boll_upper'] - df['boll_lower'])
        
        # 计算带宽 (Bandwidth)
        df['boll_width'] = (df['boll_upper'] - df['boll_lower']) / df['boll_mid'] * 100
        
        return df
    
    def get_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取布林带信号
        
        Returns:
            包含信号的字典
        """
        signals = []
        
        if len(df) < 2:
            return {"signals": signals, "status": " insufficient data"}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 获取当前价格位置
        current_price = latest.get('close', 0)
        
        # 超买信号：价格触及或突破上轨
        if latest.get('close', 0) >= latest.get('boll_upper', 0):
            signals.append({
                "type": "OVERBOUGHT",
                "message": "价格触及或突破上轨，可能回调",
                "severity": "SELL"
            })
        
        # 超卖信号：价格触及或突破下轨
        if latest.get('close', 0) <= latest.get('boll_lower', 0):
            signals.append({
                "type": "OVERSOLD",
                "message": "价格触及或突破下轨，可能反弹",
                "severity": "BUY"
            })
        
        # 中轨位置判断
        if latest.get('close', 0) > latest.get('boll_mid', 0):
            status = "中轨上方运行，多头趋势"
        else:
            status = "中轨下方运行，空头趋势"
        
        return {
            "signals": signals,
            "status": status,
            "upper": latest.get('boll_upper'),
            "mid": latest.get('boll_mid'),
            "lower": latest.get('boll_lower'),
            "pctb": latest.get('boll_pctb'),
            "width": latest.get('boll_width')
        }

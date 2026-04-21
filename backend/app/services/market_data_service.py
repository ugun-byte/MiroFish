import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import ta
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MarketDataService:
    @staticmethod
    def _is_korean_ticker(ticker: str) -> bool:
        """
        간단한 한국 주식 티커 판별 (6자리 숫자 혹은 .KS, .KQ 종결자 유무)
        """
        if ticker.endswith('.KS') or ticker.endswith('.KQ'):
            return True
        if ticker.isdigit() and len(ticker) == 6:
            return True
        return False

    @staticmethod
    def _clean_korean_ticker(ticker: str) -> str:
        """FinanceDataReader용으로 티커 포맷 정리 (숫자 6자리 추출)"""
        if ticker.endswith('.KS') or ticker.endswith('.KQ'):
            return ticker[:-3]
        return ticker

    @staticmethod
    def fetch_ohlcv(ticker: str, period_days: int = 365) -> pd.DataFrame:
        """
        주식 데이터를 가져옵니다.
        한국 주식의 경우 FinanceDataReader를 우선 시도하고, 실패 시 yfinance를 사용합니다.
        미국 등 해외 주식은 yfinance를 사용합니다.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        df = None

        try:
            if MarketDataService._is_korean_ticker(ticker):
                clean_ticker = MarketDataService._clean_korean_ticker(ticker)
                logger.info(f"Fetching Korean stock data using FinanceDataReader: {clean_ticker}")
                df = fdr.DataReader(clean_ticker, start_str, end_str)
                # FinanceDataReader 리턴값 정규화 (보통 Open, High, Low, Close, Volume 리턴)
            else:
                logger.info(f"Fetching global stock data using yfinance: {ticker}")
                stock = yf.Ticker(ticker)
                # period 대신 start/end로 정확한 OHLCV 획득
                df = stock.history(start=start_str, end=end_str)
        except Exception as e:
            logger.error(f"Failed to fetch market data for {ticker}: {e}")
            return pd.DataFrame()

        if df is None or df.empty:
            logger.warning(f"No market data found for {ticker}")
            return pd.DataFrame()

        # 데이터프레임 표준화 (컬럼 첫 글자 대문자 맞춤)
        # yfinance는 Date가 인덱스고 Open, High, Low, Close, Volume를 가짐
        # fdr 역시 Date 인덱스에 Open, High, Low, Close, Volume 가짐 (가끔 Change 포함)
        return df

    @staticmethod
    def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        OHLCV 데이터프레임에 보조지표(MACD, RSI, 볼린저밴드 등)를 추가합니다.
        단, 데이터가 너무 적을 경우 계산되지 않을 수 있습니다.
        """
        if df.empty or len(df) < 30:
            return df

        try:
            # RSI (14)
            df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
            
            # MACD
            macd = ta.trend.MACD(close=df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Diff'] = macd.macd_diff()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
            df['BB_High'] = bb.bollinger_hband()
            df['BB_Low'] = bb.bollinger_lband()
            df['BB_Mid'] = bb.bollinger_mavg()
            
            # Simple Moving Averages
            df['SMA_20'] = ta.trend.sma_indicator(close=df['Close'], window=20)
            df['SMA_60'] = ta.trend.sma_indicator(close=df['Close'], window=60)
            
        except Exception as e:
            logger.warning(f"Technical indicators calculation failed: {e}")
        
        return df

    @staticmethod
    def generate_market_summary(ticker: str, df: pd.DataFrame) -> str:
        """
        계산된 데이터프레임을 LLM이 읽기 쉬운 요약 텍스트(마크다운)로 변환합니다.
        """
        if df.empty:
            return f"❌ 시장 데이터를 가져오지 못했습니다 (Ticker: {ticker}). 티커 정보를 확인하세요."

        latest = df.iloc[-1]
        
        # 기본 정보
        close_price = latest.get('Close', 0)
        open_price = latest.get('Open', 0)
        volume = latest.get('Volume', 0)
        date_str = df.index[-1].strftime('%Y-%m-%d')
        
        # 보조지표 (계산된 경우만 표기)
        rsi = latest.get('RSI', 'N/A')
        rsi_str = f"{rsi:.2f}" if isinstance(rsi, (int, float)) and pd.notna(rsi) else 'N/A'
        
        macd_val = latest.get('MACD', 'N/A')
        macd_str = f"{macd_val:.2f}" if isinstance(macd_val, (int, float)) and pd.notna(macd_val) else 'N/A'
        
        sma20 = latest.get('SMA_20', 'N/A')
        sma60 = latest.get('SMA_60', 'N/A')
        
        # 간단한 트렌드 추정 로직
        trend = "보합권 (Neutral)"
        if isinstance(sma20, (int, float)) and isinstance(sma60, (int, float)) and pd.notna(sma20) and pd.notna(sma60):
            if close_price > sma20 and sma20 > sma60:
                trend = "단기적 상승세 (Bullish)"
            elif close_price < sma20 and sma20 < sma60:
                trend = "단기적 하락세 (Bearish)"
                
        if isinstance(rsi, (int, float)) and pd.notna(rsi):
            if rsi >= 70:
                trend += " / 과매수 구간 경고 (Overbought)"
            elif rsi <= 30:
                trend += " / 과매도 구간 진입 (Oversold)"

        # 마크다운 템플릿 작성
        summary = f"""
### 📊 [시장 데이터 분석: {ticker}]
*기준일자: {date_str}*

**[현재 가격 및 기본 정보]**
- 종가 (Close): {close_price:,.2f}
- 시가 (Open): {open_price:,.2f}
- 거래량 (Volume): {volume:,.0f}
- 단기 트렌드 시그널: **{trend}**

**[핵심 기술적 지표 (Technical Indicators)]**
- **RSI (14일)**: {rsi_str}  *(참고: 70 이상은 과매수, 30 이하는 과매도)*
- **MACD**: {macd_str}
- **이동평균 (SMA)**: 20MA({sma20:,.2f}), 60MA({sma60:,.2f})

*(이 데이터는 PRISM Quant Engine에 의해 자동으로 수집 및 계산되었습니다. 시뮬레이션 군중 심리와 이 정량적 차트 흐름을 결합하여 분석을 진행하십시오.)*
"""
        return summary.strip()

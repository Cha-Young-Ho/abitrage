"""
거래소 추상화 인터페이스
모든 거래소 worker가 구현해야 하는 기본 인터페이스
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
import asyncio
from dataclasses import dataclass
from enum import Enum

class ExchangeType(Enum):
    """거래소 타입"""
    BINANCE = "binance"
    UPBIT = "upbit"
    BITHUMB = "bithumb"
    COINBASE = "coinbase"
    KRAKEN = "kraken"

class DataType(Enum):
    """데이터 타입"""
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADE = "trade"
    KLINE = "kline"
    DEPTH = "depth"

@dataclass
class MarketData:
    """시장 데이터 구조"""
    exchange: str
    symbol: str
    data_type: DataType
    data: Dict[str, Any]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "data_type": self.data_type.value,
            "data": self.data,
            "timestamp": self.timestamp
        }

class BaseExchangeWorker(ABC):
    """거래소 worker 기본 클래스"""
    
    def __init__(self, exchange: ExchangeType, redis_manager):
        self.exchange = exchange
        self.redis_manager = redis_manager
        self.is_running = False
        self.subscribed_symbols: List[str] = []
        self.data_handlers: Dict[DataType, Callable] = {}
        
        # Redis 채널 설정
        self.channels = {
            DataType.TICKER: f"{exchange.value}:ticker",
            DataType.ORDERBOOK: f"{exchange.value}:orderbook", 
            DataType.TRADE: f"{exchange.value}:trade",
            DataType.KLINE: f"{exchange.value}:kline",
            DataType.DEPTH: f"{exchange.value}:depth"
        }
    
    @abstractmethod
    async def connect(self) -> bool:
        """거래소 연결"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """거래소 연결 해제"""
        pass
    
    @abstractmethod
    async def subscribe_ticker(self, symbols: List[str]) -> bool:
        """티커 데이터 구독"""
        pass
    
    @abstractmethod
    async def subscribe_orderbook(self, symbols: List[str]) -> bool:
        """오더북 데이터 구독"""
        pass
    
    @abstractmethod
    async def subscribe_trades(self, symbols: List[str]) -> bool:
        """거래 데이터 구독"""
        pass
    
    @abstractmethod
    async def subscribe_klines(self, symbols: List[str], interval: str = "1m") -> bool:
        """캔들 데이터 구독"""
        pass
    
    def register_data_handler(self, data_type: DataType, handler: Callable):
        """데이터 핸들러 등록"""
        self.data_handlers[data_type] = handler
    
    async def publish_data(self, market_data: MarketData):
        """Redis에 데이터 발행"""
        try:
            channel = self.channels.get(market_data.data_type)
            if channel:
                message = market_data.to_dict()
                success = self.redis_manager.publish(
                    self.exchange.value, 
                    channel, 
                    message
                )
                if success:
                    print(f"✅ {self.exchange.value}:{market_data.symbol} {market_data.data_type.value} 데이터 발행")
                else:
                    print(f"❌ {self.exchange.value}:{market_data.symbol} {market_data.data_type.value} 데이터 발행 실패")
        except Exception as e:
            print(f"❌ 데이터 발행 오류: {e}")
    
    async def start(self):
        """worker 시작"""
        if self.is_running:
            print(f"⚠️ {self.exchange.value} worker가 이미 실행 중입니다")
            return
        
        try:
            print(f"🚀 {self.exchange.value} worker 시작...")
            self.is_running = True
            
            # 거래소 연결
            if await self.connect():
                print(f"✅ {self.exchange.value} 연결 성공")
                
                # 기본 구독 설정
                if self.subscribed_symbols:
                    await self._setup_subscriptions()
                
                # 데이터 수신 루프 시작
                await self._data_loop()
            else:
                print(f"❌ {self.exchange.value} 연결 실패")
                self.is_running = False
                
        except Exception as e:
            print(f"❌ {self.exchange.value} worker 시작 오류: {e}")
            self.is_running = False
    
    async def stop(self):
        """worker 중지"""
        if not self.is_running:
            return
        
        print(f"🛑 {self.exchange.value} worker 중지...")
        self.is_running = False
        
        try:
            await self.disconnect()
            print(f"✅ {self.exchange.value} 연결 해제 완료")
        except Exception as e:
            print(f"❌ {self.exchange.value} 연결 해제 오류: {e}")
    
    async def _setup_subscriptions(self):
        """구독 설정"""
        try:
            # 기본적으로 티커 데이터 구독
            await self.subscribe_ticker(self.subscribed_symbols)
            print(f"✅ {self.exchange.value} 기본 구독 설정 완료")
        except Exception as e:
            print(f"❌ {self.exchange.value} 구독 설정 오류: {e}")
    
    async def _data_loop(self):
        """데이터 수신 루프"""
        while self.is_running:
            try:
                # 각 거래소별로 데이터 수신 로직 구현
                await self._receive_data()
                await asyncio.sleep(0.1)  # CPU 사용률 조절
            except Exception as e:
                print(f"❌ {self.exchange.value} 데이터 수신 오류: {e}")
                await asyncio.sleep(1)
    
    @abstractmethod
    async def _receive_data(self):
        """데이터 수신 (거래소별 구현)"""
        pass
    
    def add_symbols(self, symbols: List[str]):
        """구독할 심볼 추가"""
        for symbol in symbols:
            if symbol not in self.subscribed_symbols:
                self.subscribed_symbols.append(symbol)
        print(f"📝 {self.exchange.value} 구독 심볼 추가: {symbols}")
    
    def remove_symbols(self, symbols: List[str]):
        """구독할 심볼 제거"""
        for symbol in symbols:
            if symbol in self.subscribed_symbols:
                self.subscribed_symbols.remove(symbol)
        print(f"🗑️ {self.exchange.value} 구독 심볼 제거: {symbols}")
    
    def get_status(self) -> Dict[str, Any]:
        """worker 상태 반환"""
        return {
            "exchange": self.exchange.value,
            "is_running": self.is_running,
            "subscribed_symbols": self.subscribed_symbols,
            "channels": self.channels,
            "data_handlers": list(self.data_handlers.keys())
        }

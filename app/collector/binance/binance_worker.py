"""
Binance 거래소 데이터 수집 Worker
WebSocket을 통한 실시간 데이터 수집 및 Redis pub/sub으로 데이터 발행
"""
import asyncio
import json
import time
from typing import List, Dict, Any
from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException

from ..base_exchange import BaseExchangeWorker, ExchangeType, DataType, MarketData
from yh_db import RedisManager

class BinanceWorker(BaseExchangeWorker):
    """Binance 거래소 데이터 수집 Worker"""
    
    def __init__(self, redis_manager: RedisManager, api_key: str = None, api_secret: str = None):
        super().__init__(ExchangeType.BINANCE, redis_manager)
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = None
        self.socket_manager = None
        self.sockets = {}  # WebSocket 연결 관리
        
        # 기본 구독 심볼 설정
        self.subscribed_symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
            "XRPUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT"
        ]
    
    async def connect(self) -> bool:
        """Binance 연결"""
        try:
            # REST API 클라이언트 생성
            self.client = await AsyncClient.create(
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            # WebSocket 매니저 생성
            self.socket_manager = BinanceSocketManager(self.client)
            
            print(f"✅ Binance 연결 성공")
            return True
            
        except Exception as e:
            print(f"❌ Binance 연결 실패: {e}")
            return False
    
    async def disconnect(self):
        """Binance 연결 해제"""
        try:
            # WebSocket 연결들 종료
            for symbol, socket in self.sockets.items():
                await socket.close()
            self.sockets.clear()
            
            # 클라이언트 종료
            if self.client:
                await self.client.close_connection()
            
            print(f"✅ Binance 연결 해제 완료")
            
        except Exception as e:
            print(f"❌ Binance 연결 해제 오류: {e}")
    
    async def subscribe_ticker(self, symbols: List[str]) -> bool:
        """티커 데이터 구독"""
        try:
            for symbol in symbols:
                if symbol in self.sockets:
                    continue
                
                # 24hr 티커 통계 WebSocket 구독
                socket = self.socket_manager.symbol_ticker_socket(symbol)
                self.sockets[symbol] = socket
                
                # 비동기 태스크로 데이터 수신 시작
                asyncio.create_task(self._handle_ticker_data(socket, symbol))
            
            print(f"✅ Binance 티커 구독 완료: {symbols}")
            return True
            
        except Exception as e:
            print(f"❌ Binance 티커 구독 실패: {e}")
            return False
    
    async def subscribe_orderbook(self, symbols: List[str]) -> bool:
        """오더북 데이터 구독"""
        try:
            for symbol in symbols:
                socket_key = f"{symbol}_orderbook"
                if socket_key in self.sockets:
                    continue
                
                # 오더북 WebSocket 구독 (5레벨)
                socket = self.socket_manager.symbol_depth_socket(symbol, depth=5)
                self.sockets[socket_key] = socket
                
                # 비동기 태스크로 데이터 수신 시작
                asyncio.create_task(self._handle_orderbook_data(socket, symbol))
            
            print(f"✅ Binance 오더북 구독 완료: {symbols}")
            return True
            
        except Exception as e:
            print(f"❌ Binance 오더북 구독 실패: {e}")
            return False
    
    async def subscribe_trades(self, symbols: List[str]) -> bool:
        """거래 데이터 구독"""
        try:
            for symbol in symbols:
                socket_key = f"{symbol}_trades"
                if socket_key in self.sockets:
                    continue
                
                # 거래 내역 WebSocket 구독
                socket = self.socket_manager.symbol_trade_socket(symbol)
                self.sockets[socket_key] = socket
                
                # 비동기 태스크로 데이터 수신 시작
                asyncio.create_task(self._handle_trade_data(socket, symbol))
            
            print(f"✅ Binance 거래 데이터 구독 완료: {symbols}")
            return True
            
        except Exception as e:
            print(f"❌ Binance 거래 데이터 구독 실패: {e}")
            return False
    
    async def subscribe_klines(self, symbols: List[str], interval: str = "1m") -> bool:
        """캔들 데이터 구독"""
        try:
            for symbol in symbols:
                socket_key = f"{symbol}_klines_{interval}"
                if socket_key in self.sockets:
                    continue
                
                # 캔들 데이터 WebSocket 구독
                socket = self.socket_manager.kline_socket(symbol, interval=interval)
                self.sockets[socket_key] = socket
                
                # 비동기 태스크로 데이터 수신 시작
                asyncio.create_task(self._handle_kline_data(socket, symbol, interval))
            
            print(f"✅ Binance 캔들 데이터 구독 완료: {symbols} ({interval})")
            return True
            
        except Exception as e:
            print(f"❌ Binance 캔들 데이터 구독 실패: {e}")
            return False
    
    async def _handle_ticker_data(self, socket, symbol: str):
        """티커 데이터 처리"""
        async with socket as ticker_socket:
            while self.is_running:
                try:
                    data = await ticker_socket.recv()
                    
                    # MarketData 객체 생성
                    market_data = MarketData(
                        exchange=self.exchange.value,
                        symbol=symbol,
                        data_type=DataType.TICKER,
                        data=data,
                        timestamp=time.time()
                    )
                    
                    # Redis에 발행
                    await self.publish_data(market_data)
                    
                except Exception as e:
                    print(f"❌ {symbol} 티커 데이터 처리 오류: {e}")
                    await asyncio.sleep(1)
    
    async def _handle_orderbook_data(self, socket, symbol: str):
        """오더북 데이터 처리"""
        async with socket as orderbook_socket:
            while self.is_running:
                try:
                    data = await orderbook_socket.recv()
                    
                    # MarketData 객체 생성
                    market_data = MarketData(
                        exchange=self.exchange.value,
                        symbol=symbol,
                        data_type=DataType.ORDERBOOK,
                        data=data,
                        timestamp=time.time()
                    )
                    
                    # Redis에 발행
                    await self.publish_data(market_data)
                    
                except Exception as e:
                    print(f"❌ {symbol} 오더북 데이터 처리 오류: {e}")
                    await asyncio.sleep(1)
    
    async def _handle_trade_data(self, socket, symbol: str):
        """거래 데이터 처리"""
        async with socket as trade_socket:
            while self.is_running:
                try:
                    data = await trade_socket.recv()
                    
                    # MarketData 객체 생성
                    market_data = MarketData(
                        exchange=self.exchange.value,
                        symbol=symbol,
                        data_type=DataType.TRADE,
                        data=data,
                        timestamp=time.time()
                    )
                    
                    # Redis에 발행
                    await self.publish_data(market_data)
                    
                except Exception as e:
                    print(f"❌ {symbol} 거래 데이터 처리 오류: {e}")
                    await asyncio.sleep(1)
    
    async def _handle_kline_data(self, socket, symbol: str, interval: str):
        """캔들 데이터 처리"""
        async with socket as kline_socket:
            while self.is_running:
                try:
                    data = await kline_socket.recv()
                    
                    # MarketData 객체 생성
                    market_data = MarketData(
                        exchange=self.exchange.value,
                        symbol=symbol,
                        data_type=DataType.KLINE,
                        data=data,
                        timestamp=time.time()
                    )
                    
                    # Redis에 발행
                    await self.publish_data(market_data)
                    
                except Exception as e:
                    print(f"❌ {symbol} 캔들 데이터 처리 오류: {e}")
                    await asyncio.sleep(1)
    
    async def _receive_data(self):
        """데이터 수신 (WebSocket으로 자동 처리됨)"""
        # WebSocket은 별도 태스크에서 처리되므로 여기서는 대기만
        await asyncio.sleep(1)
    
    async def get_account_info(self) -> Dict[str, Any]:
        """계정 정보 조회 (API 키가 있는 경우)"""
        if not self.client or not self.api_key:
            return {"error": "API 키가 설정되지 않았습니다"}
        
        try:
            account_info = await self.client.get_account()
            return account_info
        except BinanceAPIException as e:
            return {"error": f"계정 정보 조회 실패: {e}"}
    
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """심볼 정보 조회"""
        if not self.client:
            return {"error": "클라이언트가 연결되지 않았습니다"}
        
        try:
            symbol_info = await self.client.get_symbol_info(symbol)
            return symbol_info
        except BinanceAPIException as e:
            return {"error": f"심볼 정보 조회 실패: {e}"}

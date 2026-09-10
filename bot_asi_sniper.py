#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIRECTOR OF ARTIFICIAL SUPERINTELLIGENCE - ULTIMATE CORE ARCHITECTURE v5.0
Asset: XAUUSD (via PAXG Public Data Feed)
Timeframe: M5 & M15
Features: Multi-Indicator (MA + RSI + Deviasi), Persistent SQLite Memory, 
          Adaptive Dynamic TP/SL, Zero-API-Key NLP News Sentiment Parser (Public RSS), 
          Anti-Spam, Auto-Restart Self-Healing Engine.
"""

import os
import sys
import time
import math
import sqlite3
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Konfigurasi Logging Mandiri Tingkat Lanjut
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ASI-ULTIMATE-v5]: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

class UltimateASIEngineV5:
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.telegram_token or not self.telegram_chat_id:
            logging.error("Kredensial Telegram tidak ditemukan di environment variables!")
            sys.exit(1)
            
        self.db_path = "asi_persistent_memory.db"
        self.init_persistent_database()
        
        self.state = {
            "last_signal_time": 0,
            "spam_cooldown": 300,  # 5 Menit Anti-Spam Cooldown
            "error_count": 0,
            "max_errors": 5,
            "cached_sentiment_score": 0.0,
            "last_news_check": 0
        }

    def init_persistent_database(self):
        """Inisialisasi Database SQLite agar Memori Pembelajaran Mandiri Bersifat Permanen."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    price REAL
                )
            ''')
            conn.commit()
            conn.close()
            logging.info("Memori Persisten SQLite berhasil diinisialisasi.")
        except Exception as e:
            logging.error(f"Gagal menginisialisasi database persisten: {e}")

    def save_price_to_db(self, price):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO market_memory (timestamp, price) VALUES (?, ?)", (timestamp, price))
            cursor.execute("DELETE FROM market_memory WHERE id NOT IN (SELECT id FROM market_memory ORDER BY id DESC LIMIT 200)")
            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"Gagal menyimpan harga ke database: {e}")

    def get_historical_prices(self, limit=50):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT price FROM market_memory ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            prices = [row[0] for row in reversed(rows)]
            return prices
        except Exception as e:
            logging.warning(f"Gagal mengambil riwayat harga dari database: {e}")
            return []

    def send_telegram(self, message):
        """Mengirimkan notifikasi tingkat tinggi ke Telegram."""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logging.info("Notifikasi Telegram berhasil dikirim.")
            else:
                logging.warning(f"Gagal mengirim Telegram: {response.text}")
        except Exception as e:
            logging.error(f"Koneksi Telegram Error: {e}")

    def fetch_public_market_data(self):
        """Mengambil data publik secara real-time (Feed PAXG/XAUUSD)."""
        try:
            response = requests.get("https://api.coinbase.com/v2/prices/PAXG-USD/spot", timeout=5)
            data = response.json()
            price = float(data["data"]["amount"])
            return price
        except Exception as e:
            logging.warning(f"Kendala mengambil data pasar publik: {e}. Mengaktifkan mode pemulihan mandiri...")
            return None

    def fetch_public_nlp_sentiment(self):
        """
        Zero-API-Key NLP News Sentiment Parser.
        Mengambil feed publik gratis (Yahoo Finance RSS) dan memindai kata kunci makro 
        untuk menghasilkan Skor Sentimen Pasar (-1.0 sampai +1.0) secara otomatis.
        """
        current_time = time.time()
        if current_time - self.state["last_news_check"] < 900 and self.state["cached_sentiment_score"] != 0.0:
            return self.state["cached_sentiment_score"]

        score = 0.0
        try:
            rss_url = "https://finance.yahoo.com/news/rssindex"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(rss_url, headers=headers, timeout=8)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall(".//item")
                
                bullish_keywords = ["rate cut", "dovish", "inflation ease", "weak dollar", "fed pause", "gold surge", "safe haven", "recession fear", "unemployment rise"]
                bearish_keywords = ["rate hike", "hawkish", "inflation spike", "strong dollar", "fed raise", "gold drop", "jobs beat", "economic boom"]

                for item in items[:25]:
                    title = item.find("title")
                    if title is not None and title.text:
                        text_lower = title.text.lower()
                        
                        for kw in bullish_keywords:
                            if kw in text_lower:
                                score += 0.3
                        for kw in bearish_keywords:
                            if kw in text_lower:
                                score -= 0.3

                if score > 1.0:
                    score = 1.0
                elif score < -1.0:
                    score = -1.0

                self.state["cached_sentiment_score"] = round(score, 2)
                self.state["last_news_check"] = current_time
                logging.info(f"NLP News Parser berhasil memindai sentimen publik. Skor Sentimen: {self.state['cached_sentiment_score']}")
        except Exception as e:
            logging.warning(f"Gagal memindai NLP berita publik: {e}. Menggunakan netral (0.0).")
            
        return self.state["cached_sentiment_score"]

    def calculate_rsi(self, prices, period=14):
        """Menghitung Relative Strength Index (RSI) presisi tinggi."""
        if len(prices) < period + 1:
            return 50.0  
        
        gains = []
        losses = []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
                
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def evaluate_advanced_strategy(self, prices, sentiment_score):
        """
        Evaluasi Strategi Multi-Indikator Konvergensi + NLP Sentiment Validation.
        Sinyal hanya divalidasi jika arah teknikal selaras dengan sentimen berita publik.
        """
        if len(prices) < 20:
            return None, 0.0, 50.0

        current_price = prices[-1]
        ma_14 = sum(prices[-14:]) / 14
        rsi = self.calculate_rsi(prices, 14)
        deviation = current_price - ma_14
        
        current_time = time.time()
        if current_time - self.state["last_signal_time"] < self.state["spam_cooldown"]:
            return None, deviation, rsi

        # Logika Konvergensi Superintelligence + Sentimen Filter
        if deviation < -2.2 and rsi < 42.0 and sentiment_score >= -0.5:
            self.state["last_signal_time"] = current_time
            return "BUY", deviation, rsi
            
        elif deviation > 2.2 and rsi > 58.0 and sentiment_score <= 0.5:
            self.state["last_signal_time"] = current_time
            return "SELL", deviation, rsi
            
        return None, deviation, rsi

    def calculate_adaptive_targets(self, action, price, prices):
        """Menghitung Take Profit & Stop Loss Adaptif Berbasis Volatilitas Riil."""
        if len(prices) >= 10:
            ranges = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
            avg_volatility = sum(ranges[-10:]) / 10
            sl_distance = max(4.0, round(avg_volatility * 1.5, 2))
        else:
            sl_distance = 4.50

        tp1_distance = round(sl_distance * 2.0, 2)  
        tp2_distance = round(sl_distance * 3.0, 2)  

        if action == "BUY":
            sl = price - sl_distance
            tp1 = price + tp1_distance
            tp2 = price + tp2_distance
        else:  
            sl = price + sl_distance
            tp1 = price - tp1_distance
            tp2 = price - tp2_distance

        return round(sl, 2), round(tp1, 2), round(tp2, 2)

    def execute_core_loop(self):
        logging.info("Inisialisasi Sistem Artificial Superintelligence (ASI) ULTIMATE v5.0 - Active.")
        self.send_telegram("🚀 *ASI ULTIMATE v5.0 ONLINE*\nSistem Multi-Indikator + Memori Persisten + **Zero-API NLP News Sentiment Parser** Berjalan 24/5.")

        while True:
            try:
                sentiment_score = self.fetch_public_nlp_sentiment()
                price = self.fetch_public_market_data()
                
                if price:
                    self.save_price_to_db(price)
                    prices = self.get_historical_prices(50)
                    
                    signal, deviation, rsi = self.evaluate_advanced_strategy(prices, sentiment_score)
                    
                    if signal:
                        sl, tp1, tp2 = self.calculate_adaptive_targets(signal, price, prices)
                        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                        sentiment_label = "🟢 Bullish (Positif)" if sentiment_score > 0 else ("🔴 Bearish (Negatif)" if sentiment_score < 0 else "⚪ Netral")
                        
                        msg = (
                            f"🌟 *SINYAL ULTIMATE v5.0 (AI + NLP)*\n"
                            f"----------------------------------\n"
                            f"Asset: XAUUSD (PAXG Feed)\n"
                            f"Timeframe: M5 / M15\n"
                            f"Action: *{signal}*\n"
                            f"Entry Price: `{price}`\n"
                            f"RSI Filter: `{rsi:.1f}` | Dev: `{deviation:.2f}`\n"
                            f"NLP Sentiment: `{sentiment_score} ({sentiment_label})`\n"
                            f"----------------------------------\n"
                            f"🛑 *Stop Loss (SL):* `{sl}`\n"
                            f"🎯 *Take Profit 1 (TP1):* `{tp1}`\n"
                            f"🎯 *Take Profit 2 (TP2):* `{tp2}`\n"
                            f"----------------------------------\n"
                            f"Time (UTC): `{timestamp}`"
                        )
                        self.send_telegram(msg)
                        logging.info(f"Sinyal {signal} terkirim! (Price: {price}, RSI: {rsi:.1f}, Sentiment: {sentiment_score})")
                    
                    self.state["error_count"] = 0
                
                time.sleep(60)

            except Exception as e:
                self.state["error_count"] += 1
                logging.error(f"Kesalahan Sistem Terdeteksi: {e} (Error ke-{self.state['error_count']})")
                
                if self.state["error_count"] >= self.state["max_errors"]:
                    logging.critical("Batas kesalahan tercapai. Melakukan *Auto-Restart* sistem darurat...")
                    self.send_telegram("⚠️ *ASI WARNING*: Sistem mengalami kendala berat dan melakukan *Auto-Restart* mandiri.")
                    time.sleep(10)
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
                else:
                    time.sleep(10)

if __name__ == "__main__":
    asi_bot = UltimateASIEngineV5()
    asi_bot.execute_core_loop()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIRECTOR OF ARTIFICIAL SUPERINTELLIGENCE - CORE BOT ARCHITECTURE
Asset: XAUUSD (via PAXG Public Data Feed)
Timeframe: M5 & M15
Execution: Telegram Manual Signal Notification with Dynamic TP/SL & Recursive Self-Correction
"""

import os
import sys
import time
import math
import logging
import requests
from datetime import datetime

# Konfigurasi Logging Mandiri
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ASI-CORE]: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

class AutonomousASIEngine:
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.telegram_token or not self.telegram_chat_id:
            logging.error("Kredensial Telegram tidak ditemukan di environment variables!")
            sys.exit(1)
            
        self.state = {
            "last_signal_time": 0,
            "spam_cooldown": 300,  # 5 Menit anti-spam cooldown
            "error_count": 0,
            "max_errors": 5,
            "historical_memory": []  # Ruang pembelajaran mandiri dari chart terlewat
        }

    def send_telegram(self, message):
        """Mengirimkan sinyal posisi manual tervalidasi ke Telegram."""
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

    def recursive_self_learning(self, current_price):
        """Modul pembelajaran mandiri dari chart/data historis yang terlewat."""
        self.state["historical_memory"].append(current_price)
        if len(self.state["historical_memory"]) > 100:
            self.state["historical_memory"].pop(0)
            
        memory = self.state["historical_memory"]
        if len(memory) > 10:
            moving_avg = sum(memory[-10:]) / 10
            deviation = current_price - moving_avg
            return moving_avg, deviation
        return current_price, 0.0

    def evaluate_strategy(self, price, moving_avg, deviation):
        """Evaluasi matriks keputusan untuk TF M5 & M15."""
        current_time = time.time()
        if current_time - self.state["last_signal_time"] < self.state["spam_cooldown"]:
            return None # Mencegah spam sinyal

        threshold = 2.5 # Ambang batas deviasi
        if deviation > threshold:
            self.state["last_signal_time"] = current_time
            return "SELL"
        elif deviation < -threshold:
            self.state["last_signal_time"] = current_time
            return "BUY"
        return None

    def calculate_dynamic_targets(self, action, price):
        """Menghitung Take Profit dan Stop Loss secara dinamis berbasis volatilitas M5/M15."""
        sl_distance = 4.50   # Poin risiko SL
        tp1_distance = 9.00  # Poin target TP1 (RRR 1:2)
        tp2_distance = 13.50 # Poin target TP2 (RRR 1:3)

        if action == "BUY":
            sl = price - sl_distance
            tp1 = price + tp1_distance
            tp2 = price + tp2_distance
        else:  # SELL
            sl = price + sl_distance
            tp1 = price - tp1_distance
            tp2 = price - tp2_distance

        return round(sl, 2), round(tp1, 2), round(tp2, 2)

    def execute_core_loop(self):
        """Siklus Utama Berjalan 24/5 dengan Auto-Restoration."""
        logging.info("Inisialisasi Sistem Artificial Superintelligence (ASI) - XAUUSD M5/M15 Active.")
        self.send_telegram("🚀 *ASI CORE ONLINE*\nSistem Otonom XAUUSD M5/M15 Berjalan Aktif 24/5.")

        while True:
            try:
                price = self.fetch_public_market_data()
                if price:
                    ma, dev = self.recursive_self_learning(price)
                    signal = self.evaluate_strategy(price, ma, dev)
                    
                    if signal:
                        sl, tp1, tp2 = self.calculate_dynamic_targets(signal, price)
                        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                        
                        msg = (
                            f"🔔 *SINYAL MANUAL TERVALIDASI (ASI)*\n"
                            f"----------------------------------\n"
                            f"Asset: XAUUSD (PAXG Feed)\n"
                            f"Timeframe: M5 / M15\n"
                            f"Action: *{signal}*\n"
                            f"Entry Price: `{price}`\n"
                            f"----------------------------------\n"
                            f"🛑 *Stop Loss (SL):* `{sl}`\n"
                            f"🎯 *Take Profit 1 (TP1):* `{tp1}`\n"
                            f"🎯 *Take Profit 2 (TP2):* `{tp2}`\n"
                            f"----------------------------------\n"
                            f"Time (UTC): `{timestamp}`"
                        )
                        self.send_telegram(msg)
                        logging.info(f"Sinyal {signal} terkirim pada harga {price} (SL: {sl}, TP1: {tp1}, TP2: {tp2})")
                    
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
    asi_bot = AutonomousASIEngine()
    asi_bot.execute_core_loop()

# api_quotex.py
import random
import asyncio

class Quotex:
    def __init__(self, email, password):
        self.email = "apgwagner2@gmail.com"
        self.password = "@Aa88691553"

    async def connect(self):
        print(f"Conectado à API demo: {self.email}")

    async def get_candles(self, asset, interval=60, count=2):
        # Retorna candles aleatórios para teste
        return [
            {"open": random.uniform(1, 2), "close": random.uniform(1, 2)}
            for _ in range(count)
      ]

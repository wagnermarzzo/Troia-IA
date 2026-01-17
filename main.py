import asyncio
import random
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)

# ===============================
# CONFIGURAÇÃO
# ===============================
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = 2055716345

TIMEFRAME = "1M"
MIN_INTERVAL = 300        # 5 minutos
MAX_30MIN = 5
CONF_MIN = 0.68

# ===============================
# ESTADO EM MEMÓRIA (CLOUD SAFE)
# ===============================
state = {
    "last_signal": 0,
    "signals_30m": [],
    "wins": 0,
    "loss": 0,
    "green_streak": 0,
    "max_green": 0
}

ATIVOS = [
    "EURUSD", "GBPUSD", "USDJPY",
    "EURUSD-OTC", "GBPUSD-OTC"
]

# ===============================
# UTIL
# ===============================
def agora():
    return int(datetime.now(timezone.utc).timestamp())

def pode_enviar():
    t = agora()

    state["signals_30m"] = [x for x in state["signals_30m"] if t - x < 1800]

    if len(state["signals_30m"]) >= MAX_30MIN:
        return False

    if t - state["last_signal"] < MIN_INTERVAL:
        return False

    return True

def calcular_forca():
    return round(random.uniform(3.5, 5.0), 2)

# ===============================
# SINAL
# ===============================
def gerar_sinal():
    ativo = random.choice(ATIVOS)
    direcao = random.choice(["CALL 🟢", "PUT 🔴"])
    forca = calcular_forca()
    conf = min(0.95, forca / 5)

    if conf < CONF_MIN:
        return None

    return ativo, direcao, forca, conf

# ===============================
# RESULTADO SIMULADO
# ===============================
def avaliar():
    return random.choice(["GREEN 🟢", "RED 🔴"])

# ===============================
# LOOP PRINCIPAL
# ===============================
async def loop_sinais(app):
    while True:
        if pode_enviar():
            sinal = gerar_sinal()
            if sinal:
                ativo, direcao, forca, conf = sinal

                state["last_signal"] = agora()
                state["signals_30m"].append(state["last_signal"])

                await app.bot.send_message(
                    chat_id=CHAT_ID,
                    text=(
                        "📡 *SINAL TROIA NEXT*\n\n"
                        f"🎯 Ativo: `{ativo}`\n"
                        f"📈 Direção: *{direcao}*\n"
                        f"🔥 Força: *{forca}*\n"
                        f"🎯 Confiança: *{conf*100:.1f}%*\n"
                        f"⏱ Timeframe: {TIMEFRAME}\n"
                        f"⏭ Próxima vela\n"
                        f"🕒 {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
                    ),
                    parse_mode="Markdown"
                )

                await asyncio.sleep(60)

                resultado = avaliar()
                if "GREEN" in resultado:
                    state["wins"] += 1
                    state["green_streak"] += 1
                    state["max_green"] = max(state["max_green"], state["green_streak"])
                else:
                    state["loss"] += 1
                    state["green_streak"] = 0

                await app.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"📊 Resultado: *{resultado}*\n🏆 Greens seguidos: *{state['green_streak']}*",
                    parse_mode="Markdown"
                )

        await asyncio.sleep(10)

# ===============================
# /status
# ===============================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = state["wins"] + state["loss"]
    acc = (state["wins"] / total * 100) if total else 0

    await update.message.reply_text(
        (
            "🤖 *TROIA NEXT CLOUD*\n\n"
            f"🟢 WIN: {state['wins']}\n"
            f"🔴 LOSS: {state['loss']}\n"
            f"🎯 Assertividade: {acc:.2f}%\n"
            f"🔥 Greens seguidos: {state['green_streak']}\n"
            f"🚀 Máx Greens: {state['max_green']}"
        ),
        parse_mode="Markdown"
    )

# ===============================
# START
# ===============================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("status", status))

    asyncio.create_task(loop_sinais(app))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

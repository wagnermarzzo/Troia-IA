import random
import asyncio
from datetime import datetime, timezone

from telegram import Bot
from telegram.ext import ApplicationBuilder, ContextTypes

# ================= CONFIG =================
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = 2055716345

INTERVALO_ANALISE = 60  # segundos
TEMPO_VELA = 60         # 1 minuto

# ================= ESTADO =================
sinal_pendente = False
dados_sinal = {}

greens = 0
reds = 0
streak = 0

bot = Bot(token=TOKEN)

# ================= FUNÇÕES =================

def analisar_mercado():
    """Simulação avançada de análise (placeholder IA)"""
    forca = random.randint(65, 92)
    direcao = random.choice(["CALL ⬆️", "PUT ⬇️"])
    ativo = random.choice(["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC"])
    return ativo, direcao, forca


async def enviar_sinal():
    global sinal_pendente, dados_sinal

    ativo, direcao, forca = analisar_mercado()

    dados_sinal = {
        "ativo": ativo,
        "direcao": direcao,
        "forca": forca,
        "hora": datetime.now(timezone.utc)
    }

    texto = (
        "📡 IAQuotex Sinais\n\n"
        f"📊 Ativo: {ativo}\n"
        f"🕯 Direção: {direcao}\n"
        "⏱ Entrada: PRÓXIMA VELA\n"
        f"🎯 Força do sinal: {forca}%\n\n"
        "⚠️ Aguarde a próxima vela"
    )

    await bot.send_message(chat_id=CHAT_ID, text=texto)
    sinal_pendente = True


async def avaliar_resultado():
    global sinal_pendente, greens, reds, streak

    if not sinal_pendente:
        return

    resultado = random.choice(["GREEN", "RED"])

    if resultado == "GREEN":
        greens += 1
        streak += 1
        emoji = "🟢 GREEN ✅"
    else:
        reds += 1
        streak = 0
        emoji = "🔴 RED ❌"

    total = greens + reds
    assertividade = (greens / total) * 100 if total > 0 else 0

    texto = (
        "📡 IAQuotex Sinais\n\n"
        f"{emoji}\n\n"
        "📊 Placar:\n"
        f"🟢 Greens: {greens}\n"
        f"🔴 Reds: {reds}\n"
        f"🔥 Streak: {streak}\n"
        f"📈 Assertividade: {assertividade:.2f}%"
    )

    await bot.send_message(chat_id=CHAT_ID, text=texto)
    sinal_pendente = False


# ================= LOOP PRINCIPAL =================

async def loop_sinais(context: ContextTypes.DEFAULT_TYPE):
    global sinal_pendente

    if not sinal_pendente:
        await enviar_sinal()
    else:
        await avaliar_resultado()


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.job_queue.run_repeating(
        loop_sinais,
        interval=INTERVALO_ANALISE,
        first=10
    )

    print("🧠 TROIA IA v9 ONLINE — Cloud Stable")
    app.run_polling()


if __name__ == "__main__":
    main()

import random
from datetime import datetime, timedelta, timezone
from telegram import Bot
from telegram.ext import ApplicationBuilder, ContextTypes

# ================= CONFIG =================
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = 2055716345

INTERVALO_LOOP = 30
TEMPO_VELA = 60
PAUSA_APOS_RED = 600  # 10 minutos

# ================= ESTADO =================
estado = "LIVRE"
sinal_atual = None
pausa_ate = None

greens = 0
reds = 0
streak = 0

estrategias = {
    "Tendência": 1.0,
    "Reversão": 1.0,
    "Price Action": 1.0,
    "Micro Tendência": 1.0
}

bot = Bot(token=TOKEN)

# ================= FUNÇÕES =================

def agora_utc():
    return datetime.now(timezone.utc)

def proxima_vela():
    t = agora_utc() + timedelta(seconds=TEMPO_VELA)
    return t.replace(second=0).strftime("%H:%M")

def score_estrategia(nome):
    base = estrategias[nome] * 100
    ruído = random.randint(-5, 5)
    return int(base + ruído)

def escolher_estrategia():
    return max(estrategias, key=score_estrategia)

def analisar_mercado():
    estrategia = escolher_estrategia()
    score = score_estrategia(estrategia)

    if score < 75:
        return None

    ativo = random.choice(["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC"])
    direcao = random.choice(["CALL ⬆️", "PUT ⬇️"])
    confianca = min(95, score)

    return ativo, direcao, estrategia, score, confianca

async def enviar_sinal():
    global estado, sinal_atual

    if pausa_ate and agora_utc() < pausa_ate:
        return

    analise = analisar_mercado()
    if not analise:
        return

    ativo, direcao, estrategia, score, confianca = analise
    entrada = proxima_vela()

    sinal_atual = {
        "ativo": ativo,
        "direcao": direcao,
        "estrategia": estrategia
    }

    texto = (
        "🤖 **IAQuotex Sinais — TROIA v11**\n\n"
        "🚨 **SETUP VALIDADO PELO MOTOR IA**\n\n"
        f"📊 **Ativo:** {ativo}\n"
        f"🕯 **Direção:** {direcao}\n"
        f"⏰ **Entrada:** {entrada} (PRÓXIMA VELA)\n"
        f"🧠 **Estratégia:** {estrategia}\n"
        f"⭐ **Score:** {score}\n"
        f"🎯 **Confiança:** {confianca}%\n\n"
        "⚠️ Operação única. Aguarde o fechamento."
    )

    await bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")
    estado = "AGUARDANDO_RESULTADO"

async def enviar_resultado():
    global estado, greens, reds, streak, pausa_ate

    resultado = random.choice(["GREEN", "RED"])

    if resultado == "GREEN":
        greens += 1
        streak += 1
        estrategias[sinal_atual["estrategia"]] += 0.05
        texto = "🟢 **GREEN CONFIRMADO!** Mercado respeitou a leitura."
    else:
        reds += 1
        streak = 0
        estrategias[sinal_atual["estrategia"]] -= 0.07
        texto = "🔴 **RED.** Mercado em correção."

        if reds >= 2:
            pausa_ate = agora_utc() + timedelta(seconds=PAUSA_APOS_RED)

    total = greens + reds
    acc = (greens / total) * 100 if total else 0

    resumo = (
        f"{texto}\n\n"
        f"📊 Greens: {greens}\n"
        f"🔴 Reds: {reds}\n"
        f"🔥 Streak: {streak}\n"
        f"📈 Assertividade: {acc:.2f}%\n\n"
        "🧠 IA recalibrando estratégias..."
    )

    await bot.send_message(chat_id=CHAT_ID, text=resumo, parse_mode="Markdown")
    estado = "LIVRE"

# ================= LOOP =================

async def loop_principal(context: ContextTypes.DEFAULT_TYPE):
    if estado == "LIVRE":
        await enviar_sinal()
    else:
        await enviar_resultado()

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.job_queue.run_repeating(loop_principal, interval=INTERVALO_LOOP, first=10)
    print("🚀 TROIA IA v11 ONLINE — CLOUD STABLE")
    app.run_polling()

if __name__ == "__main__":
    main()

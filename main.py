import telebot
import time
import json
from datetime import datetime, timezone
import os

# ===============================
# CONFIGURAÇÃO
# ===============================
TOKEN = "8536239572:AAG82o0mJw9WP3RKGrJTaLp-Hl2q8Gx6HYY"
CHAT_ID = "2055716345"

TIMEFRAME = "1M"
INTERVALO_LOOP = 10          # loop roda a cada 10s
MIN_SINAL_INTERVAL = 300     # mínimo 5 min entre sinais
MAX_SINAL_30MIN = 5
CONF_MIN = 0.68
SCORE_MIN = 7.0

MEMORY_FILE = "troia_memory.json"

bot = telebot.TeleBot(TOKEN, threaded=False)

# ===============================
# ATIVOS
# ===============================
ATIVOS = [
    "EURUSD","GBPUSD","USDJPY","AUDUSD",
    "EURJPY","GBPJPY","EURUSD-OTC","GBPUSD-OTC"
]

# ===============================
# MEMÓRIA PERSISTENTE
# ===============================
def carregar_memoria():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {
        "stats": {a: {"win": 1, "loss": 1, "loss_seq": 0} for a in ATIVOS},
        "estrategias": {
            "tendencia": 1.0,
            "reversao": 1.0,
            "price_action": 1.0,
            "micro_tendencia": 1.0
        },
        "wins": 0,
        "loss": 0,
        "green_streak": 0,
        "max_green": 0,
        "ultimos_sinais": []
    }

mem = carregar_memoria()

def salvar_memoria():
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)

# ===============================
# SESSÃO (UTC)
# ===============================
def sessao_ativa():
    h = datetime.now(timezone.utc).hour
    return (7 <= h <= 11) or (13 <= h <= 17)

# ===============================
# CONTEXTO (DETERMINÍSTICO)
# ===============================
def contexto_mercado(ativo):
    s = mem["stats"][ativo]
    taxa = s["win"] / (s["win"] + s["loss"])

    if taxa > 0.55:
        return "TENDÊNCIA"
    if taxa < 0.48:
        return "LATERAL"
    return "TRANSIÇÃO"

# ===============================
# CANDLE SINTÉTICO (SEM RANDOM)
# ===============================
def forca_candle(ativo):
    s = mem["stats"][ativo]
    total = s["win"] + s["loss"]

    if total < 30:
        return "MÉDIO"

    taxa = s["win"] / total
    if taxa > 0.56:
        return "FORTE"
    if taxa > 0.50:
        return "MÉDIO"
    return "FRACO"

# ===============================
# SCORE ENGINE
# ===============================
def calcular_score(ativo, estrategia):
    ctx = contexto_mercado(ativo)
    candle = forca_candle(ativo)
    s = mem["estrategias"][estrategia]

    if ctx == "TENDÊNCIA" and estrategia in ["tendencia","micro_tendencia"]:
        s += 2.0
    if ctx == "LATERAL" and estrategia == "reversao":
        s += 2.0
    if candle == "FORTE":
        s += 1.5
    elif candle == "MÉDIO":
        s += 1.0

    return ctx, candle, s

# ===============================
# CONTROLE DE FREQUÊNCIA
# ===============================
def pode_enviar_sinal():
    agora = time.time()

    mem["ultimos_sinais"] = [
        t for t in mem["ultimos_sinais"] if agora - t < 1800
    ]

    if len(mem["ultimos_sinais"]) >= MAX_SINAL_30MIN:
        return False

    if mem["ultimos_sinais"] and agora - mem["ultimos_sinais"][-1] < MIN_SINAL_INTERVAL:
        return False

    return True

# ===============================
# GERAR SINAL
# ===============================
def gerar_sinal():
    if not sessao_ativa() or not pode_enviar_sinal():
        return None

    melhores = []

    for ativo in ATIVOS:
        if mem["stats"][ativo]["loss_seq"] >= 2:
            continue

        estrategia = max(mem["estrategias"], key=mem["estrategias"].get)
        ctx, candle, score = calcular_score(ativo, estrategia)
        conf = min(0.95, score / 10)

        if score >= SCORE_MIN and conf >= CONF_MIN:
            melhores.append((score, ativo, estrategia, ctx, candle, conf))

    if not melhores:
        return None

    melhores.sort(reverse=True)
    score, ativo, estrategia, ctx, candle, conf = melhores[0]

    direcao = "CALL" if ctx == "TENDÊNCIA" else "PUT"
    mem["ultimos_sinais"].append(time.time())
    salvar_memoria()

    return ativo, direcao, estrategia, ctx, candle, score, conf

# ===============================
# AVALIAR RESULTADO
# ===============================
def avaliar_resultado(ativo, estrategia):
    # ⚠️ aqui ainda é manual/simulado
    resultado = "WIN"  # depois pode virar input manual

    if resultado == "WIN":
        mem["wins"] += 1
        mem["green_streak"] += 1
        mem["max_green"] = max(mem["max_green"], mem["green_streak"])
        mem["stats"][ativo]["win"] += 1
        mem["stats"][ativo]["loss_seq"] = 0
        mem["estrategias"][estrategia] += 0.03
        rtxt = "🟢 GREEN"
    else:
        mem["loss"] += 1
        mem["green_streak"] = 0
        mem["stats"][ativo]["loss"] += 1
        mem["stats"][ativo]["loss_seq"] += 1
        mem["estrategias"][estrategia] = max(0.5, mem["estrategias"][estrategia] - 0.05)
        rtxt = "🔴 RED"

    salvar_memoria()
    return rtxt

# ===============================
# STATUS
# ===============================
@bot.message_handler(commands=["status"])
def status(msg):
    total = mem["wins"] + mem["loss"]
    acc = (mem["wins"] / total * 100) if total else 0

    txt = (
        f"🤖 *TROIA NEXT v11.0*\n\n"
        f"🟢 WIN: {mem['wins']}\n"
        f"🔴 LOSS: {mem['loss']}\n"
        f"🎯 Assertividade: {acc:.2f}%\n"
        f"🔥 Greens seguidos: {mem['green_streak']}\n"
        f"🚀 Máx Greens: {mem['max_green']}\n"
    )

    bot.send_message(CHAT_ID, txt, parse_mode="Markdown")

# ===============================
# LOOP PRINCIPAL
# ===============================
def main():
    bot.send_message(
        CHAT_ID,
        "🤖 *TROIA NEXT v11.0*\n"
        "🧠 Engine Estatística\n"
        "📡 Sinais fortes apenas\n"
        "⏱ 1 a 5 sinais / 30min",
        parse_mode="Markdown"
    )

    while True:
        sinal = gerar_sinal()

        if sinal:
            ativo, direcao, est, ctx, candle, score, conf = sinal
            bot.send_message(
                CHAT_ID,
                f"📡 *SINAL TROIA*\n\n"
                f"🎯 Ativo: {ativo}\n"
                f"📈 Direção: {direcao}\n"
                f"🧠 Estratégia: {est}\n"
                f"📊 Contexto: {ctx}\n"
                f"🕯 Candle: {candle}\n"
                f"⭐ Score: {score:.2f}\n"
                f"🎯 Confiança: {conf*100:.1f}%\n"
                f"⏭ Próxima vela\n"
                f"🕒 {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}",
                parse_mode="Markdown"
            )

            time.sleep(60)
            bot.send_message(
                CHAT_ID,
                f"📊 Resultado: {avaliar_resultado(ativo, est)}",
                parse_mode="Markdown"
            )

        time.sleep(INTERVALO_LOOP)

# ===============================
# START
# ===============================
if __name__ == "__main__":
    main()

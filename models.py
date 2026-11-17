"""Model Initialization File

Configura el modelo LLM que usa el agente. Este archivo es la ÚNICA fuente de
verdad para elegir modelo: no hay MODEL ni MODEL_STRONG en el .env.

Default: Anthropic claude-haiku-4-5 (rápido y barato).

═══════════════════════════════════════════════════════════════════════════
  ⚠  IMPORTANT: instala el extra del proveedor ANTES de cambiarte
═══════════════════════════════════════════════════════════════════════════

  Proveedor             Comando de instalación        ¿Ya instalado?
  --------------------  ----------------------------  ---------------------
  Anthropic (default)   -                             sí (dependencia base)
  OpenAI                -                             sí (dependencia base)
  Azure OpenAI          uv sync --extra azure         no - instalar primero
  AWS Bedrock           uv sync --extra bedrock       no - instalar primero
  Google Vertex/Gemini  uv sync --extra google        no - instalar primero
  Ollama                uv sync --extra ollama        no - instalar primero

═══════════════════════════════════════════════════════════════════════════

Para cambiar de proveedor:
  1. Ejecuta el comando de instalación de arriba (si hace falta).
  2. Comenta las líneas del bloque "Modelos activos".
  3. Descomenta UNA sección del proveedor que quieras (una sola línea por rol:
     si descomentas dos, la última gana en silencio).
  4. Pon las variables del proveedor en `.env` (ver notas en cada bloque).

En el resto del código:
    from models import model, strong_model   # o MODELS["default"] / MODELS["strong"]
"""

import os  # noqa: F401  # usado en los ejemplos comentados de Kimi / OpenRouter
from pathlib import Path

from dotenv import dotenv_values
from langchain_ollama import ChatOllama

# El .env manda sobre lo que tengas exportado en la terminal, para que el modelo
# y la trazabilidad sean los mismos con `langgraph dev` y con scripts. Una
# variable vacía en el .env cuenta como no definida: no borra una clave del
# sistema.
for _key, _value in dotenv_values(Path(__file__).resolve().parent / ".env").items():
    if _value:
        os.environ[_key] = _value

from langchain.chat_models import init_chat_model  # noqa: E402  # tras cargar el .env

# ═══ Modelos activos ═════════════════════════════════════════════════════════
# Default: Anthropic claude-haiku-4-5, rápido y económico.
# Requiere ANTHROPIC_API_KEY en .env
model = init_chat_model("anthropic:claude-haiku-4-5", timeout=60, max_retries=2)

# Modelo con más criterio, para los pasos que lo necesitan (orquestación,
# revisión de cifras, redacción final).
strong_model = init_chat_model(
    "anthropic:claude-sonnet-5-5", timeout=120, max_retries=2
)

# ═══ Alternativas (comentar las activas arriba, descomentar UNA por rol) ═════
# model = init_chat_model("anthropic:claude-sonnet-5-5")
# model = init_chat_model("openai:gpt-6-luna", use_responses_api=True)
# strong_model = init_chat_model("openai:gpt-6.1-sol", use_responses_api=True)

# ═══ Modelos open source / hospedados alternativos ═══════════════════════════

# Groq: inferencia rápida y hospedada de Llama y otros (tiene capa gratuita)
# Instalar primero:  uv sync --extra groq
# Requiere GROQ_API_KEY en .env  (console.groq.com)
#
# model = init_chat_model("groq:llama-3.3-70b-versatile")

# Ollama: modelos locales, sin API key
# Instalar primero:  uv sync --extra ollama   y la app de https://ollama.com
# Descargar primero un modelo, p. ej.:  ollama pull qwen2.5:7b
# Ojo: los modelos pequeños (7-8B) fallan llamando herramientas o inventan
# nombres; deja strong_model en un modelo hospedado.
#
#model = ChatOllama(
#    model="ministral-3:latest",
#        temperature=0.4
#)

# Kimi (Moonshot AI): API hospedada compatible con OpenAI
# No necesita instalación extra (langchain-openai es dependencia base)
# Requiere KIMI_API_KEY en .env  (platform.moonshot.cn)
#
# from langchain_openai import ChatOpenAI
# model = ChatOpenAI(model="moonshot-v1-8k", base_url="https://api.moonshot.cn/v1", api_key=os.environ["KIMI_API_KEY"])

# OpenRouter: modelos open source hospedados vía API compatible con OpenAI
# Hay modelos gratuitos; regístrate en openrouter.ai y saca una API key
# Requiere OPENROUTER_API_KEY en .env
#
# from langchain_openai import ChatOpenAI
# model = ChatOpenAI(model="nvidia/nemotron-3-ultra-550b-a55b:free", base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])


# ═══ Modelos de proveedor cloud (requieren extra, ver tabla) ═════════════════
# ─── Azure OpenAI ─────────────────────────────────────────────────────────────
# Instalar primero:  uv sync --extra azure
# Requiere AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT y OPENAI_API_VERSION en .env
# El nombre del deployment se pone aquí, no en el .env
#
# from langchain_openai import AzureChatOpenAI
# model = AzureChatOpenAI(azure_deployment="gpt-4.1", api_version="2024-12-01-preview")


# ─── AWS Bedrock ──────────────────────────────────────────────────────────────
# Instalar primero:  uv sync --extra bedrock
# Requiere AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY en .env
# La región se pone aquí, no en el .env
#
# from langchain_aws import ChatBedrockConverse
# model = ChatBedrockConverse(model_id="anthropic.claude-sonnet-4-6", region_name="us-east-1")


# ─── Google Gemini ────────────────────────────────────────────────────────────
# Instalar primero:  uv sync --extra google
# Requiere GOOGLE_API_KEY en .env
#
#model = init_chat_model(
#    model="google_genai:gemini-3.5-flash",
#    temperature=0.4
#    )


# ═══ Acceso por rol ══════════════════════════════════════════════════════════
# Para darle un modelo distinto a cada agente sin volver a tocar este archivo:
#     from models import MODELS
#     create_deep_agent(model=MODELS["default"], subagents=[{"model": MODELS["strong"], ...}])
MODELS = {"default": model, "strong": strong_model}

# Override puntual, útil para comparar dos modelos con el mismo set de pruebas,
# sin editar nada aquí:
#     MODEL_OVERRIDE=openai:gpt-6.1-sol uv run langgraph dev
#
# _override = os.getenv("MODEL_OVERRIDE")
# if _override:
#     model = init_chat_model(_override, timeout=60, max_retries=2)
#     strong_model = init_chat_model(_override, timeout=120, max_retries=2)
#     MODELS = {"default": model, "strong": strong_model}

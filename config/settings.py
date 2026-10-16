import os
from pathlib import Path

from dotenv import load_dotenv


# Obtiene la carpeta principal de EvU3 desde config/settings.py.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Carga .env desde esa carpeta, independientemente de dónde
# se ejecute el programa. No reemplaza variables del entorno existentes.
load_dotenv(PROJECT_ROOT / ".env")

# La clave se lee del entorno y nunca se imprime.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Modelos elegidos para cada tipo de contenido.
MODELO_TEXTO = os.getenv("MODELO_TEXTO", "gpt-6-luna").strip()
MODELO_IMAGEN = os.getenv("MODELO_IMAGEN", "gpt-image-1-mini").strip()
MODELO_AUDIO = os.getenv("MODELO_AUDIO", "gpt-4o-mini-tts").strip()

# Ajustes de imagen para reducir el costo por generación.
CALIDAD_IMAGEN = os.getenv("CALIDAD_IMAGEN", "low").strip()
TAMANO_IMAGEN = os.getenv("TAMANO_IMAGEN", "1024x1024").strip()

# Voz utilizada para la narración.
VOZ_AUDIO = os.getenv("VOZ_AUDIO", "alloy").strip()

# Por defecto, las solicitudes reales están deshabilitadas.
# Solo el valor "true" activa esta opción.
HABILITAR_API_REAL = (
    os.getenv("HABILITAR_API_REAL", "false").strip().lower() == "true"
)

# Define las rutas de salida sin crear todavía las carpetas.
OUTPUT_DIR = PROJECT_ROOT / "resultados"
TEXTO_DIR = OUTPUT_DIR / "texto"
IMAGENES_DIR = OUTPUT_DIR / "imagenes"
AUDIO_DIR = OUTPUT_DIR / "audio"


def validar_configuracion():
    """Comprueba los valores locales sin consultar la API."""

    # Evita modelos vacíos por errores al editar .env.
    if not all([MODELO_TEXTO, MODELO_IMAGEN, MODELO_AUDIO]):
        raise ValueError("Los nombres de los modelos no pueden estar vacíos.")

    # Mantiene los ajustes económicos acordados para este proyecto.
    if CALIDAD_IMAGEN != "low":
        raise ValueError("Usa CALIDAD_IMAGEN=low para esta etapa.")

    if TAMANO_IMAGEN != "1024x1024":
        raise ValueError("Usa TAMANO_IMAGEN=1024x1024 para esta etapa.")

    if not VOZ_AUDIO:
        raise ValueError("Debes indicar una voz para la narración.")


def validar_acceso_real():
    """Bloquea las generaciones hasta que se habiliten explícitamente."""

    validar_configuracion()

    if not HABILITAR_API_REAL:
        raise ValueError(
            "La API real está deshabilitada. "
            "No se enviará ninguna solicitud."
        )

    if not OPENAI_API_KEY or OPENAI_API_KEY == "pega_aqui_tu_clave":
        raise ValueError("Configura tu clave de OpenAI en .env.")

    # Esta comprobación solo verifica la presencia de una clave.
    # Su validez, permisos y saldo se comprueban al consultar OpenAI.
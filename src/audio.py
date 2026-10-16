from pathlib import Path
from uuid import uuid4

from openai import (
    OpenAI,
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)

from config import settings


def generar_audio(texto, carpeta_destino=None):
    """Convierte el cuento en narración MP3 y devuelve su ubicación."""

    # Valida el texto antes de crear el cliente o consumir la API.
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("Debes indicar el texto que deseas narrar.")

    texto = texto.strip()

    # Mantiene acotada la longitud de la narración y su consumo.
    # Este límite es del proyecto, no un presupuesto en dólares.
    if len(texto) > 3000:
        raise ValueError("El texto no debe superar los 3000 caracteres.")

    # Detiene la operación mientras la API real esté deshabilitada.
    settings.validar_acceso_real()

    carpeta = (
        settings.AUDIO_DIR
        if carpeta_destino is None
        else Path(carpeta_destino)
    )

    # Prepara la carpeta antes de solicitar una narración de pago.
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise RuntimeError(
            "No se pudo preparar la carpeta de audio."
        ) from error

    try:
        with OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url="https://api.openai.com/v1",
            timeout=120,
            max_retries=0,
        ) as cliente:
            respuesta = cliente.audio.speech.create(
                model=settings.MODELO_AUDIO,
                voice=settings.VOZ_AUDIO,
                input=texto,

                # Indica cómo narrar el cuento para estudiantes.
                instructions=(
                    "Narra en español con voz cálida, "
                    "pronunciación clara y ritmo tranquilo para niños."
                ),

                # Solicita el formato exigido por la evaluación.
                response_format="mp3",
            )

            # Lee los bytes mientras el cliente permanece abierto.
            contenido = respuesta.read()

        if not isinstance(contenido, bytes) or not contenido:
            raise RuntimeError("OpenAI no devolvió contenido de audio.")

        # Evita reemplazar narraciones anteriores.
        ruta = carpeta / f"narracion_{uuid4().hex[:12]}.mp3"

        try:
            ruta.write_bytes(contenido)
        except OSError as error:
            raise RuntimeError(
                "El audio se generó, pero no se pudo guardar."
            ) from error

        return ruta

    except AuthenticationError as error:
        raise RuntimeError("La clave de OpenAI no es válida.") from error

    except PermissionDeniedError as error:
        raise RuntimeError(
            "Tu cuenta o clave no tiene acceso al modelo de audio."
        ) from error

    except RateLimitError as error:
        raise RuntimeError(
            "Se alcanzó un límite de uso o no hay saldo disponible."
        ) from error

    except APIConnectionError as error:
        raise RuntimeError("No se pudo conectar con OpenAI.") from error

    except APIStatusError as error:
        raise RuntimeError(
            f"OpenAI rechazó la solicitud: HTTP {error.status_code}."
        ) from error
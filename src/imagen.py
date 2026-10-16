import base64
import binascii
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


def generar_imagen(descripcion, carpeta_destino=None):
    """Genera una ilustración PNG y devuelve su ubicación."""

    # Valida la escena antes de crear el cliente o consumir la API.
    if not isinstance(descripcion, str) or not descripcion.strip():
        raise ValueError("Debes indicar una descripción de la escena.")

    descripcion = descripcion.strip()

    if len(descripcion) > 1000:
        raise ValueError("La descripción no debe superar 1000 caracteres.")

    # Bloquea las solicitudes mientras .env mantenga la API deshabilitada.
    settings.validar_acceso_real()

    carpeta = (
        settings.IMAGENES_DIR
        if carpeta_destino is None
        else Path(carpeta_destino)
    )

    # Prepara la carpeta antes de solicitar una imagen de pago.
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise RuntimeError(
            "No se pudo preparar la carpeta de imágenes."
        ) from error

    prompt = (
        "Ilustración infantil para educación básica. "
        "Personajes amigables, colores suaves y sin texto escrito. "
        f"Escena: {descripcion}"
    )

    try:
        with OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url="https://api.openai.com/v1",
            timeout=120,
            max_retries=0,
        ) as cliente:
            respuesta = cliente.images.generate(
                model=settings.MODELO_IMAGEN,
                prompt=prompt,

                # Solicita una sola imagen con los ajustes económicos.
                n=1,
                quality=settings.CALIDAD_IMAGEN,
                size=settings.TAMANO_IMAGEN,

                # El formato solicitado coincide con la extensión final.
                output_format="png",
            )

        if not respuesta.data or not respuesta.data[0].b64_json:
            raise RuntimeError("OpenAI no devolvió una imagen.")

        # Convierte la imagen codificada en base64 a bytes.
        try:
            contenido = base64.b64decode(
                respuesta.data[0].b64_json,
                validate=True,
            )
        except (binascii.Error, ValueError) as error:
            raise RuntimeError(
                "La imagen recibida tiene una codificación inválida."
            ) from error

        # Comprueba la firma del formato PNG.
        # Esto identifica el formato, pero no valida toda la imagen.
        if not contenido.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("La respuesta no tiene formato PNG.")

        # Usa un identificador para no reemplazar imágenes anteriores.
        ruta = carpeta / f"ilustracion_{uuid4().hex[:12]}.png"

        try:
            ruta.write_bytes(contenido)
        except OSError as error:
            raise RuntimeError(
                "La imagen se generó, pero no se pudo guardar."
            ) from error

        return ruta

    except AuthenticationError as error:
        raise RuntimeError("La clave de OpenAI no es válida.") from error

    except PermissionDeniedError as error:
        raise RuntimeError(
            "Tu cuenta o clave no tiene acceso al modelo de imágenes."
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
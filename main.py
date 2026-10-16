from uuid import uuid4

from config import settings
from src.texto import generar_cuento
from src.imagen import generar_imagen
from src.audio import generar_audio


def main():
    """Solicita los datos y genera el material educativo."""

    try:
        # Comprueba la configuración local sin consultar OpenAI.
        settings.validar_configuracion()

        tema = input("Tema del cuento: ").strip()
        nivel = int(input("Curso (1 a 4 básico): "))
        descripcion = input("Descripción de la ilustración: ").strip()

        # Valida todas las entradas antes de consumir la API.
        if not tema or len(tema) > 200:
            raise ValueError("El tema debe tener entre 1 y 200 caracteres.")

        if not 1 <= nivel <= 4:
            raise ValueError("El curso debe estar entre 1 y 4.")

        if not descripcion or len(descripcion) > 1000:
            raise ValueError(
                "La descripción debe tener entre 1 y 1000 caracteres."
            )

        # Detiene el flujo si la API sigue deshabilitada o falta la clave.
        settings.validar_acceso_real()

        # Solicita una confirmación antes de las operaciones de pago.
        print("\nSe generarán un cuento, una imagen y una narración.")
        print("Estas operaciones consumen saldo de la API de OpenAI.")
        confirmacion = input("Escribe GENERAR para continuar: ").strip()

        if confirmacion != "GENERAR":
            print("Operación cancelada. No se enviaron solicitudes.")
            return

        # Prepara las carpetas antes de solicitar contenido.
        for carpeta in [
            settings.TEXTO_DIR,
            settings.IMAGENES_DIR,
            settings.AUDIO_DIR,
        ]:
            carpeta.mkdir(parents=True, exist_ok=True)

        # Genera y guarda el cuento con un nombre único.
        print("\nGenerando cuento...")
        cuento = generar_cuento(tema, nivel)

        ruta_texto = (
            settings.TEXTO_DIR / f"cuento_{uuid4().hex[:12]}.txt"
        )
        ruta_texto.write_text(cuento, encoding="utf-8")

        print("\nCUENTO")
        print(cuento)
        print(f"\nTexto guardado: {ruta_texto}")

        # Comprueba el límite de audio antes de generar la imagen.
        # Si el cuento es demasiado largo, conserva el texto y se detiene.
        if len(cuento) > 3000:
            raise ValueError(
                "El cuento supera el límite de narración. "
                "El texto quedó guardado; no se generaron imagen ni audio."
            )

        print("\nGenerando ilustración...")
        ruta_imagen = generar_imagen(descripcion)
        print(f"Imagen guardada: {ruta_imagen}")

        # Utiliza el mismo cuento como entrada para la narración.
        print("\nGenerando narración con una voz creada por IA...")
        ruta_audio = generar_audio(cuento)
        print(f"Audio guardado: {ruta_audio}")

        print("\nMaterial educativo generado correctamente.")

    except ValueError as error:
        print(f"No se pudo continuar: {error}")

    except (OSError, RuntimeError) as error:
        # Si un paso falla, los archivos anteriores se conservan.
        # Las solicitudes completadas pueden haber consumido saldo.
        print(f"No se pudo completar el proceso: {error}")
        print("Revisa los archivos guardados antes de repetir.")


# Importar este archivo no inicia la aplicación.
if __name__ == "__main__":
    main()
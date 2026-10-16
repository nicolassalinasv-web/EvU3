import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from config import settings
from src.audio import generar_audio


class TestGenerarAudio(unittest.TestCase):
    """Comprueba la solicitud y el guardado de audio sin conexión."""

    def setUp(self):
        # Cada prueba utiliza una carpeta temporal independiente.
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.carpeta = Path(temporal.name) / "audio"

        # Sustituye el cliente de OpenAI antes de ejecutar la función.
        cambio = patch("src.audio.OpenAI")
        self.constructor = cambio.start()
        self.addCleanup(cambio.stop)

        self.cliente = (
            self.constructor.return_value
            .__enter__.return_value
        )

        # Estos bytes sirven para probar transporte y guardado.
        # No representan un MP3 reproducible ni una narración real.
        self.contenido = b"contenido-de-audio-de-prueba"
        self.cliente.audio.speech.create.return_value.read.return_value = (
            self.contenido
        )

        # Cambia la configuración solo durante la prueba.
        # El cliente sigue sustituido y no puede conectarse a la API.
        for nombre, valor in [
            ("HABILITAR_API_REAL", True),
            ("OPENAI_API_KEY", "clave-ficticia-local"),
        ]:
            cambio = patch.object(settings, nombre, valor)
            cambio.start()
            self.addCleanup(cambio.stop)

    def test_solicitud_y_guardado(self):
        ruta = generar_audio("  Un conejo ayudó a su amiga.  ", self.carpeta)

        # Comprueba la carpeta, extensión y bytes guardados.
        self.assertEqual(ruta.parent, self.carpeta)
        self.assertEqual(ruta.suffix, ".mp3")
        self.assertEqual(ruta.read_bytes(), self.contenido)

        # Verifica el texto limpio y los parámetros de narración.
        solicitud = self.cliente.audio.speech.create
        solicitud.assert_called_once()
        datos = solicitud.call_args.kwargs

        self.assertEqual(datos["model"], settings.MODELO_AUDIO)
        self.assertEqual(datos["voice"], settings.VOZ_AUDIO)
        self.assertEqual(datos["input"], "Un conejo ayudó a su amiga.")
        self.assertEqual(datos["response_format"], "mp3")
        self.assertIn("español", datos["instructions"])

    def test_texto_invalido(self):
        for texto in ["", "   ", None, 123, "a" * 3001]:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    generar_audio(texto, self.carpeta)

        # Los datos inválidos no deben crear clientes ni carpetas.
        self.constructor.assert_not_called()
        self.assertFalse(self.carpeta.exists())

    def test_api_deshabilitada(self):
        with patch.object(settings, "HABILITAR_API_REAL", False):
            with self.assertRaisesRegex(ValueError, "deshabilitada"):
                generar_audio("Un cuento breve.", self.carpeta)

        self.constructor.assert_not_called()
        self.assertFalse(self.carpeta.exists())

    def test_respuesta_invalida(self):
        # Rechaza respuestas vacías o que no contengan bytes.
        for contenido in [b"", None, "audio", 123]:
            with self.subTest(contenido=contenido):
                self.cliente.audio.speech.create.return_value.read.return_value = (
                    contenido
                )

                with self.assertRaisesRegex(RuntimeError, "contenido de audio"):
                    generar_audio("Un cuento breve.", self.carpeta)

        self.assertEqual(list(self.carpeta.iterdir()), [])

    def test_error_al_preparar_carpeta(self):
        # Simula un fallo antes de solicitar la narración.
        with patch.object(
            Path,
            "mkdir",
            side_effect=PermissionError("Acceso denegado"),
        ):
            with self.assertRaisesRegex(RuntimeError, "preparar la carpeta"):
                generar_audio("Un cuento breve.", self.carpeta)

        self.constructor.assert_not_called()

    def test_error_al_guardar(self):
        # Simula un fallo de escritura después de recibir el audio.
        with patch.object(
            Path,
            "write_bytes",
            side_effect=PermissionError("Acceso denegado"),
        ):
            with self.assertRaisesRegex(RuntimeError, "no se pudo guardar"):
                generar_audio("Un cuento breve.", self.carpeta)

    def test_no_reemplaza_audio_anterior(self):
        primera = generar_audio("Primer cuento.", self.carpeta)
        segunda = generar_audio("Segundo cuento.", self.carpeta)

        self.assertNotEqual(primera, segunda)
        self.assertTrue(primera.is_file())
        self.assertTrue(segunda.is_file())

    def test_lee_audio_con_cliente_abierto(self):
        # Verifica el orden: el audio se lee antes de cerrar el cliente.
        eventos = []

        self.constructor.return_value.__enter__.side_effect = (
            lambda: self.cliente
        )

        def leer():
            eventos.append("leer")
            return self.contenido

        def cerrar(*args):
            eventos.append("cerrar")
            return False

        self.cliente.audio.speech.create.return_value = SimpleNamespace(
            read=leer
        )
        self.constructor.return_value.__exit__.side_effect = cerrar

        generar_audio("Un cuento breve.", self.carpeta)

        self.assertEqual(eventos, ["leer", "cerrar"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
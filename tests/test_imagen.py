import base64
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from config import settings
from src.imagen import generar_imagen


class TestGenerarImagen(unittest.TestCase):
    """Comprueba la solicitud y el guardado con respuestas locales."""

    def setUp(self):
        # Cada prueba guarda sus archivos en una carpeta temporal.
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.carpeta = Path(temporal.name) / "imagenes"

        # Sustituye el cliente antes de que pueda crearse una conexión.
        cambio = patch("src.imagen.OpenAI")
        self.constructor = cambio.start()
        self.addCleanup(cambio.stop)

        self.cliente = (
            self.constructor.return_value
            .__enter__.return_value
        )

        # Imagen PNG de un píxel, utilizada únicamente como ejemplo.
        self.imagen_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0"
            "lEQVR42mP8/x8AAwMCAO+jwioAAAAASUVORK5CYII="
        )

        self.cliente.images.generate.return_value = SimpleNamespace(
            data=[SimpleNamespace(b64_json=self.imagen_base64)]
        )

        # Habilita el modo real solo en memoria, con el cliente sustituido.
        for nombre, valor in [
            ("HABILITAR_API_REAL", True),
            ("OPENAI_API_KEY", "clave-ficticia-local"),
        ]:
            cambio = patch.object(settings, nombre, valor)
            cambio.start()
            self.addCleanup(cambio.stop)

    def test_solicitud_y_guardado(self):
        ruta = generar_imagen("  Un bosque  ", self.carpeta)

        # Comprueba la ubicación, extensión y contenido guardado.
        self.assertEqual(ruta.parent, self.carpeta)
        self.assertEqual(ruta.suffix, ".png")
        self.assertEqual(
            ruta.read_bytes(),
            base64.b64decode(self.imagen_base64),
        )

        # Comprueba que solicita una única imagen de calidad baja.
        solicitud = self.cliente.images.generate
        solicitud.assert_called_once()
        datos = solicitud.call_args.kwargs

        self.assertEqual(datos["model"], settings.MODELO_IMAGEN)
        self.assertEqual(datos["n"], 1)
        self.assertEqual(datos["quality"], "low")
        self.assertEqual(datos["size"], "1024x1024")
        self.assertEqual(datos["output_format"], "png")
        self.assertIn("Escena: Un bosque", datos["prompt"])

    def test_descripcion_invalida(self):
        for descripcion in ["", "   ", None, 123, "a" * 1001]:
            with self.subTest(descripcion=descripcion):
                with self.assertRaises(ValueError):
                    generar_imagen(descripcion, self.carpeta)

        # No crea clientes ni carpetas cuando los datos son inválidos.
        self.constructor.assert_not_called()
        self.assertFalse(self.carpeta.exists())

    def test_api_deshabilitada(self):
        with patch.object(settings, "HABILITAR_API_REAL", False):
            with self.assertRaisesRegex(ValueError, "deshabilitada"):
                generar_imagen("Un bosque", self.carpeta)

        self.constructor.assert_not_called()
        self.assertFalse(self.carpeta.exists())

    def test_respuesta_sin_imagen(self):
        self.cliente.images.generate.return_value = SimpleNamespace(
            data=[]
        )

        with self.assertRaisesRegex(RuntimeError, "no devolvió"):
            generar_imagen("Un bosque", self.carpeta)

        self.assertEqual(list(self.carpeta.iterdir()), [])

    def test_base64_invalido(self):
        self.cliente.images.generate.return_value = SimpleNamespace(
            data=[SimpleNamespace(b64_json="%%%")]
        )

        with self.assertRaisesRegex(RuntimeError, "codificación"):
            generar_imagen("Un bosque", self.carpeta)

    def test_contenido_no_png(self):
        # Una respuesta base64 válida puede contener otro formato.
        contenido = base64.b64encode(b"esto no es PNG").decode("ascii")
        self.cliente.images.generate.return_value = SimpleNamespace(
            data=[SimpleNamespace(b64_json=contenido)]
        )

        with self.assertRaisesRegex(RuntimeError, "formato PNG"):
            generar_imagen("Un bosque", self.carpeta)

    def test_error_al_guardar(self):
        # Simula un problema de escritura sin alterar permisos reales.
        with patch.object(
            Path,
            "write_bytes",
            side_effect=PermissionError("Acceso denegado"),
        ):
            with self.assertRaisesRegex(RuntimeError, "no se pudo guardar"):
                generar_imagen("Un bosque", self.carpeta)

    def test_no_reemplaza_imagen_anterior(self):
        # Dos generaciones deben utilizar nombres diferentes.
        primera = generar_imagen("Un bosque", self.carpeta)
        segunda = generar_imagen("Un río", self.carpeta)

        self.assertNotEqual(primera, segunda)
        self.assertTrue(primera.is_file())
        self.assertTrue(segunda.is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
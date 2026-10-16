import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config import settings
from main import main


class TestAplicacion(unittest.TestCase):
    """Comprueba el flujo completo con las generaciones sustituidas."""

    def setUp(self):
        # Cada prueba utiliza carpetas temporales.
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.carpeta = Path(temporal.name)

        # Sustituye las tres funciones antes de ejecutar main().
        # Ninguna prueba puede generar contenido de pago.
        sustituciones = [
            ("main.generar_cuento", "cuento"),
            ("main.generar_imagen", "imagen"),
            ("main.generar_audio", "audio"),
        ]

        for destino, atributo in sustituciones:
            cambio = patch(destino)
            setattr(self, atributo, cambio.start())
            self.addCleanup(cambio.stop)

        self.cuento.return_value = "Un conejo ayudó a una tortuga."
        self.imagen.return_value = self.carpeta / "imagen.png"
        self.audio.return_value = self.carpeta / "audio.mp3"

        # Cambia configuración y rutas solo durante la prueba.
        valores = {
            "HABILITAR_API_REAL": True,
            "OPENAI_API_KEY": "clave-ficticia-local",
            "TEXTO_DIR": self.carpeta / "texto",
            "IMAGENES_DIR": self.carpeta / "imagenes",
            "AUDIO_DIR": self.carpeta / "audio",
        }

        for nombre, valor in valores.items():
            cambio = patch.object(settings, nombre, valor)
            cambio.start()
            self.addCleanup(cambio.stop)

    def ejecutar(self, entradas):
        # Simula lo escrito en la terminal y captura los mensajes.
        with (
            patch("builtins.input", side_effect=entradas),
            patch("builtins.print") as imprimir,
        ):
            main()

        return imprimir

    def test_flujo_completo(self):
        self.ejecutar([
            "La amistad",
            "3",
            "Un conejo y una tortuga",
            "GENERAR",
        ])

        # Comprueba los datos enviados a cada función.
        self.cuento.assert_called_once_with("La amistad", 3)
        self.imagen.assert_called_once_with("Un conejo y una tortuga")
        self.audio.assert_called_once_with(self.cuento.return_value)

        # main() guarda el cuento; las otras funciones guardan sus archivos.
        textos = list((self.carpeta / "texto").glob("cuento_*.txt"))
        self.assertEqual(len(textos), 1)
        self.assertEqual(
            textos[0].read_text(encoding="utf-8"),
            self.cuento.return_value,
        )

    def test_cancelacion(self):
        self.ejecutar(["La amistad", "3", "Un bosque", "CANCELAR"])

        # Cancelar debe impedir las tres generaciones.
        self.cuento.assert_not_called()
        self.imagen.assert_not_called()
        self.audio.assert_not_called()
        self.assertEqual(list(self.carpeta.iterdir()), [])

    def test_curso_invalido(self):
        self.ejecutar(["La amistad", "5", "Un bosque"])

        self.cuento.assert_not_called()
        self.imagen.assert_not_called()
        self.audio.assert_not_called()

    def test_curso_no_numerico(self):
        self.ejecutar(["La amistad", "tres"])

        self.cuento.assert_not_called()
        self.imagen.assert_not_called()
        self.audio.assert_not_called()

    def test_api_deshabilitada(self):
        with patch.object(settings, "HABILITAR_API_REAL", False):
            self.ejecutar(["La amistad", "3", "Un bosque"])

        self.cuento.assert_not_called()
        self.imagen.assert_not_called()
        self.audio.assert_not_called()
        self.assertEqual(list(self.carpeta.iterdir()), [])

    def test_fallo_del_cuento_detiene_el_flujo(self):
        self.cuento.side_effect = RuntimeError("Conexión fallida")

        imprimir = self.ejecutar([
            "La amistad", "3", "Un bosque", "GENERAR"
        ])

        self.imagen.assert_not_called()
        self.audio.assert_not_called()

        # Comprueba que el usuario recibe información del problema.
        mensajes = " ".join(
            str(llamada.args[0])
            for llamada in imprimir.call_args_list
            if llamada.args
        )
        self.assertIn("Conexión fallida", mensajes)

    def test_fallo_de_imagen_conserva_texto(self):
        self.imagen.side_effect = RuntimeError("Error de imagen")

        self.ejecutar(["La amistad", "3", "Un bosque", "GENERAR"])

        self.audio.assert_not_called()
        textos = list((self.carpeta / "texto").glob("cuento_*.txt"))
        self.assertEqual(len(textos), 1)

    def test_cuento_largo_detiene_imagen_y_audio(self):
        self.cuento.return_value = "a" * 3001

        self.ejecutar(["La amistad", "3", "Un bosque", "GENERAR"])

        self.imagen.assert_not_called()
        self.audio.assert_not_called()

        # Conserva el cuento aunque no pueda narrarlo.
        textos = list((self.carpeta / "texto").glob("cuento_*.txt"))
        self.assertEqual(len(textos), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
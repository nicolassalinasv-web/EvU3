import unittest
from types import SimpleNamespace
from unittest.mock import patch

from config import settings
from src.texto import generar_cuento


class TestGenerarCuento(unittest.TestCase):
    """Comprueba el generador de cuentos sin conectarse a OpenAI."""

    def setUp(self):
        # Sustituye OpenAI en el módulo donde se utiliza.
        # Así, incluso con el modo real habilitado durante una prueba,
        # nunca se crea un cliente de red.
        sustituto = patch("src.texto.OpenAI")
        self.constructor = sustituto.start()
        self.addCleanup(sustituto.stop)

        # Obtiene el cliente simulado utilizado dentro del bloque with.
        self.cliente = (
            self.constructor.return_value
            .__enter__.return_value
        )

        # Prepara una respuesta local con la estructura necesaria.
        self.cliente.responses.create.return_value = SimpleNamespace(
            status="completed",
            output_text="  Un conejo ayudó a su amiga tortuga.  ",
        )

    def habilitar_modo_de_prueba(self):
        # Cambia temporalmente la configuración solo dentro de esta prueba.
        # addCleanup restaura los valores originales al terminar.
        for nombre, valor in [
            ("HABILITAR_API_REAL", True),
            ("OPENAI_API_KEY", "clave-ficticia-local"),
        ]:
            cambio = patch.object(settings, nombre, valor)
            cambio.start()
            self.addCleanup(cambio.stop)

    def test_solicitud_y_respuesta(self):
        self.habilitar_modo_de_prueba()

        cuento = generar_cuento("  La amistad  ", 3)

        # Comprueba la lectura del texto y la eliminación de espacios.
        self.assertEqual(
            cuento, "Un conejo ayudó a su amiga tortuga."
        )

        # Verifica los controles de consumo y el tema enviado.
        solicitud = self.cliente.responses.create
        solicitud.assert_called_once()
        datos = solicitud.call_args.kwargs

        self.assertEqual(datos["model"], settings.MODELO_TEXTO)
        self.assertEqual(datos["input"], "La amistad")
        self.assertEqual(datos["max_output_tokens"], 600)
        self.assertEqual(datos["reasoning"], {"effort": "none"})
        self.assertFalse(datos["store"])
        self.assertIn("3° básico", datos["instructions"])

    def test_datos_invalidos(self):
        # Los datos incorrectos deben rechazarse antes de crear el cliente.
        casos = [
            ("", 3),
            ("   ", 3),
            (None, 3),
            ("a" * 201, 3),
            ("La amistad", 0),
            ("La amistad", 5),
            ("La amistad", "3"),
            ("La amistad", True),
        ]

        for tema, nivel in casos:
            with self.subTest(tema=tema, nivel=nivel):
                with self.assertRaises(ValueError):
                    generar_cuento(tema, nivel)

        self.constructor.assert_not_called()

    def test_api_deshabilitada(self):
        # Confirma que false bloquea la operación antes de crear el cliente.
        with patch.object(settings, "HABILITAR_API_REAL", False):
            with self.assertRaisesRegex(ValueError, "deshabilitada"):
                generar_cuento("La amistad", 3)

        self.constructor.assert_not_called()

    def test_clave_ausente(self):
        with (
            patch.object(settings, "HABILITAR_API_REAL", True),
            patch.object(settings, "OPENAI_API_KEY", ""),
        ):
            with self.assertRaisesRegex(ValueError, "clave"):
                generar_cuento("La amistad", 3)

        self.constructor.assert_not_called()

    def test_cuento_incompleto(self):
        self.habilitar_modo_de_prueba()

        # Simula una respuesta cortada por el límite de salida.
        self.cliente.responses.create.return_value = SimpleNamespace(
            status="incomplete",
            output_text="Había una vez...",
        )

        with self.assertRaisesRegex(RuntimeError, "no se completó"):
            generar_cuento("La amistad", 3)

    def test_respuesta_vacia(self):
        self.habilitar_modo_de_prueba()

        self.cliente.responses.create.return_value = SimpleNamespace(
            status="completed",
            output_text="   ",
        )

        with self.assertRaisesRegex(RuntimeError, "no devolvió"):
            generar_cuento("La amistad", 3)


# Permite ejecutar estas pruebas como módulo desde la raíz de EvU3.
if __name__ == "__main__":
    unittest.main(verbosity=2)
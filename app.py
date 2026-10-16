import streamlit as st
from uuid import uuid4

from config import settings
from src.texto import generar_cuento
from src.imagen import generar_imagen
from src.audio import generar_audio


# Configura el título y el ancho de la página.
st.set_page_config(
    page_title="Material educativo",
    page_icon="📚",
    layout="centered",
)

st.title("📚 Generador de material educativo")
st.write(
    "Crea un cuento para Lenguaje, una ilustración "
    "y una narración para estudiantes de 1.º a 4.º básico."
)

# Conserva los resultados entre las actualizaciones de la página.
# Así, descargar un archivo no vuelve a generar contenido.
if "material" not in st.session_state:
    st.session_state.material = {}

if settings.HABILITAR_API_REAL:
    st.warning(
        "Generar material consume saldo de la API de OpenAI."
    )
else:
    st.info(
        "La API está deshabilitada. Puedes revisar la interfaz "
        "sin generar contenido."
    )

# El formulario reúne las entradas en una única acción.
with st.form("formulario_material"):
    tema = st.text_input(
        "Tema del cuento",
        max_chars=200,
        placeholder="La amistad",
    )

    nivel = st.selectbox(
        "Curso",
        options=[1, 2, 3, 4],
        format_func=lambda curso: f"{curso}° básico",
    )

    descripcion = st.text_area(
        "Descripción de la ilustración",
        max_chars=1000,
        placeholder=(
            "Dos niños compartiendo lápices de colores "
            "en una sala de clases."
        ),
    )

    acepta_costo = st.checkbox(
        "Entiendo que esta generación consume saldo de OpenAI."
    )

    generar = st.form_submit_button(
        "Generar material",
        disabled=not settings.HABILITAR_API_REAL,
    )

# Las llamadas a OpenAI ocurren únicamente al enviar el formulario.
if generar:
    try:
        tema = tema.strip()
        descripcion = descripcion.strip()

        # Valida las entradas y la confirmación antes de consumir la API.
        if not tema:
            raise ValueError("Indica el tema del cuento.")

        if not descripcion:
            raise ValueError("Describe la escena de la ilustración.")

        if not acepta_costo:
            raise ValueError("Debes confirmar el consumo de saldo.")

        settings.validar_acceso_real()

        # Prepara las carpetas antes de solicitar contenido.
        for carpeta in [
            settings.TEXTO_DIR,
            settings.IMAGENES_DIR,
            settings.AUDIO_DIR,
        ]:
            carpeta.mkdir(parents=True, exist_ok=True)

        # Inicia un resultado nuevo solo después de validar las entradas.
        # Conserva los pasos completados si una operación posterior falla.
        st.session_state.material = {}

        with st.spinner("Generando cuento..."):
            cuento = generar_cuento(tema, nivel)

            ruta_texto = (
                settings.TEXTO_DIR
                / f"cuento_{uuid4().hex[:12]}.txt"
            )
            ruta_texto.write_text(cuento, encoding="utf-8")

            st.session_state.material["cuento"] = cuento
            st.session_state.material["ruta_texto"] = ruta_texto

        if len(cuento) > 3000:
            raise ValueError(
                "El cuento quedó guardado, pero supera el límite "
                "de narración. No se generaron imagen ni audio."
            )

        with st.spinner("Generando ilustración..."):
            ruta_imagen = generar_imagen(descripcion)

            # Conserva los bytes para mostrar y descargar sin otra consulta.
            st.session_state.material["imagen"] = (
                ruta_imagen.read_bytes()
            )

        with st.spinner("Generando narración..."):
            ruta_audio = generar_audio(cuento)
            st.session_state.material["audio"] = (
                ruta_audio.read_bytes()
            )

        st.success("Material educativo generado correctamente.")

    except (ValueError, OSError, RuntimeError) as error:
        st.error(str(error))
        st.caption(
            "Los pasos completados pueden haber consumido saldo. "
            "Revisa los resultados antes de generar nuevamente."
        )

# Muestra los resultados conservados, sin realizar llamadas a OpenAI.
material = st.session_state.material

if "cuento" in material:
    st.subheader("Cuento")
    st.markdown(material["cuento"])

    st.download_button(
        "Descargar cuento TXT",
        data=material["cuento"].encode("utf-8"),
        file_name="cuento.txt",
        mime="text/plain",
    )

if "imagen" in material:
    st.subheader("Ilustración")
    st.image(material["imagen"])

    st.download_button(
        "Descargar imagen PNG",
        data=material["imagen"],
        file_name="ilustracion.png",
        mime="image/png",
    )

if "audio" in material:
    st.subheader("Narración")
    st.caption("Esta narración utiliza una voz generada por IA.")
    st.audio(material["audio"], format="audio/mpeg")

    st.download_button(
        "Descargar narración MP3",
        data=material["audio"],
        file_name="narracion.mp3",
        mime="audio/mpeg",
    )
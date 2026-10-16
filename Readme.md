# EvU3 — Generador de material educativo con OpenAI

Aplicación Python para ayudar a docentes de Lenguaje a generar
cuentos para estudiantes de 1.º a 4.º básico, una ilustración PNG
y la narración del cuento en formato MP3.

## Estado del proyecto

El código incluye la integración con OpenAI y cuenta con
30 pruebas automáticas aprobadas usando clientes sustituidos.

Todavía no se ha verificado la autenticación, el acceso a los
modelos ni la generación real de contenido.

Las pruebas no consumen la API. La ejecución real sí consume saldo.

## Requisitos

- Python 3.14.7, versión utilizada durante el desarrollo.
- Dependencias de requirements.txt.
- Conexión a internet para instalar dependencias y utilizar la API.
- Clave de OpenAI con permisos de generación.
- Saldo y acceso a los modelos configurados.

## Organización

```text
EvU3/
├── config/
│   ├── __init__.py
│   └── settings.py
├── src/
│   ├── __init__.py
│   ├── texto.py
│   ├── imagen.py
│   └── audio.py
├── tests/
│   ├── __init__.py
│   ├── test_texto.py
│   ├── test_imagen.py
│   ├── test_audio.py
│   └── test_main.py
├── resultados/
│   ├── texto/
│   ├── imagenes/
│   └── audio/
├── .env
├── .gitignore
├── main.py
├── app.py
├── requirements.txt
└── README.md
```

Las carpetas de resultados se crean cuando se necesitan.

## Instalación en Windows

Abre PowerShell desde la carpeta principal EvU3.

Si todavía no existe el entorno virtual:

```powershell
python -m venv venv
```

Actívalo:

```powershell
.\venv\Scripts\Activate.ps1
```

Instala las dependencias:

```powershell
python -m pip install -r requirements.txt
```

Si no puedes activar el entorno, utiliza directamente:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configuración

Crea .env en la raíz:

```env
OPENAI_API_KEY=pega_aqui_tu_clave

MODELO_TEXTO=gpt-6-luna

MODELO_IMAGEN=gpt-image-1-mini
CALIDAD_IMAGEN=low
TAMANO_IMAGEN=1024x1024

MODELO_AUDIO=gpt-4o-mini-tts
VOZ_AUDIO=alloy

HABILITAR_API_REAL=false
```

Reemplaza el marcador de la clave únicamente en tu equipo.
No compartas .env ni lo incluyas en la entrega del proyecto.
El archivo está excluido mediante .gitignore.

Las variables existentes en el entorno tienen prioridad sobre .env.

## Comprobar la configuración sin consumo

```powershell
python -c "from config.settings import validar_configuracion; validar_configuracion(); print('Configuración local correcta')"
```

Esta comprobación no consulta OpenAI ni verifica la clave,
los permisos o el saldo.

## Ejecutar las pruebas

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Resultado obtenido durante el desarrollo:

```text
Ran 30 tests
OK
```

Las pruebas sustituyen los clientes y las funciones de generación.
Utilizan claves ficticias y carpetas temporales.

Comprueban:

- Validación de entradas.
- Parámetros de las solicitudes.
- Lectura de respuestas simuladas.
- Guardado y nombres de archivos.
- Bloqueo de la API deshabilitada.
- Cancelación del flujo.
- Manejo de algunos errores y conservación de resultados anteriores.

No comprueban la calidad educativa del contenido, la autenticación
real, la disponibilidad de modelos ni la reproducción de un MP3 real.

## Ejecutar la aplicación

Con el entorno activo:

```powershell
python main.py
```

Ejemplo de entradas:

```text
Tema del cuento: La amistad
Curso (1 a 4 básico): 3
Descripción de la ilustración: Un conejo y una tortuga en un bosque
```

Con HABILITAR_API_REAL=false, la aplicación detiene el proceso
antes de enviar solicitudes. No genera contenido de ejemplo.

Para utilizar la API real, cambia explícitamente en .env:

```env
HABILITAR_API_REAL=true
```

Inicia nuevamente la aplicación. Antes de generar, solicita:

```text
Escribe GENERAR para continuar:
```

Solo escribir GENERAR permite continuar.
Las generaciones consumen saldo de la API de OpenAI.

## Resultados

Una ejecución completa guarda:

- resultados/texto/cuento_<identificador>.txt
- resultados/imagenes/ilustracion_<identificador>.png
- resultados/audio/narracion_<identificador>.mp3

Cada archivo tiene un identificador para conservar resultados anteriores.
La narración utiliza el mismo texto del cuento y una voz generada por IA.

La descripción de la ilustración la proporciona el usuario.
Debe corresponder al tema y a los personajes del cuento.

## Ejemplos de cada función

Estos ejemplos realizan solicitudes de pago si la API está habilitada.

### Cuento

```python
from src.texto import generar_cuento

cuento = generar_cuento("La amistad", 3)
print(cuento)
```

Devuelve el cuento como texto. main.py se encarga de guardarlo.

### Ilustración

```python
from src.imagen import generar_imagen

ruta = generar_imagen("Un conejo y una tortuga en un bosque")
print(ruta)
```

Genera un PNG, lo guarda y devuelve su ubicación.

### Narración

```python
from src.audio import generar_audio

ruta = generar_audio("Un conejo ayudó a su amiga tortuga.")
print(ruta)
```

Genera la narración MP3, la guarda y devuelve su ubicación.

Las llamadas directas a estas funciones no solicitan la confirmación
GENERAR de main.py. Sí comprueban HABILITAR_API_REAL y la configuración.

## Controles de consumo

- Cuento: máximo de 600 tokens de salida y razonamiento none.
- Tema: máximo de 200 caracteres.
- Imagen: una imagen, calidad low y tamaño 1024×1024.
- Descripción: máximo de 1000 caracteres.
- Narración: máximo de 3000 caracteres.
- Reintentos automáticos deshabilitados.

Estos controles reducen el consumo por solicitud.
No constituyen un límite de gasto en dólares.

Si el cuento alcanza el límite de salida y queda incompleto,
la aplicación informa el problema; la solicitud puede haber
consumido saldo.

## Validaciones y errores

El curso debe ser un entero entre 1 y 4.
Tema, descripción y texto deben contener caracteres visibles.

Se manejan errores de:

- Configuración y entradas.
- Autenticación y permisos.
- Límites de uso o saldo.
- Conexión y respuestas HTTP.
- Creación de carpetas y escritura de archivos.

Si un paso falla, los resultados anteriores se conservan.
Las solicitudes completadas pueden haber consumido saldo.
Repetir la aplicación genera solicitudes nuevas.

## Verificación

Se verificó la generación real de un cuento con Luna,
una ilustración PNG con GPT Image 1 Mini y una narración
MP3 con GPT-4o Mini TTS.

La imagen se abrió correctamente y el audio se reprodujo.
También se aprobaron 30 pruebas automáticas sin consumo de API.

Se ejecutó correctamente el flujo completo de main.py con
OpenAI y se guardaron los archivos TXT, PNG y MP3.

La interfaz web permite generar y mostrar el cuento,
la ilustración PNG y la narración MP3, con opciones
para descargar cada resultado.

# Mi aplicación Streamlit
para activar App.py ejecutar comando: python -m streamlit run app.py

## Instalar
python -m pip install -r requirements.txt

## Ejecutar
python -m streamlit run app.py

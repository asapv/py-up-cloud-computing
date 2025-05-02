# py-up-cloud-computing

## Descripción del Proyecto
Es un proyecto de computación en la nube que utiliza Azure Batch para procesar datos de canales de YouTube de manera paralela y escalable. El objetivo principal es extraer información de videos (como metadatos y comentarios) de múltiples canales simultáneamente, procesarlos y almacenar los resultados en archivos Excel. Este pipeline está diseñado para manejar grandes volúmenes de datos de manera eficiente, aprovechando la infraestructura de Azure y contenedores Docker.

## Propósito del Script `run_batch_job.py`
El script run_batch_job.py es el componente central del pipeline. Su función es:

- Obtener Credenciales: Recupera secretos (como claves de API y credenciales de Azure) desde Azure Key Vault.
- Crear un Job en Azure Batch: Configura un job (yt-scraper-job) asociado al pool yt-scraper-pool.
- Generar Tareas: Crea tareas paralelas para procesar cada canal de YouTube definido en la lista channels. Cada tarea ejecuta el script run_pipeline.py dentro de un contenedor Docker, procesando un número definido de videos por canal (por defecto, 5 videos).
- Almacenar Resultados: Guarda los resultados (archivos Excel) en Azure Blob Storage (output).

## Objetivo de la Configuración con Docker y Azure Batch
La configuración del proyecto utiliza Docker y Azure Batch para lograr:

- Escalabilidad: Azure Batch permite procesar múltiples canales de YouTube en paralelo, asignando tareas a nodos del pool yt-scraper-pool. Esto reduce el tiempo de procesamiento al distribuir la carga de trabajo.
- Portabilidad y Consistencia: El uso de un contenedor Docker (ytscraperacr.azurecr.io/yt-scraper) asegura que el entorno de ejecución (dependencias, versiones de Python, bibliotecas) sea consistente en todos los nodos, eliminando problemas de compatibilidad.
- Automatización y Gestión de Recursos: Azure Batch administra automáticamente la asignación de nodos, ejecución de tareas y almacenamiento de resultados, mientras que Docker facilita la configuración del entorno.

Con esta arquitectura, se puede procesar un número variable de canales (por ejemplo, 2 o 4) simultáneamente, ajustando el número de nodos en el pool según la carga de trabajo

---
## Contenido del Repositorio
```plaintext
📦 py-up-cloud-computing\
├── 📁 scripts/                           # Scripts principales del pipeline\
│   ├── run_pipeline.py                   # Script que procesa los datos de un canal de YouTube\
│   └── run_batch_job.py                  # Script que configura y ejecuta tareas en Azure Batch\
├── 📁 src/                               # Código fuente del proyecto\
│   ├── __pycache__/                      # Archivos de caché generados por Python\
│   ├── __init__.py                       # Archivo para definir el módulo src\
│   ├── api_utils.py                      # Utilidades para interactuar con la API de YouTube\
│   ├── moments_analyzer.py               # Script para analizar momentos en los videos\
│   ├── pipeline.py                       # Script principal del pipeline (ejecutado por run_pipeline.py)\
│   ├── svg_extraction.py                 # Script para extraer datos en formato SVG (si aplica)\
│   └── video_metadata.py                 # Script para extraer metadatos de videos\
├── 📄 .env                               # Archivo de variables de entorno\
├── 📄 .gitignore                         # Archivo para ignorar archivos en Git\
├── 📄 Dockerfile                         # Definición del contenedor para el pipeline\
├── 📄 README.md                          # Documentación del proyecto\
└── 📄 requirements.txt                   # Dependencias del proyecto\
```

## Integrantes del Equipo
* **Bruno Andre Herrera Criollo**  
  Departamento de Ingeniería, Universidad del Pacífico.
* **Jhoan Leandro Vargas Collas**  
  Departamento de Ingeniería, Universidad del Pacífico.
* **Paulo Giusepe Verde Huayney**  
  Departamento de Ingeniería, Universidad del Pacífico.

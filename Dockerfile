FROM ubuntu:20.04
 # Evitar interacciones durante la instalación
 ENV DEBIAN_FRONTEND=noninteractive

 # Instalar dependencias
 RUN apt-get update && apt-get install -y \
     python3 \
     python3-pip \
     firefox \
     wget \
     && rm -rf /var/lib/apt/lists/*

 # Instalar geckodriver
 RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
     && tar -xvzf geckodriver-v0.34.0-linux64.tar.gz \
     && mv geckodriver /usr/local/bin/ \
     && rm geckodriver-v0.34.0-linux64.tar.gz

 # Instalar dependencias de Python
 COPY requirements.txt .
 RUN pip3 install --no-cache-dir -r requirements.txt

 # Copiar perfil de Firefox
 COPY firefox_profile /root/.mozilla/firefox/profile
 ENV FIREFOX_PROFILE_PATH=/root/.mozilla/firefox/profile

 # Copiar código fuente
 COPY src /app/src
 COPY scripts /app/scripts
 COPY .env /app/.env

 # Establecer directorio de trabajo
 WORKDIR /app

 # Comando por defecto
 CMD ["python3", "scripts/run_pipeline.py"]
#!/bin/bash

# Script para exponer Streamlit a internet usando ngrok

echo "🚀 Iniciando Streamlit y exponiendo a internet con ngrok..."

# Iniciar Streamlit en segundo plano
streamlit run app.py --server.address 0.0.0.0 --server.port 8501 &
STREAMLIT_PID=$!

# Esperar a que Streamlit inicie
sleep 3

# Exponer con ngrok (necesitas tener ngrok instalado)
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok encontrado"
    echo "🌍 Tu aplicación estará disponible en la URL que mostrará ngrok"
    echo ""
    ngrok http 8501
else
    echo "❌ ngrok no está instalado"
    echo ""
    echo "Instálalo con:"
    echo "  1. Ve a https://ngrok.com/signup"
    echo "  2. Descarga ngrok para Linux"
    echo "  3. Ejecuta: unzip ngrok.zip && sudo mv ngrok /usr/local/bin/"
    echo "  4. Configura tu token: ngrok config add-authtoken <tu-token>"
fi

# Limpiar al salir
kill $STREAMLIT_PID 2>/dev/null

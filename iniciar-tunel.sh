#!/bin/bash

# Script para iniciar el túnel ngrok hacia la aplicación Streamlit
# Uso: ./iniciar-tunel.sh

echo "🚀 Iniciando túnel ngrok para Sendas Antiguas..."
echo ""

# Verificar si Streamlit está corriendo
if ! curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "⚠️  Streamlit no está corriendo. Iniciándolo..."
    streamlit run app.py &
    sleep 5
fi

# Iniciar ngrok
echo "✅ Creando túnel público..."
echo "📋 URL pública aparecerá abajo"
echo ""

export PATH="$HOME/.local/bin:$PATH"
ngrok http 8501 --log=stdout

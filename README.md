# SA Construcción Iglesia

Aplicación para administrar los ingresos y gastos de la construcción de una iglesia.

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### Ejecutar local (solo tu PC)
```bash
streamlit run app.py
```

### Compartir en red local (para otros dispositivos)
```bash
streamlit run app.py --server.address 0.0.0.0
```
Luego comparte tu IP local con los hermanos: `http://TU_IP:8501`

## Características

- ✅ Registro de donaciones (ingresos)
- ✅ Registro de gastos (egresos)  
- ✅ Dashboard con gráficos modernos
- ✅ Resumen financiero
- ✅ Export PDF
- ✅ Datos se guardan localmente

## Estructura

```
SA Construccion Iglesia/
├── app.py              # Aplicación principal
├── requirements.txt    # Dependencias
└── datos_iglesia/       # Datos (se crea automáticamente)
    └── datos.db        # Base de datos SQLite
```
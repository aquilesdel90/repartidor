# 🚚 Bimba Scanner — Guía de Deploy

## Qué hace esta app
- Escanea etiquetas con la cámara (OCR offline)
- Swipe derecha = confirmar · izquierda = rechazar
- Al 3er rechazo abre dictado por voz automáticamente
- Manda todas las direcciones al servidor de una vez
- OR-Tools calcula la ruta óptima real
- Mapa Leaflet con todos los puntos y la línea del recorrido
- Cada parada abre Google Maps GPS directo

---

## PASO 1 — API Key de Mapbox (5 minutos, gratis)

1. Entrá a https://mapbox.com
2. Crear cuenta (gratis, no pide tarjeta)
3. Dashboard → Tokens → Copy Default Public Token
4. Guardalo, lo vas a necesitar en el Paso 3

---

## PASO 2 — Subir a GitHub

1. Entrá a https://github.com → New repository
2. Nombre: `bimba-scanner`
3. Público o privado, cualquiera sirve
4. Crear repositorio
5. Subí estos archivos:
   - `app.py`
   - `requirements.txt`
   - `Procfile`
   - `railway.toml`
   - `static/index.html`

   **Opción fácil — desde la web de GitHub:**
   - En el repositorio vacío, clic en "uploading an existing file"
   - Arrastrá todos los archivos (respetando la carpeta static/)

---

## PASO 3 — Deploy en Railway (10 minutos, gratis)

1. Entrá a https://railway.app
2. Login con GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Elegí `bimba-scanner`
5. Railway detecta Python automáticamente y despliega

6. **Configurar la API Key de Mapbox:**
   - En el proyecto Railway → Settings → Variables
   - Agregar variable:
     - Key: `MAPBOX_TOKEN`
     - Value: tu token de Mapbox del Paso 1
   - Save → Railway redespliega automáticamente

7. **Obtener la URL de tu app:**
   - Settings → Domains → Generate Domain
   - Te da algo como: `bimba-scanner-production.up.railway.app`

---

## PASO 4 — Configurar la URL en la app

1. Abrí `static/index.html`
2. Buscá la línea:
   ```
   const BACKEND_URL = window.location.origin;
   ```
3. Esta línea ya está bien — no hay que cambiar nada.
   La app usa automáticamente la misma URL del servidor.

---

## PASO 5 — Usar en el celu

1. Abrí Chrome en el celu
2. Entrá a tu URL de Railway
3. Chrome va a pedir permiso de cámara → Permitir
4. ¡Listo!

**Tip:** Agregala a la pantalla de inicio:
Chrome → menú (3 puntos) → "Agregar a pantalla de inicio"
Queda como una app nativa.

---

## Flujo de uso

### Antes de salir (con datos o WiFi):
1. Abrís la app
2. Apuntás la cámara a cada etiqueta
3. Swipe derecha si la dirección está bien
4. Swipe izquierda si no (al 3er rechazo abre voz)
5. Cuando terminaste → "Calcular ruta"
6. La app manda todo al servidor, geocodifica y optimiza
7. Te muestra el mapa con el recorrido completo

### En el auto (sin internet):
1. El mapa ya está cargado
2. Tocás "Ir a parada 1 →"
3. Se abre Google Maps con esa coordenada exacta
4. Llegás, entregás, volvés a la app
5. "Ir a parada 2 →" y así hasta terminar

---

## Si algo falla

- **OCR no lee bien:** Usá el botón 🎤 Voz o ✏️ Manual
- **Geocodificación falla:** Revisá que MAPBOX_TOKEN esté configurado en Railway
- **La app no carga:** Verificá que Railway muestre "Active" en verde

---

## Costo

- Railway: gratis hasta 500 horas/mes (te sobra)
- Mapbox: gratis hasta 100.000 geocodificaciones/mes
- OR-Tools: gratis para siempre
- Leaflet (mapa): gratis para siempre

**Total: $0**

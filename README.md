# bloc_notas
Bloc de notas con Tkinter y SQLite, pensado para ser ligero y portable.

## Caracteristicas
- Notas con persistencia en SQLite.
- Editor con busqueda, reemplazo y resaltado.
- Formato basico: negrita, cursiva, subrayado, tachado, colores.
- Inserciones rapidas (titulos, listas, checklist, bloques de codigo, enlaces).
- Exportar a `.txt` / `.md` e importar `.md`.
- Multilenguaje (es/en/pt/fr) y temas (warm/dark/minimal/retro).
- Barra de estado con contadores y estado de guardado.
- Plantillas configurables desde `settings.json`.
- Filtros por tags y ordenamiento (recientes / A-Z / pines primero).

## Requisitos
- Python 3.10+

## Ejecutar
```bash
python block.py
```

Opciones CLI:
```bash
python block.py --reset-settings
python block.py --debug
```

## Estructura del proyecto
```
bloc_notas/
  block.py
  src/
    app.py
    notes_app.py
    storage_sqlite.py
    export_import.py
    models.py
    controllers/
    ui/
  tests/
```

## Base de datos
Tabla `notes` (SQLite):
- `id` (TEXT UUID)
- `title` (TEXT)
- `content` (TEXT)
- `tags` (TEXT, separadas por coma)
- `pinned` (INTEGER 0/1)
- `created_at`, `updated_at` (TEXT ISO)

## Configuracion
- `settings.json` se crea automaticamente al guardar configuracion.
- Puedes restablecerla con `--reset-settings`.
- Formatos de fecha/hora usan `strftime` y se validan al cargar.
- Si hay problemas de configuracion, se muestran avisos en la barra de estado.

Ejemplo de `settings.json`:
```json
{
  "settings_version": 1,
  "theme": "warm",
  "language": "es",
  "datetime_format": "%Y-%m-%d %H:%M",
  "date_format": "%Y-%m-%d",
  "search": {
    "term": "",
    "match_case": false,
    "regex": false,
    "whole_word": false
  },
  "view": {
    "status_bar": true,
    "zoom": 100,
    "focus": false
  },
  "tab_size": 4,
  "sidebar": {
    "sort_mode": "pinned",
    "tags": []
  },
  "templates": {
    "quick_note": "Plantilla opcional"
  }
}
```

## Tests
```bash
pytest
```

## Atajos rapidos
Edicion:
- `Ctrl+Z` / `Ctrl+Y` o `Ctrl+Shift+Z`: Deshacer / Rehacer
- `Ctrl+X` / `Ctrl+C` / `Ctrl+V`: Cortar / Copiar / Pegar
- `Ctrl+A`: Seleccionar todo
- `Ctrl+L`: Seleccionar linea
- `Ctrl+D`: Seleccionar palabra

Formato:
- `Ctrl+B` / `Ctrl+I` / `Ctrl+U`: Negrita / Cursiva / Subrayado
- `Ctrl+Shift+X`: Tachado
- `Ctrl+Shift+K`: Limpiar formato (seleccion)
- `Ctrl+Plus` / `Ctrl+-`: Tamano + / -
- `Ctrl+0`: Restablecer tamano

Insertar:
- `Ctrl+Shift+H`: Encabezado
- `Ctrl+Shift+L`: Lista
- `Ctrl+Shift+S`: Separador
- `Ctrl+Alt+1/2/3`: H1 / H2 / H3
- `Ctrl+Alt+U`: Insertar enlace
- `Ctrl+Alt+I`: Codigo inline
- `Ctrl+Alt+G`: Bloque de codigo
- `Ctrl+Shift+D`: Fecha
- `Ctrl+Alt+T`: Fecha y hora

Buscar:
- `Ctrl+F` o `Ctrl+H`: Buscar en nota
- `F3` / `Shift+F3`: Buscar siguiente / anterior
- `Ctrl+F2`: Buscar en lista

Vista:
- `Ctrl+Alt++` / `Ctrl+Alt+-`: Zoom +
- `Ctrl+Alt+0`: Reset zoom
- `Ctrl+Shift+F`: Modo enfoque

## Archivos ignorados
Por defecto se ignoran:
- `notes.db`
- `settings.json`
## Archivos ignorados
Por defecto se ignoran:
- `notes.db`
- `settings.json`

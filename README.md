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
- Formatos de fecha/hora usan `strftime`.

## Tests
```bash
pytest
```

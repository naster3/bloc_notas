from __future__ import annotations

SECTION_TITLES = {
    "edit": {"es": "Edicion", "en": "Editing", "pt": "Edicao", "fr": "Edition"},
    "format": {"es": "Formato", "en": "Formatting", "pt": "Formato", "fr": "Format"},
    "insert": {"es": "Insertar", "en": "Insert", "pt": "Inserir", "fr": "Inserer"},
    "search": {"es": "Buscar", "en": "Search", "pt": "Buscar", "fr": "Rechercher"},
    "view": {"es": "Ver", "en": "View", "pt": "Ver", "fr": "Affichage"},
}

SHORTCUTS = {
    "edit": [
        {
            "keys": "Ctrl+Z",
            "label": {
                "es": "Deshacer",
                "en": "Undo",
                "pt": "Desfazer",
                "fr": "Annuler",
            },
        },
        {
            "keys": "Ctrl+Y",
            "label": {
                "es": "Rehacer",
                "en": "Redo",
                "pt": "Refazer",
                "fr": "Retablir",
            },
        },
        {
            "keys": "Ctrl+Shift+Z",
            "label": {
                "es": "Rehacer",
                "en": "Redo",
                "pt": "Refazer",
                "fr": "Retablir",
            },
        },
        {
            "keys": "Ctrl+X",
            "label": {
                "es": "Cortar",
                "en": "Cut",
                "pt": "Cortar",
                "fr": "Couper",
            },
        },
        {
            "keys": "Ctrl+C",
            "label": {
                "es": "Copiar",
                "en": "Copy",
                "pt": "Copiar",
                "fr": "Copier",
            },
        },
        {
            "keys": "Ctrl+V",
            "label": {
                "es": "Pegar",
                "en": "Paste",
                "pt": "Colar",
                "fr": "Coller",
            },
        },
        {
            "keys": "Ctrl+A",
            "label": {
                "es": "Seleccionar todo",
                "en": "Select all",
                "pt": "Selecionar tudo",
                "fr": "Tout selectionner",
            },
        },
        {
            "keys": "Ctrl+L",
            "label": {
                "es": "Seleccionar linea",
                "en": "Select line",
                "pt": "Selecionar linha",
                "fr": "Selectionner ligne",
            },
        },
        {
            "keys": "Ctrl+D",
            "label": {
                "es": "Seleccionar palabra",
                "en": "Select word",
                "pt": "Selecionar palavra",
                "fr": "Selectionner mot",
            },
        },
    ],
    "format": [
        {
            "keys": "Ctrl+B",
            "label": {
                "es": "Negrita",
                "en": "Bold",
                "pt": "Negrito",
                "fr": "Gras",
            },
        },
        {
            "keys": "Ctrl+I",
            "label": {
                "es": "Cursiva",
                "en": "Italic",
                "pt": "Italico",
                "fr": "Italique",
            },
        },
        {
            "keys": "Ctrl+U",
            "label": {
                "es": "Subrayado",
                "en": "Underline",
                "pt": "Sublinhado",
                "fr": "Souligner",
            },
        },
        {
            "keys": "Ctrl+Shift+X",
            "label": {
                "es": "Tachado",
                "en": "Strikethrough",
                "pt": "Riscado",
                "fr": "Barre",
            },
        },
        {
            "keys": "Ctrl+Shift+K",
            "label": {
                "es": "Limpiar formato",
                "en": "Clear formatting",
                "pt": "Limpar formato",
                "fr": "Effacer format",
            },
        },
        {
            "keys": "Ctrl+Shift+R",
            "label": {
                "es": "Restablecer formato",
                "en": "Reset formatting",
                "pt": "Redefinir formato",
                "fr": "Reinitialiser format",
            },
        },
        {
            "keys": "Ctrl+Alt+F",
            "label": {
                "es": "Fuente",
                "en": "Font",
                "pt": "Fonte",
                "fr": "Police",
            },
        },
        {
            "keys": "Ctrl+Alt+C",
            "label": {
                "es": "Color de texto",
                "en": "Text color",
                "pt": "Cor do texto",
                "fr": "Couleur du texte",
            },
        },
        {
            "keys": "Ctrl+Alt+B",
            "label": {
                "es": "Color de fondo",
                "en": "Background color",
                "pt": "Cor de fundo",
                "fr": "Couleur de fond",
            },
        },
        {
            "keys": "Ctrl+Plus / Ctrl+-",
            "label": {
                "es": "Tamano +/-",
                "en": "Size +/-",
                "pt": "Tamanho +/-",
                "fr": "Taille +/-",
            },
        },
        {
            "keys": "Ctrl+0",
            "label": {
                "es": "Restablecer tamano",
                "en": "Reset size",
                "pt": "Redefinir tamanho",
                "fr": "Reinitialiser taille",
            },
        },
    ],
    "insert": [
        {
            "keys": "Ctrl+Shift+H",
            "label": {
                "es": "Encabezado",
                "en": "Heading",
                "pt": "Cabecalho",
                "fr": "Entete",
            },
        },
        {
            "keys": "Ctrl+Alt+1/2/3",
            "label": {
                "es": "Titulos H1/H2/H3",
                "en": "Titles H1/H2/H3",
                "pt": "Titulos H1/H2/H3",
                "fr": "Titres H1/H2/H3",
            },
        },
        {
            "keys": "Ctrl+Shift+D",
            "label": {
                "es": "Fecha",
                "en": "Date",
                "pt": "Data",
                "fr": "Date",
            },
        },
        {
            "keys": "Ctrl+Alt+T",
            "label": {
                "es": "Fecha y hora",
                "en": "Date and time",
                "pt": "Data e hora",
                "fr": "Date et heure",
            },
        },
        {
            "keys": "Ctrl+Shift+L",
            "label": {
                "es": "Lista",
                "en": "List",
                "pt": "Lista",
                "fr": "Liste",
            },
        },
        {
            "keys": "Ctrl+Shift+B",
            "label": {
                "es": "Lista con vi\u00f1etas",
                "en": "Bulleted list",
                "pt": "Lista com marcadores",
                "fr": "Liste a puces",
            },
        },
        {
            "keys": "Ctrl+Shift+N",
            "label": {
                "es": "Lista numerada",
                "en": "Numbered list",
                "pt": "Lista numerada",
                "fr": "Liste numerotee",
            },
        },
        {
            "keys": "Ctrl+Shift+C",
            "label": {
                "es": "Checklist",
                "en": "Checklist",
                "pt": "Checklist",
                "fr": "Checklist",
            },
        },
        {
            "keys": "Ctrl+Alt+L",
            "label": {
                "es": "Enlace",
                "en": "Link",
                "pt": "Link",
                "fr": "Lien",
            },
        },
        {
            "keys": "Ctrl+Alt+U",
            "label": {
                "es": "Insertar enlace",
                "en": "Insert link",
                "pt": "Inserir link",
                "fr": "Inserer lien",
            },
        },
        {
            "keys": "Ctrl+Alt+I",
            "label": {
                "es": "Codigo inline",
                "en": "Inline code",
                "pt": "Codigo inline",
                "fr": "Code inline",
            },
        },
        {
            "keys": "Ctrl+Alt+G",
            "label": {
                "es": "Bloque de codigo",
                "en": "Code block",
                "pt": "Bloco de codigo",
                "fr": "Bloc de code",
            },
        },
        {
            "keys": "Ctrl+Alt+Q/M/O/J",
            "label": {
                "es": "Plantillas rapida/reunion/todo/diario",
                "en": "Templates quick/meeting/todo/journal",
                "pt": "Modelos rapida/reuniao/todo/diario",
                "fr": "Modeles rapide/reunion/todo/journal",
            },
        },
        {
            "keys": "Menu",
            "label": {
                "es": "Separador, Encabezados, Listas, Plantillas, Enlaces/Codigo, Fechas",
                "en": "Separator, Headings, Lists, Templates, Links/Code, Dates",
                "pt": "Separador, Cabecalhos, Listas, Modelos, Links/Codigo, Datas",
                "fr": "Separateur, Entetes, Listes, Modeles, Liens/Code, Dates",
            },
        }
    ],
    "search": [
        {
            "keys": "Ctrl+F",
            "label": {
                "es": "Buscar en nota",
                "en": "Find in note",
                "pt": "Buscar na nota",
                "fr": "Rechercher dans la note",
            },
        },
        {
            "keys": "Ctrl+F2",
            "label": {
                "es": "Buscar en lista",
                "en": "Search in list",
                "pt": "Buscar na lista",
                "fr": "Rechercher dans la liste",
            },
        },
        {
            "keys": "Ctrl+H",
            "label": {
                "es": "Reemplazar",
                "en": "Replace",
                "pt": "Substituir",
                "fr": "Remplacer",
            },
        },
        {
            "keys": "F3",
            "label": {
                "es": "Buscar siguiente",
                "en": "Find next",
                "pt": "Buscar seguinte",
                "fr": "Rechercher suivant",
            },
        },
        {
            "keys": "Shift+F3",
            "label": {
                "es": "Buscar anterior",
                "en": "Find previous",
                "pt": "Buscar anterior",
                "fr": "Rechercher precedent",
            },
        },
        {
            "keys": "Menu",
            "label": {
                "es": "Buscar en lista",
                "en": "Search in list",
                "pt": "Buscar na lista",
                "fr": "Rechercher dans la liste",
            },
        },
    ],
    "view": [
        {
            "keys": "Ctrl+Alt+Plus",
            "label": {
                "es": "Acercar",
                "en": "Zoom in",
                "pt": "Ampliar",
                "fr": "Zoom avant",
            },
        },
        {
            "keys": "Ctrl+Shift+F",
            "label": {
                "es": "Modo enfoque",
                "en": "Focus mode",
                "pt": "Modo foco",
                "fr": "Mode focus",
            },
        },
        {
            "keys": "Ctrl+Alt+-",
            "label": {
                "es": "Alejar",
                "en": "Zoom out",
                "pt": "Reduzir",
                "fr": "Zoom arriere",
            },
        },
        {
            "keys": "Ctrl+Alt+0",
            "label": {
                "es": "Restaurar zoom",
                "en": "Reset zoom",
                "pt": "Restaurar zoom",
                "fr": "Reinitialiser zoom",
            },
        },
        {
            "keys": "Menu",
            "label": {
                "es": "Restablecer vista",
                "en": "Reset view",
                "pt": "Restaurar vista",
                "fr": "Reinitialiser vue",
            },
        },
        {
            "keys": "Ctrl+Alt+R",
            "label": {
                "es": "Restablecer vista",
                "en": "Reset view",
                "pt": "Restaurar vista",
                "fr": "Reinitialiser vue",
            },
        },
        {
            "keys": "Menu",
            "label": {
                "es": "Ajuste de linea, Barra de estado, Restablecer vista",
                "en": "Line wrap, Status bar, Reset view",
                "pt": "Quebra de linha, Barra de status, Restaurar vista",
                "fr": "Retour a la ligne, Barre d'etat, Reinitialiser vue",
            },
        },
    ],
}

SECTION_ORDER = ("edit", "format", "insert", "search", "view")

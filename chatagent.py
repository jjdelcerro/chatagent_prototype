# -*- coding: utf-8 -*-
"""
Módulo principal de la aplicación.
Lanza la interfaz de usuario del chat y registra los procesadores de respuesta.
"""

from addons.chatagent_prototype.gvsigdesktop.utils import showPanel

from addons.chatagent_prototype.aiclients.gemini import GeminiClient

from addons.chatagent_prototype.chat_panel import ChatPanel
from addons.chatagent_prototype.processors.text_processor import TextProcessor
from addons.chatagent_prototype.processors.sql_processor import SqlProcessor
from addons.chatagent_prototype.processors.chart_processor import ChartProcessor
from addons.chatagent_prototype.processors.plantuml_processor import PlantUMLProcessor

"""
Otros processors a implementar:
- zoom, hace zoom en la vista
  Similar al sql pero con el resultado se calcula un envelope y se aplica a la vista corrient

- select, selecciona elementos de una capa
  seria siminar al de sql pero con el resultado selecciona los elementos de una capa.

- drawgeom, genera una geometria y se inserta en el graphics layer
  Similar a sql pero con el resultado crea una/s geometria/s que inserta en el graphics layer

- updatetable, llama al update table.
  No esta claro como podria operar, pero la cosa es que interactue con la herramienta de 
  actualizar tabla.

- operar con la seleccion  SELECT * FROM T WHERE PK in ({pk_seleccion})
  No esta nada claro, pero que pueda interactuar con la seleccion de una capa seria
  muy interesante.

"""

def main(**args):
    """
    Función principal que inicializa y lanza la aplicación de chat.
    """
    chat_panel = ChatPanel(GeminiClient())

    # Registrar los procesadores de respuesta
    chat_panel.register_processor(TextProcessor())
    chat_panel.register_processor(SqlProcessor())
    chat_panel.register_processor(ChartProcessor())
    chat_panel.register_processor(PlantUMLProcessor())

    # Mostrar el panel de chat en una ventana
    showPanel(chat_panel, "[\u26A0\uFE0F PRUEBA CONCEPTUAL] Chat con el asistente virtual")


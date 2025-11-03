# -*- coding: utf-8 -*-
"""
Módulo para el procesador de respuestas de tipo 'text'.
Extiende la clase abstracta Processor y maneja las respuestas generales de la IA.
"""

from addons.chatagent_prototype.processor import Processor

class TextProcessor(Processor):
    """
    Procesador para respuestas de tipo 'text'.
    Simplemente extrae el mensaje de la respuesta JSON y lo muestra en el historial del chat.
    """

    def get_type(self):
        """
        Devuelve el tipo de procesador.
        """
        return "text"

    def get_description(self):
        """
        Devuelve una breve descripción de lo que hace este procesador.
        """
        return u"Gestiona consultas de texto generales."

    def get_initial_prompt_info(self):
        """
        Devuelve la parte del prompt inicial que describe este procesador.
        """
        return u"""
== Consultas de tipo 'text' ==
  Se devolvera este tipo de respuesta cuando la peticion del usuario no se corresponda con ninguno de los otros tipos.
  El campo 'type' debe ser "text".
  Debe incluir un campo 'message' con la respuesta a mostrar al usuario.
  Al construir este json debes prestar especial atencion al contenido del mensaje, ya que el json resultante debe ser valido.
  Si en el mensaje aparecen dobles comillas o retornos de linea recuerda que debes escaparlas.
  Ejemplo:
  {
    "type": "text",
    "message": "Hola, soy un asistente de chat. ¿En qué puedo ayudarte?"
  }
"""

    def process_response(self, chat, user_query, json_response):
        try:
            message = json_response.getString("message")
            chat.append_message(chat.getAgentName(), message)
        except Exception as e:
            chat.append_message(chat.getAgentName(),u"Error al procesar la respuesta: %s" % e)
            print "Error al procesar la respuesta de texto: %s" % e


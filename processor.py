 
# -*- coding: utf-8 -*-
"""
Módulo que define la clase abstracta base para todos los procesadores de respuesta.
Cada tipo de procesador específico (texto, SQL, gráfico) extenderá esta clase.
"""

class Processor:
    """
    Clase abstracta base para los procesadores de respuesta de la IA.
    Define la interfaz común que deben implementar todos los procesadores específicos.
    """

    def process_response(self, chat_panel, user_query, json_response):
        """
        Procesa la respuesta JSON de la IA.
        Este método debe ser implementado por las subclases para manejar
        la lógica específica de cada tipo de respuesta.

        Args:
            chat_panel (chat_panel.ChatPanel): La instancia del panel de chat para interactuar con la UI.
            json_response (javax.json.JsonObject): El objeto JSON devuelto por la IA.
        """
        raise NotImplementedError("El método process_response debe ser implementado por las subclases.")

    def get_type(self):
        """
        Devuelve el tipo de procesador.
        Por ejemplo: "text", "sql_processor", "chart_processor".

        Returns:
            str: El tipo de procesador.
        """
        raise NotImplementedError("El método get_type debe ser implementado por las subclases.")

    def get_initial_prompt_info(self):
        """
        Devuelve la parte del prompt inicial que describe este procesador,
        incluyendo el formato esperado de la respuesta JSON para este tipo.

        Returns:
            str: La descripción del procesador para el prompt inicial.
        """
        raise NotImplementedError("El método get_initial_prompt_info debe ser implementado por las subclases.")

    def get_description(self):
        """
        Devuelve una breve descripción de lo que hace este procesador,
        para ser usada en la lista de tipos de consulta soportados en el prompt inicial.

        Returns:
            str: Una descripción corta del procesador.
        """
        raise NotImplementedError("El método get_description debe ser implementado por las subclases.")

def main(**args):
  print "processor ok"

  
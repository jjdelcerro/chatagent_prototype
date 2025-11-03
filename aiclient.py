# -*- coding: utf-8 -*-
"""
Módulo que define la clase abstracta base para todos los cliente de IA.
Cada cliente específico extenderá esta clase.
"""

class AIClient:
    """
    Clase abstracta base para los distintos clientes de IA.
    Define la interfaz común que deben implementar todos los clientes específicos.
    """
    def __init__(self):
      pass
      
    def resetHistory(self):
        """
        Reinicia el historial de mensajes de la conversación.
        Esto elimina todas las interacciones previas almacenadas.
        """
        raise NotImplementedError("El método resetHistory debe ser implementado por las subclases.")
        

    def send_message(self, user_prompt, initial_prompt=None, temperature=None):
        """
        Envía un mensaje al modelo de IA, gestionando el historial de la conversación.

        Args:
            user_prompt (str): El mensaje actual del usuario. Este mensaje se añade al historial
                                y se envía como parte de la conversación.
            initial_prompt (str, optional): Un mensaje inicial que se añade al historial
                                            solo si el historial está completamente vacío.
                                            Útil para establecer el contexto inicial de la conversación.
                                            Por defecto es None.
            temperature (float, optional): La temperatura de generación para esta solicitud específica.

        Returns:
            str: La respuesta generada por el modelo de IA.
                 Si ocurre un error durante la solicitud o el procesamiento de la respuesta,
                 devuelve una cadena que indica el error.
        """
        raise NotImplementedError("El método send_message debe ser implementado por las subclases.")

def main(**args):
  print "Ok"
   

# -*- coding: utf-8 -*-
"""
Módulo: gemini_api

Descripción:
Este módulo proporciona una clase GeminiAPI para interactuar con la API de Gemini.
Gestiona el historial de la conversación y realiza solicitudes HTTP POST
utilizando las clases estándar de Java (java.net) y procesa JSON con javax.json.
Está diseñado para ejecutarse en Jython 2.7 sobre Java 1.8.
"""

# Importa las clases necesarias de Java para la conexión de red y E/S
from java.net import URL, HttpURLConnection
from java.io import BufferedReader, InputStreamReader, OutputStreamWriter, StringReader

# Importa las clases necesarias de javax.json para la manipulación de JSON
from javax.json import Json
from javax.json import JsonObject
from javax.json import JsonArray
from javax.json import JsonReader

import sys

from addons.chatagent_prototype.aiclient import AIClient
from addons.chatagent_prototype import config


class GeminiClient(AIClient):
    """
    Clase para interactuar con la API de Gemini, gestionando el historial de mensajes.
    """

    def __init__(self, temperature=0.1): # 0.3 o incluso menor parece lo razonable para programar (jython o SQL)
        """
        Inicializa una nueva instancia de GeminiAPI.
        El historial de mensajes se inicializa vacío.
        La clave API se espera que sea inyectada por el entorno de ejecución (Canvas).

        Args:
            temperature (float, optional): La temperatura de generación del modelo.
                                           Un valor entre 0.0 y 1.0 (inclusive).
                                           Valores más bajos hacen las respuestas más deterministas,
                                           valores más altos las hacen más creativas. Por defecto es 0.3.
        """
        AIClient.__init__(self)
        self.history = []  # Almacena el historial de mensajes en el formato esperado por la API de Gemini.
                           # Ejemplo: [{"role": "user", "parts": [{"text": "Hola"}]}, ...]
        self.model_name = config.GEMINI_MODEL
        self.api_key = config.API_KEY
        self.api_url_base = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s"
        self.temperature = temperature # Atributo para la temperatura de generación

    def resetHistory(self):
        """
        Reinicia el historial de mensajes de la conversación.
        Esto elimina todas las interacciones previas almacenadas.
        """
        self.history = []
        print("Historial de mensajes reiniciado.")

    def _build_payload(self, current_temperature=None):
        """
        Construye el objeto JSON que se enviará como payload a la API de Gemini.
        El payload se construye a partir del historial de mensajes actual e incluye
        la configuración de generación con la temperatura.

        Args:
            current_temperature (float, optional): La temperatura específica para esta solicitud.
                                                   Si se proporciona, sobrescribe la temperatura
                                                   predeterminada de la instancia.

        Returns:
            javax.json.JsonObject: El objeto JSON que representa el payload de la solicitud.
        """
        payload_builder = Json.createObjectBuilder()

        # Construye el array 'contents' que contiene toda la conversación
        contents_array_builder = Json.createArrayBuilder()
        for message in self.history:
            message_builder = Json.createObjectBuilder()
            message_builder.add("role", message["role"])
            
            parts_array_builder = Json.createArrayBuilder()
            # Itera sobre las partes de cada mensaje (asumiendo que cada parte tiene una clave 'text')
            for part in message["parts"]:
                parts_array_builder.add(Json.createObjectBuilder().add("text", part["text"]))
            
            message_builder.add("parts", parts_array_builder)
            contents_array_builder.add(message_builder)

        payload_builder.add("contents", contents_array_builder)

        # Añadir la configuración de generación (generationConfig) con la temperatura
        # Usa la temperatura proporcionada en el método o la temperatura de la instancia
        temp_to_use = current_temperature if current_temperature is not None else self.temperature
        
        generation_config_builder = Json.createObjectBuilder()
        generation_config_builder.add("temperature", float(temp_to_use)) # Asegura que sea un float

        payload_builder.add("generationConfig", generation_config_builder)

        return payload_builder.build()

    def _send_request(self, payload_json_object):
        """
        Envía una solicitud HTTP POST a la API de Gemini con el payload JSON especificado.
        Maneja la conexión, el envío de datos y la lectura de la respuesta.

        Args:
            payload_json_object (javax.json.JsonObject): El objeto JSON a enviar en el cuerpo de la solicitud.

        Returns:
            str: La respuesta completa de la API como una cadena JSON.

        Raises:
            Exception: Si ocurre un error durante la conexión HTTP o la respuesta de la API no es exitosa.
        """
        try:
            # Construye la URL completa con el nombre del modelo y la clave API
            url_string = self.api_url_base % (self.model_name, self.api_key)
            url = URL(url_string)
            
            # Abre la conexión HTTP
            conn = url.openConnection()
            conn.setRequestMethod("POST")
            conn.setRequestProperty("Content-Type", "application/json")
            conn.setDoOutput(True)  # Habilita la escritura en el cuerpo de la solicitud

            # Escribe el payload JSON en el flujo de salida de la conexión
            output_stream = conn.getOutputStream()
            writer = OutputStreamWriter(output_stream, "UTF-8")
            writer.write(payload_json_object.toString())  # Convierte el JsonObject a su representación de cadena JSON
            writer.flush()
            writer.close()
            output_stream.close()

            # Obtiene el código de respuesta HTTP
            response_code = conn.getResponseCode()

            # Lee la respuesta (o el flujo de error si el código no es 200 OK)
            if response_code == HttpURLConnection.HTTP_OK:
                reader = BufferedReader(InputStreamReader(conn.getInputStream(), "UTF-8"))
            else:
                reader = BufferedReader(InputStreamReader(conn.getErrorStream(), "UTF-8"))
                error_response_content = ""
                line = reader.readLine()
                while line is not None:
                    error_response_content += line
                    line = reader.readLine()
                reader.close()
                conn.disconnect()
                raise Exception("Error de la API (Código: %d): %s" % (response_code, error_response_content))

            # Lee el contenido completo de la respuesta
            response_content = ""
            line = reader.readLine()
            while line is not None:
                response_content += line
                line = reader.readLine()
            reader.close()
            conn.disconnect()
            return response_content
        except Exception, e:
            # Captura y re-lanza cualquier excepción de red o I/O para un manejo superior
            print("Error al enviar la solicitud HTTP: %s" % e)
            raise

    def send_message(self, user_prompt, initial_prompt=None, temperature=None):
        """
        Envía un mensaje al modelo de Gemini, gestionando el historial de la conversación.

        Args:
            user_prompt (str): El mensaje actual del usuario. Este mensaje se añade al historial
                                y se envía como parte de la conversación.
            initial_prompt (str, optional): Un mensaje inicial que se añade al historial
                                            solo si el historial está completamente vacío.
                                            Útil para establecer el contexto inicial de la conversación.
                                            Por defecto es None.
            temperature (float, optional): La temperatura de generación para esta solicitud específica.
                                           Si se proporciona, sobrescribe la temperatura predeterminada
                                           de la instancia de GeminiAPI para esta llamada.
                                           Por defecto es None (usa la temperatura de la instancia).

        Returns:
            str: La respuesta generada por el modelo de Gemini.
                 Si ocurre un error durante la solicitud o el procesamiento de la respuesta,
                 devuelve una cadena que indica el error.
        """
        try:
            # 1. Gestionar el 'initial_prompt': se añade solo si el historial está vacío
            if not self.history and initial_prompt is not None:
                self.history.append({"role": "user", "parts": [{"text": initial_prompt}]})
                #print u"DEBUG: Initial prompt añadido al historial:\n'%s'" % initial_prompt # Para depuración

            # 2. Añadir el 'user_prompt' actual al historial.
            # Este es el mensaje que el usuario acaba de enviar.
            self.history.append({"role": "user", "parts": [{"text": user_prompt}]})
            #print u"DEBUG: User prompt añadido al historial: '%s'" % user_prompt # Para depuración

            # 3. Construir el payload JSON utilizando el historial completo y la temperatura
            payload_json_object = self._build_payload(current_temperature=temperature)
            
            # 4. Enviar la solicitud HTTP a la API de Gemini
            json_response_string = self._send_request(payload_json_object)

            # 5. Parsear la respuesta JSON recibida
            json_reader = Json.createReader(StringReader(json_response_string))
            response_json = json_reader.readObject()
            json_reader.close()

            #print u"DEBUG: recibida respuesta:\n%s" % response_json.toString()
            
            generated_text = ""
            # Extraer el texto generado por el modelo de la respuesta JSON
            if response_json.containsKey("candidates"):
                candidates = response_json.getJsonArray("candidates")
                if not candidates.isEmpty():
                    first_candidate = candidates.getJsonObject(0)
                    if first_candidate.containsKey("content"):
                        content = first_candidate.getJsonObject("content")
                        if content.containsKey("parts"):
                            parts = content.getJsonArray("parts")
                            if not parts.isEmpty():
                                first_part = parts.getJsonObject(0)
                                if first_part.containsKey("text"):
                                    generated_text = first_part.getString("text")
                                else:
                                    print "Advertencia: La parte del contenido no tiene el campo 'text'."
                            else:
                                print "Advertencia: El array 'parts' del contenido está vacío."
                        else:
                            print "Advertencia: El candidato no tiene el campo 'content'."
                    else:
                        print "Advertencia: El candidato no tiene el campo 'content'."
                else:
                    print "Advertencia: El array 'candidates' está vacío en la respuesta de la API."
            else:
                print "Advertencia: La respuesta de la API no contiene el campo 'candidates'."
                # Si la respuesta contiene un objeto 'error', lo procesamos
                if response_json.containsKey("error"):
                    error_obj = response_json.getJsonObject("error")
                    error_message = error_obj.getString("message", "Error desconocido del API.")
                    generated_text = u"Error del API: %s" % error_message
                    print "Error detallado del API: %s" % error_message
                else:
                    generated_text = "Error: Estructura de respuesta inesperada del API."

            #print u"DEBUG: extraida respuesta:\n%s" % generated_text
 
            # 6. Añadir la respuesta del modelo al historial
            # Solo se añade si la respuesta no es un mensaje de error generado internamente.
            if not generated_text.startswith("Error:"):
                self.history.append({"role": "model", "parts": [{"text": generated_text}]})
            
            return generated_text

        except Exception, e:
            # Captura cualquier excepción que ocurra durante el proceso de send_message
            print("Error general en send_message: %s" % e)
            # Si la llamada falla, se puede considerar eliminar el último user_prompt del historial
            # para evitar que una solicitud fallida "contamine" el historial de la conversación.
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop() # Elimina el último mensaje del usuario si la respuesta no se pudo obtener
            return "Error: No se pudo procesar la solicitud o la respuesta del API. Detalles: %s" % e

def main(**args):
  print "Ok"
  
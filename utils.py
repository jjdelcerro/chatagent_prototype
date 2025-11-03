# -*- coding: utf-8 -*-

from java.lang import StringBuilder
from java.util import Collections
from java.util import Properties
from java.util import UUID

from java.io import File 
from java.io import StringReader
from java.net import URL 

from java.awt import Dimension
from java.awt import GridBagConstraints
from javax.swing import JFrame, JPanel
from javax.swing import JLabel, ImageIcon
from javax.swing.text import SimpleAttributeSet, StyleConstants
import javax.swing.JComponent

from javax.json import Json

import os


def send_message(api, user_input, initial_prompt=None):
  response = api.send_message(user_input,initial_prompt)  
  return response

def loadImageIntoLabel(label, imagePath):
    """
    Carga una imagen desde la ruta de archivo especificada (PNG) y la establece
    como el icono de un JLabel.

    Args:
        label (JLabel): El JLabel donde se cargará la imagen.
        imagePath (str): La ruta completa al archivo de imagen (por ejemplo, "C:/imagenes/mi_imagen.png").
    """
    if not isinstance(label, JLabel):
        print "Error: El primer argumento debe ser una instancia de JLabel."
        return

    if not imagePath:
        print "Error: La ruta de la imagen debe ser una cadena no vacía."
        return

    try:
        # Intenta crear un objeto File para la ruta de la imagen
        imageFile = File(imagePath)

        # Verifica si el archivo existe y es un archivo
        if not imageFile.exists():
            print "Error: El archivo de imagen no existe en la ruta: %s" % imagePath
            label.setIcon(None) # Limpiar cualquier icono anterior
            return
        if not imageFile.isFile():
            print "Error: La ruta proporcionada no apunta a un archivo válido: %s" % imagePath
            label.setIcon(None)
            return

        # Crea un ImageIcon a partir de la URL del archivo
        # Es más robusto usar URL para ImageIcon, ya que maneja rutas relativas y absolutas
        imageUrl = imageFile.toURI().toURL()
        icon = ImageIcon(imageUrl)

        # Establece el icono en el JLabel
        label.setIcon(icon)
        print "Imagen cargada exitosamente en la etiqueta: %s" % imagePath

    except Exception as e:
        print "Error al cargar la imagen: %s" % e
        e.printStackTrace()
        label.setIcon(None) # En caso de error, asegúrate de que el JLabel no tenga un icono roto

def extraer_json_de_markdown(texto_completo):
    """
    Localiza un bloque JSON formateado con Markdown (```json ... ```) en un texto
    sin usar expresiones regulares, lo extrae y devuelve una tupla con el JSON
    encontrado y el texto sin ese JSON.

    Args:
        texto_completo (unicode): La cadena de texto de entrada que puede contener
                                  un bloque JSON en formato Markdown.

    Returns:
        tuple: Una tupla que contiene:
               - El JSON extraído (unicode) si se encuentra, o None si no.
               - El texto original sin el bloque JSON (unicode) si se encuentra,
                 o el texto completo si no se encuentra el JSON.
    """
    # Definir las marcas de inicio y fin del bloque JSON Markdown
    marca_inicio = u'```json'
    marca_fin = u'```'

    # Buscar la posición de la marca de inicio
    pos_inicio = texto_completo.find(marca_inicio)

    # Si se encuentra la marca de inicio
    if pos_inicio != -1:
        # Calcular la posición donde realmente empieza el contenido JSON
        pos_contenido_inicio = pos_inicio + len(marca_inicio)

        # Buscar la posición de la marca de fin, empezando después de la marca de inicio
        pos_fin = texto_completo.find(marca_fin, pos_contenido_inicio)

        # Si se encuentra la marca de fin
        if pos_fin != -1:
            # Extraer el contenido que está entre las marcas
            json_encontrado = texto_completo[pos_contenido_inicio:pos_fin].strip()

            # Construir el texto restante
            # Parte antes del bloque JSON
            texto_antes_json = texto_completo[:pos_inicio].strip()
            # Parte después del bloque JSON
            texto_despues_json = texto_completo[pos_fin + len(marca_fin):].strip()

            # Concatenar las partes para obtener el texto sin el JSON
            texto_sin_json = u''
            if texto_antes_json:
                texto_sin_json += texto_antes_json
            if texto_antes_json and texto_despues_json:
                texto_sin_json += u'\n' # Añadir un salto de línea si ambas partes existen
            if texto_despues_json:
                texto_sin_json += texto_despues_json

            return json_encontrado, texto_sin_json
    
    # Si no se encuentra el patrón completo (inicio y fin), devolver None y el texto original
    return None, texto_completo

BUTTON_PLACEHOLDER = "{component}"

def insertText(editorPane, text, *components): 
    """
    Inserta un texto en la posición actual del cursor de un JEditorPane,
    reemplazando múltiples marcadores '{component}' dentro del texto con los
    componentes proporcionados como argumentos variables, en el orden en que aparecen.
    Si no se proporcionan componentes o no hay más componentes disponibles para
    un marcador, el marcador no se reemplazará y se insertará como texto plano.

    Args:
        editorPane (JEditorPane): El JEditorPane donde se insertará el texto y los componentes.
        text (str): La cadena de texto a insertar, que puede contener múltiples marcadores '{component}'.
        *components (javax.swing.JComponent): Un número variable de argumentos de componentes
                                               que reemplazarán los marcadores.
    """
    doc = editorPane.getDocument() 
    caretPosition = editorPane.getCaretPosition() 

    try:
        # 'components' ahora es una tupla debido a *components.
        # La convertimos a una lista mutable para poder usar pop().
        components_list = list(components)

        # 'current_insertion_point' rastrea la posición actual en el documento donde se insertará el contenido.
        current_insertion_point = caretPosition
        # 'remaining_text' es la parte del texto original que aún no se ha procesado.
        remaining_text = text

        # Bucle principal para procesar el texto y reemplazar los marcadores.
        # Continúa mientras haya marcadores en el texto restante Y haya componentes disponibles.
        while BUTTON_PLACEHOLDER in remaining_text and len(components_list) > 0:
            # Encuentra la posición de la primera ocurrencia del marcador en el 'remaining_text'.
            placeholder_index = remaining_text.find(BUTTON_PLACEHOLDER)

            # Extrae la porción de texto que precede al marcador.
            text_before_placeholder = remaining_text[0:placeholder_index]

            # 1. Insertar el texto que está antes del marcador en el documento.
            doc.insertString(current_insertion_point, text_before_placeholder, None)
            # Avanzar el punto de inserción por la longitud del texto insertado.
            current_insertion_point += len(text_before_placeholder)

            # Obtiene el siguiente componente de la lista (el primero disponible).
            component_to_insert = components_list.pop(0)

            # Establece la alineación vertical del componente dentro de la línea de texto.
            # Un valor de 0.75f (float) intenta centrarlo verticalmente.
            component_to_insert.setAlignmentY(0.75)

            # Crear un conjunto de atributos para el componente.
            component_attrs = SimpleAttributeSet()
            # Asignar el componente a los atributos, lo que permite que el JEditorPane lo renderice.
            StyleConstants.setComponent(component_attrs, component_to_insert)

            # 2. Insertar el componente en el documento. Se representa con un espacio
            # al que se le aplican los atributos especiales que contienen el componente.
            doc.insertString(current_insertion_point, " ", component_attrs)
            # Avanzar el punto de inserción por la longitud del "espacio" del componente.
            current_insertion_point += 1

            # Actualiza 'remaining_text' para que sea la parte del texto original
            # que sigue al marcador que acabamos de procesar.
            remaining_text = remaining_text[placeholder_index + len(BUTTON_PLACEHOLDER):]

        # 3. Después de que el bucle termina (ya no hay marcadores o no hay más componentes),
        # insertar cualquier texto restante en el documento.
        doc.insertString(current_insertion_point, remaining_text, None)
        # Actualizar el punto de inserción final.
        current_insertion_point += len(remaining_text)

        # Mover el cursor del JEditorPane al final de todo el contenido insertado.
        editorPane.setCaretPosition(current_insertion_point) 

    except Exception as e:
        # En caso de cualquier error, imprimir la traza de la pila para depuración.
        print "DEBUG: insertText a petado", e
        e.printStackTrace()

 
def main(**args):
  print "ok"
 

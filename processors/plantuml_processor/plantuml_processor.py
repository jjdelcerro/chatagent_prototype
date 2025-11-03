# -*- coding: utf-8 -*-
"""
Módulo para el procesador de respuestas de tipo 'text'.
Extiende la clase abstracta Processor y maneja las respuestas generales de la IA.
"""
import gvsig

import tempfile
import os
import subprocess
import sys 
from datetime import datetime

from java.awt import Dimension, Font
from javax.swing import SwingWorker, JButton, JLabel
from java.awt.event import ActionListener
from java.awt.event import MouseAdapter, MouseEvent 

from addons.chatagent_prototype.processor import Processor
from addons.chatagent_prototype.utils import loadImageIntoLabel
from addons.chatagent_prototype.gvsigdesktop.utils import showPanel, showImage, addToToolBar

class PlantUMLProcessor(Processor):
    """
    Procesador para respuestas de tipo 'plantuml'.
    """

    def get_type(self):
        """
        Devuelve el tipo de procesador.
        """
        return "plantuml"

    def get_description(self):
        """
        Devuelve una breve descripción de lo que hace este procesador.
        """
        return u"Gestiona consultas generales que involucren la creacion de diagramas usando PlantUML."

    def get_initial_prompt_info(self):
        """
        Devuelve la parte del prompt inicial que describe este procesador.
        """
        return u"""
== Consultas de tipo 'plantuml' ==
  Utilizaras este tipo de respuesta para cualquier consulta que involucre la creacion de 
  Diagramas de Secuencia, Diagramas de Casos de Uso,  Diagramas de Clases, Diagramas de Actividad,
  Diagramas de Componentes o de Diagramas de Relación de Entidades (ERD).
  El campo 'type' debe ser "plantuml".
  Cuando te pida que generes un diagrama entidad relacion usaras el formato de plantuml para entregarmelo. 
  Cuando generes el diagrama usa solo caracters ascii, no incluyas acentos, eñes ni otros caracteres que puedan causar problemas de codificacion.
  Si no puedes generar el diagrama en formato plantuml por alguna razon no uses este formato de respuesta.
  Debe incluir un campo 'diagram' que contendra la definicion en formato PlantUML del diagrama solicitado.
  Generaras un titulo corto y descriptivo de la diagrama que se solicitado, y lo dejaras en el atributo "title" del json que generes.  
  El titulo no deberia tenas mas de 100 caracteres.
  Ejemplo:
  {
   "type": "plantuml",
   "diagram": "\n  @startuml\n  hide circle\n  skinparam linetype ortho\n  \n  entity \"SOPORTES_MODELOS\" {\n    + CODE : BIGINT <<PK>>\n    --\n    DESCRIPTION : VARCHAR(200)\n  }\n  \n  entity \"SOPORTES\" {\n    + CODE : VARCHAR(60) <<PK>>\n    --\n    GEOMETRIA : GEOMETRY(1)\n    MODELO : BIGINT <<FK>>\n    MATERIAL : VARCHAR(60) <<FK>>\n    ROTACION : DECIMAL(5,2)\n  }\n  \n  SOPORTES_MODELOS ||--o{ SOPORTES : MODELO\n  \n  @enduml\n  ", 
   "title": "Diagrama ERD de modelos"
  }
"""

    def process_response(self, chat_panel, user_query, json_response):
        try:
            diagram = json_response.getString("diagram")
            title = json_response.getString("title",u"Diagrama listo")
            executeListener = ButtonActionListener(title, diagram, chat_panel)
            ahora = datetime.now().strftime("%d %b, %H:%M")
            
            button = JButton("Abrir")
            button.setFont(Font("Monospaced", Font.PLAIN, 12))
            button.addActionListener(executeListener)
            
            label = JLabel()
            loadImageIntoLabel(label, gvsig.getResource(__file__, "images/tools-chatagent-adddiagram.png"))
            label.addMouseListener(AddToToolbarListener(executeListener, title))
            label.setToolTipText(title)
            
            chat_panel.append_message(chat_panel.getAgentName(),(u"%s. %s {component} {component}" % (title,ahora)), button, label)
 
        except Exception as e:
            chat_panel.append_message(chat_panel.getAgentName(),u"Error al procesar la respuesta: %s" % e)
            print "Error al procesar la respuesta: %s" % e

class AddToToolbarListener(MouseAdapter):
    def __init__(self, executeListener, tooltip):
        self.executeListener = executeListener
        self.tooltip = tooltip
    def mouseClicked(self, event):
      addToToolBar(self.executeListener, gvsig.getResource(__file__, "images/tools-chatagent-diagram.png"), self.tooltip)

class ButtonActionListener(ActionListener):
    def __init__(self, title, diagram, chat_panel):
        self.title = title
        self.diagram = diagram
        self.chat_panel = chat_panel
    def actionPerformed(self, event=None):
        worker = ExecutionWorker(self.title, self.diagram, self.chat_panel)
        worker.execute()
            
class ExecutionWorker(SwingWorker):
    def __init__(self, title, diagram, chat_panel):
        self.title = title
        self.diagram = diagram
        self.chat_panel = chat_panel
        self.exception = None
        self.image_path = None

    def doInBackground(self):
        try:
            self.image_path = generate_plantuml_image(self.diagram)
        except Exception as e:
            self.exception = e
            print "Error en doInBackground (ExecutionWorker): %s" % e
        return None

    def done(self):
        try:
            if self.exception:
                self.chat_panel.append_message(self.chat_panel.getAgentName(),u"Error preparando el diagrama.")
            else:
                showImage(self.title, self.image_path, size=Dimension(400,400))
        except Exception as e:
            self.chat_panel.append_message(self.chat_panel.getAgentName(),u"Error al mostrar los resultados.")
            print "Error en done (ExecutionWorker): %s" % e

def generate_plantuml_image(plantuml_description):
    puml_file_path = None
    image_file_path = None

    try:
        # 1. Crear un archivo temporal para la descripción PlantUML
        # mkstemp devuelve un descriptor de archivo (fd) y la ruta del archivo.
        # Usamos suffix=".puml" para la extensión y prefix="plantuml_" para el nombre.
        fd, puml_file_path = tempfile.mkstemp(suffix=".puml", prefix="plantuml_")
        os.close(fd) # Es importante cerrar el descriptor de archivo inmediatamente
                     # para que PlantUML pueda leerlo.

        #print "Guardando descripción PlantUML en archivo temporal:", puml_file_path

        # Escribir la descripción PlantUML en el archivo temporal
        # En Jython 2.7, 'w' es suficiente para texto.
        with open(puml_file_path, "w") as f:
            f.write(plantuml_description)

        # 2. Determinar la ruta de salida para la imagen
        # PlantUML generará la imagen en el mismo directorio que el archivo .puml
        # y con el mismo nombre base, pero con extensión .png por defecto.
        output_dir = os.path.dirname(puml_file_path)
        base_name = os.path.basename(puml_file_path)
        # Extraer el nombre sin extensión y añadir .png
        image_file_name = os.path.splitext(base_name)[0] + ".png"
        image_file_path = os.path.join(output_dir, image_file_name)

        # 3. Construir el comando para ejecutar PlantUML
        # Asumimos que 'plantuml' está disponible en el PATH del sistema como un comando.
        # El argumento "-o" especifica el directorio de salida.
        command = ["plantuml", "-o", output_dir, puml_file_path]

        #print "Ejecutando comando PlantUML:", " ".join(command)

        # 4. Ejecutar el comando PlantUML
        # subprocess.check_call lanzará una CalledProcessError si el comando
        # devuelve un código de salida no cero (indicando un error).
        # Esto es preferible a subprocess.call para un manejo de errores más robusto.
        subprocess.check_call(command)

        # 5. Verificar si la imagen fue generada y devolver su ruta
        if os.path.exists(image_file_path):
            #print "Imagen PlantUML generada con éxito en:", image_file_path
            return image_file_path
        else:
            print u"Error: La imagen PlantUML no se generó o no se encontró en:", image_file_path
            return None

    except subprocess.CalledProcessError as e:
        print u"Error al ejecutar PlantUML. Código de salida:", e.returncodeu
        print u"Comando ejecutado:", e.cmd
        # En Jython 2.7, e.output y e.stderr pueden no estar disponibles directamente en CalledProcessError
        # dependiendo de la versión exacta y cómo se configure subprocess.
        # Puedes capturar la salida con subprocess.check_output si necesitas verla.
        print u"Asegúrate de que el comando 'plantuml' esté en tu PATH del sistema."
        return None
    except IOError as e:
        print u"Error de E/S al manejar archivos temporales:", e
        return None
    except Exception as e:
        print u"Ocurrió un error inesperado:", e
        return None
    finally:
        # Limpiar el archivo .puml temporal, independientemente de si hubo un error o no.
        if puml_file_path and os.path.exists(puml_file_path):
            try:
                os.remove(puml_file_path)
                #print "Archivo temporal .puml eliminado:", puml_file_path
            except Exception as e:
                print u"Advertencia: No se pudo eliminar el archivo temporal .puml:", e


def main(**args):
  print "ok"
 

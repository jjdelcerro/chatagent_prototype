# -*- coding: utf-8 -*-
"""
Módulo para el procesador de respuestas de tipo 'chart_processor'.
Contiene la lógica para ejecutar consultas SQL, procesar el ResultSet
y generar gráficos utilizando la librería XChart.
"""
import gvsig

from javax.swing import JPanel, SwingWorker, JButton, JLabel
from java.awt import BorderLayout, Dimension, Font
from java.awt.event import ActionListener
from java.awt.event import MouseAdapter 
from datetime import datetime

from org.knowm.xchart.internal.chartpart import Chart
from org.knowm.xchart.style import Styler
import org.knowm.xchart
import org.knowm.xchart.style
import org.knowm.xchart.style.colors
import org.knowm.xchart.style.lines
import org.knowm.xchart.style.markers
import org.knowm.xchart.style.theme

from addons.chatagent_prototype.processor import Processor
from addons.chatagent_prototype.utils import loadImageIntoLabel
from addons.chatagent_prototype.gvsigdesktop.utils import executeSQL, showPanel, addToToolBar

class ChartProcessor(Processor):
    """
    Procesador para respuestas de tipo 'chart'.
    """

    def get_type(self):
        return "chart"

    def get_description(self):
        return u"Genera graficos de barras o tartas a partir de los datos."

    def get_initial_prompt_info(self):
        return u"""
== Consultas de tipo 'chart' ==
  Utilizaras este tipo de respuesta para cualquier consulta que involucre la creacion de graficos de barra o de tarta.
  Para este tipo de respuesta tu tarea consiste en un proceso de generación en **tres pasos secuenciales**. 
  Debes generar tres salidas distintas y completas para cada uno de los pasos. 
  
  Las reglas y notas descritas para el tratamiento de consultas de tipo chart deben aplicarse solo cuando se este
  generando este tipo de respuesta.
 
  Paso 1: Generacion de la SQL
  Generaras una consulta SQL que devolvera los datos necesarios para crear el gráfico solicitado por el usuario.
  Los datos obtenidos de esta consulta se pasaran a la funcion Jython que construyas en el paso 3.
 
  Paso 2: Generacion de la descipcion de la estructura del ResultSet obtenido a partir de la SQL del paso 1.
  Especificación para la Descripción de la Estructura del ResultSet.
  - Esta descripción debe detallar las columnas del ResultSet generado por la consulta SQL del Paso 1.
  - Formato: Un JSON Array de objetos. Cada objeto en el array debe describir una columna.
  Estructura de cada objeto:
    {
      "name": "nombre_columna_en_el_ResultSet",
       "type": "Tipo_Sugerido_para_Jython",  // El tipo de dato en Jython (ej: String,int, double)
       "source_sql_type": "Tipo_SQL_Original" // Opcional: el tipo de dato original en la DB
    }
    Ejemplo de JSON esperado para un ResultSet con columnas 'nombre' y 'poblacion':
      [
         { "name": "nombre", "type": "String", "source_sql_type": "VARCHAR" },
         { "name": "poblacion", "type": "double", "source_sql_type": "INTEGER" }
    ]
    
  Paso 3. Generacion de una funcion jython que construya el gráfico solicitado
  En este paso generaras una funcion en jython 2.7 que tomando como datos de entrada el ResultSet obtenido
  en el paso 1 genere un grafico de barras o tartas deacuerdo con las espcificaciones del usuario.
  Especificación para la Función Jython a Generar
  - Nombre de la función: generate_chart
  - Lenguaje: Jython 2.7
  - Entrada (Argumento): 'resultSet' (un objeto de tipo java.sql.ResultSet).
  - Salida (Valor de retorno): Un objeto de tipo org.knowm.xchart.internal.Chart.
  - Biblioteca a utilizar: XChart (org.knowm.xchart.*) version 3.8.1 IMPORTANTE!!. 
  - MUY IMPORTANTE!! incluye los imports necesarios **DENTRO DE LA FUNCION**, en las primeras lineas.
  - Asegurate de que incluyas todos los imports de todas las clases de xchart que uses.
  - Por favor, asegúrate de importar las clases antes de usarlas.
  - Cuando generes código, prefiero que uses la sintaxis de from ... import ... y luego la clase directamente.
  - Siempre haz el import explícito de la clase antes de referenciarla.
  - Sigue la convención de importar el tipo o clase  y luego usarlo directamente. 
  - No debes generar codigo antes y despues de la funcion.
  - No generes comentarios en el codigo de la funcion, ni dentro ni fuera de ella.
  - Para manejar tipos basicos (como string, double, int...) no uses metodos java, manejalos usando funcionalidades de jython.
  - No uses el metodo setHasBarBorders.
  - No incluyas comentarios en la funcion.
  - Dentro del código Jython las cadenas que incluyan caracteres especiales (como ó, ñ, etc.) deben ir prefijadas con u, por ejemplo: u'Mi cadena'."
  - Dentro del código Jython asegúrate de que todas las cadenas de texto sean Unicode.
  Requisitos Clave:
  - Iterar a través del 'resultSet'.
  - **¡Crucial! Procesar las columnas y tipos de datos basándote *precisamente* en la estructura del ResultSet generada en el Paso 2.**
  - Utilizar la API de XChart para crear el Dataset y el objeto Chart.
  - Configurar el gráfico según la Petición del Usuario.
  - Asegurarse de cerrar el 'resultSet' y su Statement (try...finally).
  - Devolver el objeto Chart.

  El json generado debera tener los siguientes campos:
  - "type", con el valor "chart"
  - "sql", con la sql generada en el paso 1.
  - "result_set_schema" con el json generado en el paso 2.
  - "function" un valor de cadena que contendra la funcion generada en el paso 3.
  - "title", con un descripcion corta que identifique el grafico que se ha pedido. El titulo no deberia tenas mas de 100 caracteres.

  Ejemplo de respuesta:
   {
  "type": "chart",
  "sql": "SELECT SM.DESCRIPTION, COUNT(S.CODE) AS UsoDeSoportes FROM PUBLIC.SOPORTES AS S JOIN PUBLIC.SOPORTES_MODELOS AS SM ON S.MODELO = SM.CODE GROUP BY SM.DESCRIPTION LIMIT 1000;",
  "result_set_schema": [
    {
      "name": "DESCRIPTION",
      "type": "String",
      "source_sql_type": "VARCHAR"
    },
    {
      "name": "UsoDeSoportes",
      "type": "double",
      "source_sql_type": "BIGINT"
    }
  ],
  "title": "Usos de modelos de soporte",
  "function": "\\ndef generate_chart(resultSet):\\n    from org.knowm.xchart import CategoryChartBuilder\\n    from org.knowm.xchart.style.Styler import LegendPosition\\n    from java.util import ArrayList\\n\\n    categories = ArrayList()\\n    values = ArrayList()\\n\\n    try:\\n        while resultSet.next():\\n            category = resultSet.getString(\\"DESCRIPTION\\")\\n            value = resultSet.getDouble(\\"UsoDeSoportes\\")\\n            categories.add(category)\\n            values.add(value)\\n    finally:\\n        if resultSet:\\n            resultSet.close()\\n\\n    chart = CategoryChartBuilder().width(800).height(600).title(\\"Usos de modelos de soporte\\").xAxisTitle(\\"Modelo de Soporte\\").yAxisTitle(\\"N\\u00famero de Usos\\").build()\\n\\n    chart.getStyler().setLegendPosition(LegendPosition.InsideNW)\\n    chart.getStyler().setHasBarBorders(True)\\n\\n    chart.addSeries(\\"N\\u00famero de Usos\\", categories, values)\\n\\n    return chart  \\n  "
 }
"""

    def process_response(self, chat_panel, user_query, json_response):
        try:
            title = json_response.getString("title", u"Gráfico listo")
            executeListener = ButtonActionListener(json_response, chat_panel)
            ahora = datetime.now().strftime("%d %b, %H:%M")

            button = JButton("Abrir")
            button.setFont(Font("Monospaced", Font.PLAIN, 12))
            button.addActionListener(executeListener)
            
            
            label = JLabel()
            loadImageIntoLabel(label, gvsig.getResource(__file__, "images/tools-chatagent-addchart.png"))
            label.addMouseListener(AddToToolbarListener(executeListener, title))
            label.setToolTipText(title)
            
            chat_panel.append_message(chat_panel.getAgentName(),(u"%s. %s {component} {component}" % (title,ahora)), button, label)
            
        except Exception as e:
            chat_panel.append_message(chat_panel.getAgentName(),u"Error al procesar la respuesta: %s" % e)
            print u"Error al procesar la respuesta: %s" % e

class AddToToolbarListener(MouseAdapter):
    def __init__(self, executeListener, tooltip):
        self.executeListener = executeListener
        self.tooltip = tooltip
    def mouseClicked(self, event=None):
      addToToolBar(self.executeListener, gvsig.getResource(__file__, "images/tools-chatagent-chart.png"), self.tooltip)

class ButtonActionListener(ActionListener):
    def __init__(self, json, chat_panel):
       self.json = json
       self.chat_panel = chat_panel
    def actionPerformed(self, event=None):
        worker = ExecutionWorker(self.json, self.chat_panel)
        worker.execute()
            
class ExecutionWorker(SwingWorker):
    def __init__(self, json, chat_panel):
        self.json = json
        self.chat_panel = chat_panel
        self.resultSet = None
        self.chart = None
        self.exception = None

    def doInBackground(self):
        try:
            # Paso 1: Ejecutar la consulta SQL
            sql_query = self.json.getString("sql")
            self.resultSet = executeSQL(self.chat_panel.getDataModel(),sql_query)
            if not self.resultSet:
                raise Exception(u"La ejecución de la consulta SQL no devolvió un ResultSet.")

            generate_chart_code = self.json.getString("function")

            print "DEBUG: generate_char:\n",generate_chart_code
            
            # Paso 2 y 3: Ejecutar el código Jython para generar el gráfico
            # Creamos un diccionario local para la ejecución del código
            local_scope = {}
            # Ejecutamos el código de la función en el ámbito local
            exec generate_chart_code in globals(), local_scope

            # Obtenemos la función generada y la llamamos con el ResultSet
            generate_chart = local_scope.get("generate_chart")
            if not generate_chart:
                raise Exception(u"La función 'generate_chart' no se encontró en el código Jython proporcionado.")

            self.chart = generate_chart(self.resultSet)
            if not self.chart:
                raise Exception(u"La función 'generate_chart' no devolvió un objeto Chart.")

        except Exception as e:
            self.exception = e
            print u"Error en doInBackground (ChartGenerationWorker): %s" % e
        finally:
            # Asegurarse de cerrar el ResultSet si no se hizo dentro de generate_chart
            if self.resultSet:
                try:
                    self.resultSet.close()
                except Exception as e:
                    print u"Error al cerrar ResultSet en finally (ChartGenerationWorker): %s" % e
        return None

    def done(self):
        try:
            if self.exception:
                self.chat_panel.append_message(self.chat_panel.getAgentName(),u"Error al generar el gráfico: %s" % self.exception)
            elif self.chart:
                # Importar XChartPanel aquí para asegurar que se usa en el EDT
                from org.knowm.xchart import XChartPanel
                title = self.json.getString("title","Gráfica")
                chart_panel = XChartPanel(self.chart)
                chart_panel.setPreferredSize(Dimension(800, 600)) # Tamaño preferido para la ventana
                showPanel(chart_panel, title)
            else:
                self.chat_panel.append_message(self.chat_panel.getAgentName(),u"La generación del gráfico no devolvió un Chart.")
        except Exception as e:
            self.chat_panel.append_message(self.chat_panel.getAgentName(),u"Error al mostrar el gráfico: %s" % e)
            print u"Error en done (ChartGenerationWorker): %s" % e

def main(**args):
  print "chart_processor ok"


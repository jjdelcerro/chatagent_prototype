# -*- coding: utf-8 -*-
"""
Módulo para el procesador de respuestas de tipo 'sql_processor'.
Contiene la lógica para ejecutar consultas SQL generadas por la IA y mostrar los resultados en una tabla.
"""
import gvsig

import java
from javax.swing import JPanel, JTable, JScrollPane, BorderFactory, SwingWorker,JButton
from javax.swing.table import AbstractTableModel
from java.awt import BorderLayout, Dimension, Font
from java.lang import String, Class, Object
from java.sql import ResultSet
from java.awt.event import ActionListener
from javax.swing import JLabel
from java.awt.event import MouseAdapter, MouseEvent 

from datetime import datetime

from addons.chatagent_prototype.processor import Processor
from addons.chatagent_prototype.utils import loadImageIntoLabel
from addons.chatagent_prototype.gvsigdesktop.utils import executeSQL, showPanel, addToToolBar
from addons.chatagent_prototype.processors.sql_processor.resultsetpanel import ResultSetTablePanel

class SqlProcessor(Processor):
    """
    Procesador para respuestas de tipo 'sql_processor'.
    Extrae la consulta SQL, la ejecuta y muestra los resultados en una tabla.
    """
    def get_type(self):
        """
        Devuelve el tipo de procesador.
        """
        return u"sql"

    def get_description(self):
        """
        Devuelve una breve descripción de lo que hace este procesador.
        """
        return u"Permite realizar consultas SQL en lenguaje natural."

    def get_initial_prompt_info(self):
        """
        Devuelve la parte del prompt inicial que describe este procesador.
        """
        return u"""
== Consultas de tipo 'sql' ==
  Utilizaras este tipo de respuesta para cualquier consulta que involucre la creacion de una 
  consulta SQL contra las tablas a las que tienes acceso.
  El campo 'type' debe ser "sql".
  Debe incluir un campo 'sql' con la sentencia SQL a ejecutar, y solo incluira la sentencia SQL, sin comentarios, explicaciones o cualquier otro caracter que no forma parte de la sentencia SQL.
  La sentencia SQL debe ser de tipo SELECT y limitar el numero de resultados a 1000.
  NUNCA uses DISTINCT. 
  Si has de usar distinct en su lugar usa group by si es una altenativa valida.
  Tampoco uses la funcion ST_DWINTHIN.
  Utiliza joins frente a subselects siempre que sea posible.
  Rellena el campo "esValorEscalar" del json con un true en caso de que estimes que la consulta SQL devuelbe un valor escalar y a false en caso contrario. 
  Usa comillas dobles cuando te refieras a un campo o a una tabla.
  No uses el esquema al construir sentencias SQL.
  Si no te lo indica el usuario de forma explicita no le muestres informacion sobre las SQL que has generado.
  Cuando pienses que un valor es categorizado pero no tengas su diccionario, no inventes valores para el.
  Sobre los campos categorizados:
  - No tengas en cuenta distincion entre mayusculas y minusculas. Compara los valores en mayusculas.
  - Cuando te pregunten por el valor de un campo categorizado comparalo con los valores de la tabla que define la categoria
  - Siempre que se pregunte por un campo categorizado haz busquedas que se parezca, no que sea igual.
  Generaras un titulo corto y descriptivo de la consulta que se haya realizado, y lo dejaras en el atributo "title" del json que generes.
  El titulo no deberia tenas mas de 100 caracteres.
  Ejemplo: 
  {
    "type": "sql",
    "sql": "SELECT EMPLOYEE_ID, FIRST_NAME, LAST_NAME FROM EMPLOYEES WHERE DEPARTMENT_ID = 10 LIMIT 1000;",
    "title": "Empleados por departamento",
    "esValorEscalar": false
  }
"""

    def process_response(self, chat_panel, user_query, json_response ):
        try:
            sql_query = json_response.getString("sql")
            esValorEscalar = json_response.getBoolean("esValorEscalar", False)
            title = json_response.getString("title", u"Resultados de la consulta")
            if esValorEscalar:
              worker = SqlExecutionWorker(title, sql_query, chat_panel)
              worker.execute()
            else:
              executeListener = ExecuteListener(title, sql_query, chat_panel)
              button = JButton("Abrir")
              button.setFont(Font("Monospaced", Font.PLAIN, 12))
              button.addActionListener(executeListener)
    
              label = JLabel()
              loadImageIntoLabel(label, gvsig.getResource(__file__, "images/tools-chatagent-addsql.png"))
              label.addMouseListener(AddToToolbarListener(executeListener, title))
              label.setToolTipText(title)
              ahora = datetime.now().strftime("%d %b, %H:%M")
              chat_panel.append_message(chat_panel.getAgentName(),(u"%s. %s {component} {component}" % (title,ahora)), button, label)

        except Exception as e:
            chat_panel.append_message(chat_panel.getAgentName(),"uError al procesar la respuesta: %s" % e)
            print "Error al procesar la respuesta: %s" % e

class AddToToolbarListener(MouseAdapter):
    def __init__(self, executeListener, tooltip):
        self.executeListener = executeListener
        self.tooltip = tooltip
    def mouseClicked(self, event):
      addToToolBar(self.executeListener, gvsig.getResource(__file__, "images/tools-chatagent-sql.png"), self.tooltip)
        
class ExecuteListener(ActionListener):
    def __init__(self, title, sql_query, chat_panel):
        self.title= title
        self.sql_query = sql_query
        self.chat_panel = chat_panel
    def actionPerformed(self, event=None):
        worker = SqlExecutionWorker(self.title, self.sql_query, self.chat_panel)
        worker.execute()
            
class SqlExecutionWorker(SwingWorker):
    def __init__(self, title, sql_query, chat_panel):
        self.title= title
        self.sql_query = sql_query
        self.chat_panel = chat_panel
        self.resultSet = None
        self.exception = None

    def doInBackground(self):
        try:
            self.resultSet = executeSQL(self.chat_panel.getDataModel(),  self.sql_query)
        except Exception as e:
            self.exception = e
            print "Error en doInBackground (SqlExecutionWorker): %s" % e
        return None # SwingWorker requiere un retorno

    def done(self):
        try:
            if self.exception:
                self.chat_panel.append_message(self.chat_panel.getAgentName(),u"Error al ejecutar la consulta.")
            elif isinstance(self.resultSet, ResultSet):
                table_panel = ResultSetTablePanel(self.resultSet)
                showPanel(table_panel, self.title)
            elif self.resultSet == None:
              self.chat_panel.append_message(self.chat_panel.getAgentName(),u"No se han obtenido resultados.")
            else:
                s = str(self.resultSet)
                if s:
                  self.chat_panel.append_message(self.chat_panel.getAgentName(),u"%s: %s" % (self.title,s))
                else:
                  self.chat_panel.append_message(self.chat_panel.getAgentName(),u"No se han obtenido resultados")
        except Exception as e:
            self.chat_panel.append_message(self.chat_panel.getAgentName(),u"Error al mostrar los resultados de la consulta.")
            print "Error en done (SqlExecutionWorker): %s" % e

def main(**args):
  print "ok"
  
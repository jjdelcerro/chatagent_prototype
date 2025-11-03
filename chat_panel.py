# -*- coding: utf-8 -*-
"""
Módulo que implementa el panel principal del chat.
Carga el diseño desde chatpanel.xml.txt y gestiona la interacción del usuario
con la IA de Gemini, utilizando los distintos procesadores de respuesta.
"""

import gvsig
from gvsig.libs.formpanel import FormPanel

import sys

from javax.swing import JPanel, JButton, JTextArea, JScrollPane, JPopupMenu, JMenuItem
from javax.swing.text import DefaultEditorKit, SimpleAttributeSet, StyleConstants
from java.awt import BorderLayout, Dimension, Font
from java.awt.event import ActionListener, MouseAdapter
from java.io import FileInputStream, StringReader
from javax.json import Json
from javax.swing import SwingWorker
from java.lang import StringBuilder, Exception
from javax.swing import JTextArea, DefaultComboBoxModel
from java.awt.event import KeyAdapter, KeyEvent
from javax.swing.text import StyledEditorKit

from java.io import StringReader
from javax.json import Json

import addons.chatagent_prototype.utils
import addons.chatagent_prototype.config

from addons.chatagent_prototype.gvsigdesktop.utils import getAvailableDataModels, getDDL, getCurrentViewBboxAsWKT

class ChatPanel(FormPanel, ActionListener):
    """
    Panel principal de la aplicación de chat.
    """
    def __init__(self, aiclient):
        FormPanel.__init__(self, gvsig.getResource(__file__, "chat_panel.xml"))
        self.aiclient = aiclient
        self.dataModel = None
        
        self.processors = {} # Diccionario para almacenar los procesadores registrados
        self.is_first_interaction = True # Para controlar si se envía el prompt inicial
        
        self._setup_components()
        self._add_context_menus()

        self.updateDataModels()

        self.asJComponent().setPreferredSize(Dimension(700, 500)) 
        
        self.append_message("""
------------------------------------------------------------------------  

\u26A0\uFE0F Este asistente es una prueba conceptual con funcionalidades limitadas. 

------------------------------------------------------------------------  
""")
        
    def _setup_components(self):
        self.chatHistoryTextArea = self.txtChatHistoryTextArea
        self.userInputTextArea = self.txtUserInputTextArea
        self.sendButton = self.btnSendButton

        if self.chatHistoryTextArea:
            self.chatHistoryTextArea.setFont(Font("Monospaced", Font.PLAIN, 12))
            self.chatHistoryTextArea.setEditable(False) # Asegurarse de que no sea editable
            self.chatHistoryTextArea.setEditorKit(StyledEditorKit())
        
        if self.userInputTextArea:
            self.userInputTextArea.setFont(Font("Monospaced", Font.PLAIN, 12))
            configurar_shiftenter(self.userInputTextArea, self._send_message )

        if self.sendButton:
            self.sendButton.addActionListener(self) # Listener para el botón de enviar

    def updateDataModels(self, *args):
      model = DefaultComboBoxModel()
      for dataModel in getAvailableDataModels():
          model.addElement(dataModel)
      self.cboModelo.setModel(model)
      self.cboModelo.setSelectedIndex(-1)

    def cboModelo_change(self, *args):
      modelo = self.cboModelo.getSelectedItem()
      if modelo:
        self.setDataModel(modelo.getValue())

    def setDataModel(self, dataModel):
      if self.dataModel == dataModel:
          return
      self.dataModel = dataModel
      self.aiclient.resetHistory()
      self.is_first_interaction = True
      self.chatHistoryTextArea.setText("")
      
    def getDataModel(self):
      return self.dataModel
      
    def btnConnectToModel_click(self,event=None):
      showConnectToDatabaseWorkspaceDialog(self.updateDataModels)

    def _add_context_menus(self):
        """
        Añade menús contextuales (copiar, cortar, pegar) a las áreas de texto.
        """
        # Menú contextual para el historial del chat (solo copiar)
        if self.chatHistoryTextArea:
            history_popup = JPopupMenu()
            copy_item = JMenuItem("Copiar")
            copy_item.addActionListener(DefaultEditorKit.CopyAction())
            history_popup.add(copy_item)
            self.chatHistoryTextArea.setComponentPopupMenu(history_popup)

        # Menú contextual para la entrada del usuario (cortar, copiar, pegar)
        if self.userInputTextArea:
            input_popup = JPopupMenu()
            cut_item = JMenuItem("Cortar")
            cut_item.addActionListener(DefaultEditorKit.CutAction())
            copy_item = JMenuItem("Copiar")
            copy_item.addActionListener(DefaultEditorKit.CopyAction())
            paste_item = JMenuItem("Pegar")
            paste_item.addActionListener(DefaultEditorKit.PasteAction())
            
            input_popup.add(cut_item)
            input_popup.add(copy_item)
            input_popup.add(paste_item)
            self.userInputTextArea.setComponentPopupMenu(input_popup)

    def register_processor(self, processor):
        """
        Registra un procesador de respuesta.
        
        Args:
            processor (processor.Processor): Una instancia de una subclase de Processor.
        """
        self.processors[processor.get_type()] = processor
        print "Procesador registrado: %s" % processor.get_type()

    def append_message(self, sender, message, *components):
        text = "[%s]: %s\n" % (sender, message)
        
        doc = self.chatHistoryTextArea.getDocument()
        endPosition = doc.getLength()
        self.chatHistoryTextArea.setCaretPosition(endPosition)
        
        utils.insertText(self.chatHistoryTextArea,text, *components)
        # Desplazar al final
        self.chatHistoryTextArea.setCaretPosition(self.chatHistoryTextArea.getDocument().getLength())

    def getAgentName(self):
        return "Sistema"

    def _build_initial_prompt_string(self):
        if not self.dataModel or not self.is_first_interaction:
            return None
        supported_query_types = StringBuilder()
        detailed_query_descriptions = StringBuilder()
        for processor_type in sorted(self.processors.keys()): # Ordenar para una salida consistente
            processor = self.processors[processor_type]
            supported_query_types.append("- %s: %s\n" % (processor.get_type(), processor.get_description()))
            detailed_query_descriptions.append(processor.get_initial_prompt_info())
        ddl_info = getDDL(self.dataModel)
        viewbbox = getCurrentViewBboxAsWKT()
        full_prompt_text = config.BASE_INITIAL_PROMPT.replace("{supported_query_types}", supported_query_types.toString())
        full_prompt_text = full_prompt_text.replace("{ddl_info}", ddl_info)
        full_prompt_text = full_prompt_text.replace("{current_view_bbox}", viewbbox)
        full_prompt_text = full_prompt_text.replace("{detailed_query_descriptions}", detailed_query_descriptions.toString())

        print full_prompt_text
        
        self.is_first_interaction = False
        return full_prompt_text

    def actionPerformed(self, event):
        """
        Maneja los eventos de acción (e.g., clic en el botón Enviar).
        """
        if event.getSource() == self.sendButton or event.getSource() == self.userInputTextArea:
            self._send_message()

    def _send_message(self):
        """
        Envía el mensaje del usuario a Gemini y procesa la respuesta.
        Compondrá el prompt completo (inicial + histórico + usuario) antes de enviarlo.
        """
        user_input = self.userInputTextArea.getText().strip()
        if not user_input:
            return

        self.append_message("Usuario", user_input)
        self.userInputTextArea.setText("") # Limpiar el área de entrada
        self.sendButton.setEnabled(False) # Deshabilitar el botón mientras se procesa
        self.userInputTextArea.setEnabled(False) # Deshabilitar el área de texto

        # Usar SwingWorker para la llamada a la API
        worker = GeminiApiWorker(user_input, self.is_first_interaction, self.processors, self)
        worker.execute()
        
class GeminiApiWorker(SwingWorker):
    def __init__(self, user_input, is_first_interaction, processors, chat_panel):
        self.user_input = user_input
        self.is_first_interaction = is_first_interaction
        self.processors = processors
        self.chat_panel = chat_panel
        self.aiclient = chat_panel.aiclient
        self.response_json = None
        self.exception = None

    def doInBackground(self):
        try:
            # Construir el prompt inicial si es la primera interacción
            initial_prompt_text = ""
            if self.is_first_interaction:
                initial_prompt_text = self.chat_panel._build_initial_prompt_string()
            s = utils.send_message(self.aiclient,self.user_input,initial_prompt_text)
            # Después de la primera interacción, no se vuelve a enviar el prompt inicial completo
            self.is_first_interaction = False
            s = s.strip()
            s, text = utils.extraer_json_de_markdown(s)
            if text:
               self.chat_panel.append_message(self.chat_panel.getAgentName(), text)
            print u"DEBUG: respuesta: %s\n " % s
            
            # Parsear la respuesta JSON
            json_reader = Json.createReader(StringReader(s))
            self.response_json = json_reader.readObject()
            json_reader.close()

        except Exception as e:
            self.exception = e
            print "Error en doInBackground (GeminiApiWorker): %s" % e
            import traceback
            traceback.print_exc(file=sys.stdout)
        return None

    def done(self):
        try:
            if self.exception:
                self.chat_panel.append_message(self.chat_panel.getAgentName(),
                                               u"Error al comunicarse con Gemini: %s" % self.exception.getMessage())
            elif self.response_json:
                response_type = self.response_json.getString("type")
                processor = self.chat_panel.processors.get(response_type)
                if processor:
                    processor.process_response(self.chat_panel, self.user_input, self.response_json)
                else:
                    self.chat_panel.append_message(self.chat_panel.getAgentName(),
                                                   u"Tipo de respuesta desconocido: %s" % response_type)
                    self.chat_panel.append_message(self.chat_panel.getAgentName(),
                                                   u"Respuesta completa: %s" % self.response_json.toString())
            else:
                self.chat_panel.append_message(self.chat_panel.getAgentName(), u"No se ha recibido una respuesta valida")
        except Exception as e:
            self.chat_panel.append_message(self.chat_panel.getAgentName(),u"Error al procesar la respuesta: %s" % e)
            print "Error en done (GeminiApiWorker): %s" % e
            import traceback
            traceback.print_exc(file=sys.stdout)
        finally:
            self.chat_panel.sendButton.setEnabled(True) # Habilitar el botón
            self.chat_panel.userInputTextArea.setEnabled(True) # Habilitar el área de texto
            self.chat_panel.userInputTextArea.requestFocusInWindow() # Darle el foco


def configurar_shiftenter(textarea, funcion):
    textarea.addKeyListener(ShiftEnterKeyListener(textarea, funcion))

class ShiftEnterKeyListener(KeyAdapter):
    def __init__(self, textarea, funcion):
        self.textarea = textarea
        self.funcion = funcion

    def keyPressed(self, event):
        if event.getKeyCode() == KeyEvent.VK_ENTER and event.isShiftDown():
            event.consume()  # Consume el evento para evitar que se inserte un salto de línea
            self.funcion()


def main(**args):
  print "ok"
# encoding: utf-8

import gvsig

from gvsig import getResource

from java.io import File
from org.gvsig.andami import PluginsLocator
from org.gvsig.app import ApplicationLocator
from org.gvsig.scripting.app.extension import ScriptingExtension
from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.swing.api import ToolsSwingLocator

from addons.chatagent_prototype import chatagent 

class ChatAgentExtension(ScriptingExtension):
  def __init__(self):
    pass

  def canQueryByAction(self):
    return True

  def isEnabled(self,action):
    return True

  def isVisible(self,action):
    return True
    
  def execute(self,actionCommand, *args):
    actionCommand = actionCommand.lower()
    if actionCommand == "tools-chatagent":
      chatagent.main()

def selfRegister():
  application = ApplicationLocator.getManager()

  #
  # Registramos las traducciones
  i18n = ToolsLocator.getI18nManager()
  i18n.addResourceFamily("text",File(getResource(__file__,"i18n")))

  #
  # Registramos los iconos en el tema de iconos
  icon = File(getResource(__file__,"images","tools-chatagent.png")).toURI().toURL()
  iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()
  iconTheme.registerDefault("scripting.ChatAgentExtension", "action", "tools-chatagent", None, icon)

  #
  # Creamos la accion 
  extension = ChatAgentExtension()
  actionManager = PluginsLocator.getActionInfoManager()
  action = actionManager.createAction(
    extension, 
    "tools-chatagent", # Action name
    u"ChatAgent", # Text
    "tools-chatagent", # Action command
    "tools-chatagent", # Icon name
    None, # Accelerator
    902006100, # Position 
    u"Chat con el asistente virtual" # Tooltip
  )
  action = actionManager.registerAction(action)
  application.addMenu(action, u"tools/Chat con el asistente virtual")
  application.getMainFrame().addTool(action, "Chat con el asistente virtual")
      
def main(*args):
   selfRegister()
   
# -*- coding: utf-8 -*-

import gvsig

from java.lang import StringBuilder

from java.util import Properties
from java.util import Collections
from java.util import UUID

from java.io import FileInputStream
from java.io import File 
from java.io import StringReader
from java.net import URL 

from java.awt import Dimension
from java.awt import GridBagConstraints
from javax.swing import JFrame, JPanel
from javax.swing import JLabel, ImageIcon
import javax.swing.JComponent

from javax.json import Json

from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.dispose import DisposeUtils
from org.gvsig.tools.swing.api import ToolsSwingLocator
from org.gvsig.tools.swing.api.windowmanager import WindowManager
from org.gvsig.tools.swing.api import ToolsSwingLocator
from org.gvsig.tools.swing.api.windowmanager import WindowManager, WindowManager_v2
from org.gvsig.tools.util import ToolsUtilLocator
from org.gvsig.tools.util import LabeledValueImpl

from org.gvsig.fmap.dal import DALLocator
from org.gvsig.fmap.dal.impl import DatabaseWorkspaceStoresRepository

from org.gvsig.andami import PluginsLocator
from org.gvsig.andami.plugins import Extension
from org.gvsig.app import ApplicationLocator

from org.gvsig.scripting.app.extension import ScriptingExtension


import os
import json

MODEL_NAME="TALLER_MODELOS_DATOS"

def executeSQL(dataModel, sql):
    print "DEBUG: executeSQL dataModel: %s, SQL:  %s" % (dataModel, sql)
    server = None
    try:
      dataManager =  DALLocator.getDataManager()
      repo = dataManager.getStoresRepository().getSubrepository(dataModel)
      serverparams = repo.getServerParameters()
      server = dataManager.openServerExplorer(serverparams.getProviderName(), serverparams)    
      r = server.execute(sql)
      return r
    finally:
      DisposeUtils.dispose(server)

def showPanel(panel, title):
    manager = ToolsSwingLocator.getWindowManager()
    if not isinstance(panel,javax.swing.JComponent):
      panel = panel.asJComponent()
    manager.showWindow(panel, title, WindowManager.MODE.WINDOW)

def __getValuesOfDic(repo, table, fk):
  store = None
  try:
    d = dict()
    store = repo.getStore(table)
    ft = store.getDefaultFeatureType()
    keyname = ft.getPrimaryKey()[0].getName()
    for f in store.getFeatureSet():
      key = f.get(keyname)
      value = fk.getLabel(None,f)
      d[key] = value
    s = json.dumps(d, indent=2,ensure_ascii=False,sort_keys=True)
    return (keyname,s)
  except Exception as e:
    print "Error obteniendo los valores del diccionario '%s'. %s" % (table, str(e))
    return None
  finally:
    DisposeUtils.dispose(store)
    
def getDDL(modelName=MODEL_NAME, include_datadicts=True):
  server = None
  repo = None
  try:
    dataManager =  DALLocator.getDataManager()
    repo = dataManager.getStoresRepository().getSubrepository(modelName)
    serverparams = repo.getServerParameters()
    server = dataManager.openServerExplorer(serverparams.getProviderName(), serverparams)

    dics = dict()
    for table in repo.keySet():
      ft = repo.getFeatureType(table).getEditable()
      for attr in ft:
        if attr.isForeingKey() and attr.getForeingKey().isClosedList() and not dics.has_key(attr.getForeingKey().getTableName()):
          fk = attr.getForeingKey()
          value = __getValuesOfDic(repo, fk.getTableName(), fk)
          if value:
            dics[fk.getTableName()] = value

    builder = StringBuilder()    
    for table in repo.keySet():
      ft = repo.getFeatureType(table).getEditable()
      # Nos aseguramos que se vayan a declarar las foreign keys
      for attr in ft:
        if attr.isForeingKey():
          attr.getForeingKey().setEnsureReferentialIntegrity(True)
      sqls = server.getCreateTableSQLs(
        repo.getID(), 
        "public", 
         table, 
         ft
      )
      if table in dics.keys():
        builder.append("-- Tabla: %s tipo DICCIONARIO\n" % table)
      else:
        builder.append("-- Tabla: %s tipo ENTIDAD\n" % table)
      # Formateamos ligeramente las SQL generadas
      for sql in sqls:
        sql = sql + ";"
        if sql.startswith('CREATE TABLE'):
          sql = sql.replace(', "',',\n    "').replace('" ("','" (\n    "').replace(");","\n);").replace(', FOREIGN KEY',',\n    FOREIGN KEY')
        builder.append(sql)
        builder.append("\n")
      if include_datadicts and table in dics.keys():
        pkname, json = dics[table]
        builder.append("-- Diccionario: %s\n-- La clave de este diccionario es el valor de la columna '%s'\n-- IMPORTANTE: Las claves del diccionario son los unicos valores permitidos para referenciar al campo '%s'\n-- Valores: %s\n" % (table, pkname, pkname,json.replace("\n","\n-- "))+"\n")
      builder.append("\n")
      
    # Por ultimo devolvemos todas las SQL generadas 
    return builder.toString()
  finally:
    DisposeUtils.dispose(repo)
    DisposeUtils.dispose(server)


def getProperty(name):
    home_dir = os.path.expanduser("~")
    properties_file_path = os.path.join(home_dir, ".gvsig-devel.properties")
    props = Properties()
    try:
        fis = FileInputStream(properties_file_path)
        props.load(fis)
        fis.close()
        return props.getProperty(name)
    except java.io.IOException, e: # Sintaxis de except para Python 2.7
        print "Error al leer el archivo de propiedades '%s': %s" % (properties_file_path, e)
        return None
    except Exception, e: # Sintaxis de except para Python 2.7
        print "Ocurrió un error inesperado: %s" % e
        return None

def showConnectToDatabaseWorkspaceDialog(callback):
    from org.gvsig.geodb.databaseworkspace import ConnectToDatabaseWorkspacePanel

    winManager = ToolsSwingLocator.getWindowManager()
    panel = ConnectToDatabaseWorkspacePanel() 
    i18n = ToolsLocator.getI18nManager()

    dialog = winManager.createDialog(
        panel.asJComponent(),
        i18n.getTranslation("_Connect"),
        i18n.getTranslation("_Connect_to_database_repository"),
        WindowManager_v2.BUTTONS_APPLY_OK_CANCEL
    )
    panel.setDialog(dialog)
    dialog.setButtonLabel(WindowManager_v2.BUTTON_OK, i18n.getTranslation("_Connect"))
    dialog.setButtonLabel(WindowManager_v2.BUTTON_APPLY, i18n.getTranslation("_Disconnect"))

    class DialogActionListener(java.awt.event.ActionListener):
        def actionPerformed(self, event):
            action = dialog.getAction()
            if action == WindowManager_v2.BUTTON_OK:
                panel.connect()
                callback()
            elif action == WindowManager_v2.BUTTON_APPLY:
                panel.disconnect()
                callback()
    dialog.addActionListener(DialogActionListener())
    dialog.show(
        WindowManager.MODE.WINDOW,
        Collections.singletonMap("align", GridBagConstraints.CENTER)
    )


class ChatAgentToolExtension(Extension):
  def __init__(self, executeListener):
    self.executeListener = executeListener
  def canQueryByAction(self):
    return True
  def isEnabled(self,action):
    return True
  def isVisible(self,action):
    return True  
  def execute(self,actionCommand, *args):
    self.executeListener.actionPerformed()

def addToToolBar(executeListener, iconpath, tooltip):
  application = ApplicationLocator.getManager()
  actionManager = PluginsLocator.getActionInfoManager()
  iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()

  name = "chatagent-%s" % (UUID.randomUUID().toString().replace("-",""))
  iconTheme.registerDefault("scripting.ChatAgentToolExtension", "action", name, None, File(iconpath).toURI().toURL())
  action = actionManager.createAction(
    ChatAgentToolExtension(executeListener), 
    name, # Action name
    tooltip, # Text
    name, # Action command
    name, # Icon name
    None, # Accelerator
    1, # Position 
    tooltip # Tooltip
  )
  action = actionManager.registerAction(action)
  application.getMainFrame().addTool(action, "Asistente IA", "chatagent")
  application.getMainFrame().refreshControls()

def getCurrentViewBboxAsWKT():
    try:
        viewbbox = gvsig.currentView().getMapContext().getViewPort().getEnvelope().getBox2D().convertToWKT()
    except:
        viewbbox = "(actualmente es desconocido)"
    return viewbbox

def getAvailableDataModels():
    dataManager =  DALLocator.getDataManager()
    repo = dataManager.getStoresRepository()
    models = list()
    for sr in repo.getSubrepositories():
        #if isinstance(sr,DatabaseWorkspaceStoresRepository):
        models.append(LabeledValueImpl(sr.getLabel(),sr.getID()))
    return models

def showImage(title, image_path, size=Dimension(400,400)):
    manager = ToolsUtilLocator.getImageViewerManager()
    viewer = manager.createImageViewer()
    viewer.setImage(image_path)
    viewer.setPreferredSize(size)
    showPanel(viewer,title)    

def main(**args): 
  print getDDL(MODEL_NAME)
  print "ok"
 

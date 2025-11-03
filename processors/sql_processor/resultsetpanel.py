 
# -*- coding: utf-8 -*-


import gvsig


import java

from java.lang import String, Class, Object
from java.awt import BorderLayout, Dimension, Font
from javax.swing import JPanel, JTable, JScrollPane, BorderFactory
from javax.swing.table import AbstractTableModel
from java.sql import ResultSet


class ResultSetTableModel(AbstractTableModel):
    """
    Modelo de tabla para mostrar un java.sql.ResultSet en un JTable.
    """
    def __init__(self, resultSet):
        self.resultSet = resultSet
        self.columnNames = []
        self.columnTypes = []
        self.data = []
        self._load_data()

    def _load_data(self):
        """
        Carga los metadatos del ResultSet y todos los datos en memoria.
        """
        try:
            metaData = self.resultSet.getMetaData()
            numColumns = metaData.getColumnCount()

            # Obtener nombres y tipos de columna
            for i in range(1, numColumns + 1):
                self.columnNames.append(metaData.getColumnLabel(i))
                self.columnTypes.append(metaData.getColumnClassName(i))

            # Cargar todos los datos
            while self.resultSet.next():
                row = []
                for i in range(1, numColumns + 1):
                    row.append(self.resultSet.getObject(i))
                self.data.append(row)
        except Exception as e:
            print "Error al cargar datos del ResultSet: %s" % e
        finally:
            if self.resultSet:
                try:
                    self.resultSet.close()
                except Exception as e:
                    print "Error al cerrar ResultSet: %s" % e

    def getColumnCount(self):
        """
        Devuelve el número de columnas.
        """
        return len(self.columnNames)

    def getRowCount(self):
        """
        Devuelve el número de filas.
        """
        return len(self.data)

    def getColumnName(self, col):
        """
        Devuelve el nombre de la columna.
        """
        return self.columnNames[col]

    def getValueAt(self, row, col):
        """
        Devuelve el valor en la celda especificada.
        """
        return self.data[row][col]

    def getColumnClass(self, col):
        """
        Devuelve la clase de la columna para un renderizado adecuado.
        """
        try:
            # Intenta devolver la clase Java real
            return Class.forName(self.columnTypes[col])
        except Exception:
            # Si falla, devuelve Object.class como fallback
            return Object.class


class ResultSetTablePanel(JPanel):
    def __init__(self, resultSet):
        super(ResultSetTablePanel, self).__init__(BorderLayout())
        self.setPreferredSize(Dimension(800, 300)) # Tamaño preferido para la ventana
        self.tableModel = ResultSetTableModel(resultSet)
        self.table = JTable(self.tableModel)
        self.table.setAutoResizeMode(JTable.AUTO_RESIZE_OFF) # Permite scroll horizontal
        self.table.getTableHeader().setReorderingAllowed(False) # Evita reordenar columnas

        scrollPane = JScrollPane(self.table)
        self.add(scrollPane, BorderLayout.CENTER)
        

def main(**args):
  print "ok"
  
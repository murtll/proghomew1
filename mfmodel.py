from PyQt5.QtSql import *
from PyQt5.QtCore import *

class MainfestModel(QSqlTableModel):
    def __init__(self, parent = None, db = QSqlDatabase()):
        super(MainfestModel, self).__init__(parent, db)
    
    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
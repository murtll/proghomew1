from datetime import date
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtSql import *

from mfmodel import MainfestModel

filter_date = date.today()
filter_category = None
base_query='''select purchases.id as id, purchases.name as name, cost, date, categories.name as category from purchases 
                inner join categories on purchases.category_id = categories.id'''
current_query=base_query

def sortSelected():
    global current_query
    if sort_selector.currentIndex() == 0:
        model.setQuery(QSqlQuery(current_query))
    elif sort_selector.currentIndex() == 1:
        model.setQuery(QSqlQuery(current_query + ' order by cost asc'))
    else:
        model.setQuery(QSqlQuery(current_query + ' order by cost desc'))

    model.select()

def getCategories():
    categories = []

    query = QSqlQuery()
    query.exec_('select * from categories')

    while(query.next()):
        categories.append({
            'id': query.value(0),
            'name': query.value(1)
        })
    
    return categories

def filterClicked():
    global base_query
    global current_query
    global model
    global filter_category
    global filter_date

    def setFilterDate(date):
        global filter_date
        filter_date = date

    def setFilterCategory(category):
        global filter_category
        filter_category = category

    def clearFilter():
        setFilterDate(QDate(2000, 1, 1))
        setFilterCategory(None)
        date_input.setDate(QDate(2000, 1, 1))
        category_input.setCurrentIndex(0)

    
    input_dialog = QDialog()
    input_layout = QFormLayout(input_dialog)

    clear_button = QPushButton('Clear')
    clear_button.clicked.connect(clearFilter)

    date_input = QDateEdit()

    date_input.setCalendarPopup(True)
    date_input.setDisplayFormat('dd-MM-yyyy')
    date_input.dateChanged.connect(lambda: setFilterDate(date_input.date()))
    date_input.setMinimumDate(QDate(2000, 1, 1))
    date_input.setSpecialValueText('Select date')

    date_input.setDate(filter_date)

    category_input = QComboBox()

    categories = getCategories()

    category_input.addItem('Select category')

    for i in range(len(categories)):
        category_input.addItem(categories[i]['name'])
        category_input.setItemData(i + 1, categories[i]['id'])

    if filter_category != None:
        category_input.setCurrentIndex(filter_category)

    category_input.currentIndexChanged.connect(lambda: setFilterCategory(category_input.currentIndex()))

    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, input_dialog)

    input_layout.addRow('Date: ', date_input)
    input_layout.addRow('Category: ', category_input)
    input_layout.addRow(clear_button)
    input_layout.addWidget(button_box)

    button_box.accepted.connect(input_dialog.accept)
    button_box.rejected.connect(input_dialog.reject)

    input_dialog.setWindowTitle('Set filter')

    result = input_dialog.exec_()

    if result == 1:
        newQuery = base_query

        if date_input.date() != date_input.minimumDate() and category_input.currentData() != None:
            newQuery = (base_query + " where category_id=%i and date between datetime('%s') and datetime('%s')" 
            % (category_input.currentData(), 
            date_input.date().toPyDate().strftime("%Y-%m-%d 00:00:00"), 
            date_input.date().addDays(1).toPyDate().strftime("%Y-%m-%d 00:00:00")))
        elif date_input.date() != date_input.minimumDate():
            newQuery = (base_query + " where date between datetime('%s') and datetime('%s')" % 
            (date_input.date().toPyDate().strftime("%Y-%m-%d 00:00:00"), 
            date_input.date().addDays(1).toPyDate().strftime("%Y-%m-%d 00:00:00")))
        elif category_input.currentData() != None:
            newQuery = base_query + " where category_id=%i" % (category_input.currentData())

        model.setQuery(QSqlQuery(newQuery))
        current_query = newQuery
        # model.select()
        sortSelected()

def addItem():
    global base_query
    global model
    input_dialog = QDialog()
    input_layout = QFormLayout(input_dialog)

    name_input = QLineEdit()

    category_input = QComboBox()

    categories = getCategories()

    for i in range(len(categories)):
        category_input.addItem(categories[i]['name'])
        category_input.setItemData(i, categories[i]['id'])

    cost_input = QLineEdit()
    cost_input.setValidator(QDoubleValidator(0.99, 9999.99, 2))

    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, input_dialog)

    input_layout.addRow('Name: ', name_input)
    input_layout.addRow('Category: ', category_input)
    input_layout.addRow('Cost: ', cost_input)
    input_layout.addWidget(button_box)

    button_box.accepted.connect(input_dialog.accept)
    button_box.rejected.connect(input_dialog.reject)

    input_dialog.setWindowTitle('Add product')

    result = input_dialog.exec_()

    if result == 1 and name_input.text() != '' and cost_input.text() != '':
        query = QSqlQuery()
        query.exec_('''insert into purchases (name, cost, category_id) values ('%s', %f, '%i')''' 
        % (name_input.text(), float(cost_input.text()), category_input.currentData()))
        model.setQuery(QSqlQuery(base_query))
        model.select()

def checkSelectedRows():
    if len(selection_model.selectedRows()) > 0:
        delete_button.setEnabled(True)
    else:
        delete_button.setEnabled(False)

def deleteRows():
    queryText = ' or '.join(['id=%i' % i.data() for i in selection_model.selectedRows()])
    query = QSqlQuery()
    query.exec_('''delete from purchases where %s''' % queryText)
    model.setQuery(QSqlQuery(current_query))
    print(model.select())

def configureDb():
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName('test.db')

    if not db.open():
       msg = QMessageBox()
       msg.setIcon(QMessageBox.Critical)
       msg.setText("Cannot access storage")
       msg.exec_()
    else:
        print('Storage accessed successfully.')

    query = QSqlQuery()
    query.exec_('''PRAGMA foreign_keys = ON''')
    query.exec_('''create table if not exists categories(id integer primary key autoincrement, name text unique)''')
    query.exec_('''create table if not exists purchases(id integer primary key autoincrement, 
                name text, cost real, date datetime default current_timestamp, category_id integer references categories(id))''')
    query.exec_('''insert into categories (name) values ('Food'), ('Fun'), ('Clothes')''')


app = QApplication(sys.argv)

configureDb()

model = MainfestModel()
model.setQuery(QSqlQuery(base_query))
model.select()
model.setHeaderData(0, Qt.Horizontal, "Id")
model.setHeaderData(1, Qt.Horizontal, "Name")
model.setHeaderData(2, Qt.Horizontal, "Cost")
model.setHeaderData(3, Qt.Horizontal, "Date & Time")
model.setHeaderData(4, Qt.Horizontal, "Category")

selection_model = QItemSelectionModel()
selection_model.setModel(model)

view = QTableView()
view.setModel(model)
view.setSelectionModel(selection_model)
view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
view.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
view.clicked.connect(checkSelectedRows)

view.hideColumn(0)
view.setColumnWidth(3, 130)

sort_selector = QComboBox()

sort_selector.addItem('Sort by cost')
sort_selector.addItem('Asc')
sort_selector.addItem('Desc')

sort_selector.currentIndexChanged.connect(sortSelected)

layout = QVBoxLayout()
layout.addWidget(sort_selector)
layout.addWidget(view)

delete_button = QPushButton('Delete')
delete_button.setEnabled(False)
delete_button.clicked.connect(deleteRows)

layout.addWidget(delete_button)

add_button = QPushButton("Add product")
add_button.clicked.connect(addItem)
layout.addWidget(add_button)

filter_button = QPushButton("Filter")
filter_button.clicked.connect(filterClicked)
layout.addWidget(filter_button)

dialog = QDialog()
dialog.setGeometry(700, 400, 470, 500)
dialog.setLayout(layout)
dialog.setWindowTitle('Money Counter')
dialog.show()

sys.exit(app.exec_())
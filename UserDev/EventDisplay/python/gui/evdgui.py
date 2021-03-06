from gui import gui
from pyqtgraph.Qt import QtGui, QtCore


class ComboBoxWithKeyConnect(QtGui.QComboBox):

    def __init__(self):
        super(ComboBoxWithKeyConnect, self).__init__()

    def connectOwnerKPE(self, kpe):
        self._owner_KPE = kpe

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Up:
            super(ComboBoxWithKeyConnect, self).keyPressEvent(e)
            return
        if e.key() == QtCore.Qt.Key_Down:
            super(ComboBoxWithKeyConnect, self).keyPressEvent(e)
            return
        else:
            self._owner_KPE(e)
        # if e.key() == QtCore.Qt.Key_N:
        #     self._owner_KPE(e)
        #     pass
        # if e.key() == QtCore.Qt.Key_P:
        #     self._owner_KPE(e)
        #     pass
        # else:
        #     super(ComboBoxWithKeyConnect, self).keyPressEvent(e)
        #     self._owner_KPE(e)

# This is a widget class that contains the label and combo box
# It also knows what to do when updating


class recoBox(QtGui.QWidget):
    activated = QtCore.pyqtSignal(str)

    """docstring for recoBox"""

    def __init__(self, owner, name, product, producers):
        super(recoBox, self).__init__()
        self._label = QtGui.QLabel()
        self._name = name
        self._label.setText(self._name.capitalize() + ": ")
        self._box = ComboBoxWithKeyConnect()
        self._box.setDuplicatesEnabled(False)
        self._box.activated[str].connect(self.emitSignal)
        self._product = product
        self._producers = producers
        self._stage = "all"
        if producers == None:
            self._box.addItem("--None--")
        else:
            self._box.addItem("--Select--")
            for producer in producers:
                self._box.addItem(producer.producer())

        self._box.connectOwnerKPE(owner.keyPressEvent)

        # This is the widget itself, so set it up
        self._layout = QtGui.QVBoxLayout()
        self._layout.addWidget(self._label)
        self._layout.addWidget(self._box)
        self.setLayout(self._layout)

    def selectStage(self, stage):

        # If no stage can draw this product, just return
        if self._producers is None:
            return
        else:
            self._box.clear()

            prod_list = []
            for prod in self._producers:
                if prod.stage() == stage or stage == 'all':
                    prod_list.append(prod.producer())

            if len(prod_list) > 0:
                self._box.addItem("--Select--")
                for _producer in prod_list:
                    self._box.addItem(_producer)
            else:
                self._box.addItem("--None--")

        self._box.setDuplicatesEnabled(False)


    def keyPressEvent(self, e):
        self._box.keyPressEvent(e)
        super(recoBox, self).keyPressEvent(e)

    def emitSignal(self, text):
        self.activated.emit(text)

    def productType(self):
        return self._product

    def productObj(self, producer, stage):
        if stage is None:
            stage = "all"
        for prod in self._producers:
            if prod.producer() == producer:
                if stage == "all" or prod.stage() == stage:
                    return prod

    def name(self):
        return self._name

# Inherit the basic gui to extend it
# override the gui to give the lariat display special features:


class evdgui(gui):

    """special evd gui"""

    def __init__(self, geometry, manager=None):
        super(evdgui, self).__init__(geometry)
        if manager is None:
            manager = evd_manager(geometry)
        super(evdgui, self).initManager(manager)
        self.initUI()
        self._stage = None
        self._event_manager.fileChanged.connect(self.drawableProductsChanged)
        self._event_manager.eventChanged.connect(self.update)
        # self._event_manager.truthLabelChanged.connect(self.updateMessageBar)

    # override the initUI function to change things:
    def initUI(self):
        super(evdgui, self).initUI()
        # Change the name of the labels for lariat:
        self.update()

    # This function sets up the eastern widget
    def getEastLayout(self):
        # This function just makes a dummy eastern layout to use.
        label1 = QtGui.QLabel("EVD")
        geoName = self._geometry.DetectorName()
        label2 = QtGui.QLabel(geoName.capitalize())
        font = label1.font()
        font.setBold(True)
        label1.setFont(font)
        label2.setFont(font)



        self._eastWidget = QtGui.QWidget()
        # This is the total layout
        self._eastLayout = QtGui.QVBoxLayout()
        # add the information sections:
        self._eastLayout.addWidget(label1)
        self._eastLayout.addWidget(label2)
        self._eastLayout.addStretch(1)

        self._stageLabel = QtGui.QLabel("Stage:")
        self._stageSelection = QtGui.QComboBox()
        self._stageSelection.activated[str].connect(self.stageSelectHandler)
        # Make sure "all" is default and on top:
        self._stageSelection.addItem("all")
        for stage in self._event_manager.getStages():
            if stage != "all":
                self._stageSelection.addItem(stage)

        self._eastLayout.addWidget(self._stageLabel)
        self._eastLayout.addWidget(self._stageSelection)
        self._eastLayout.addStretch(1)

        # The wires are a special case.
        # Use a check box to control wire drawing
        self._wireButtonGroup = QtGui.QButtonGroup()
        # Draw no wires:
        self._noneWireButton = QtGui.QRadioButton("None")
        self._noneWireButton.clicked.connect(self.wireChoiceWorker)
        self._wireButtonGroup.addButton(self._noneWireButton)

        # Draw Wires:
        self._wireButton = QtGui.QRadioButton("Wire")
        self._wireButton.clicked.connect(self.wireChoiceWorker)
        self._wireButtonGroup.addButton(self._wireButton)

        # Draw Raw Digit
        self._rawDigitButton = QtGui.QRadioButton("Raw Digit")
        self._rawDigitButton.clicked.connect(self.wireChoiceWorker)
        self._wireButtonGroup.addButton(self._rawDigitButton)

        # Make a layout for this stuff:
        self._wireChoiceLayout = QtGui.QVBoxLayout()
        self._wireChoiceLabel = QtGui.QLabel("Wire Draw Options")
        self._wireChoiceLayout.addWidget(self._wireChoiceLabel)
        self._wireChoiceLayout.addWidget(self._noneWireButton)
        self._wireChoiceLayout.addWidget(self._wireButton)
        self._wireChoiceLayout.addWidget(self._rawDigitButton)

        self._eastLayout.addLayout(self._wireChoiceLayout)

        # Set the default to be no wires
        self._noneWireButton.toggle()

        # Microboone only:
        if self._geometry.DetectorName() == "uboone":
            self._noiseFilterBox = QtGui.QCheckBox("Noise Filter")
            self._noiseFilterBox.stateChanged.connect(self.noiseFilterWorker)
            self._eastLayout.addWidget(self._noiseFilterBox)

        # # Set a box for mcTruth Info
        # self._truthDrawBox = QtGui.QCheckBox("MC Truth")
        # self._truthDrawBox.stateChanged.connect(self.truthDrawBoxWorker)
        # self._eastLayout.addWidget(self._truthDrawBox)


        # Now we get the list of items that are drawable:
        drawableProducts = self._event_manager.getDrawableProducts()
        # print drawableProducts
        self._listOfRecoBoxes = []
        for product in drawableProducts:
            thisBox = recoBox(self,
                              product,
                              drawableProducts[product][1],
                              self._event_manager.getProducers(
                                  drawableProducts[product][1]))
            self._listOfRecoBoxes.append(thisBox)
            thisBox.activated[str].connect(self.recoBoxHandler)
            self._eastLayout.addWidget(thisBox)
        self._eastLayout.addStretch(2)

        self._eastWidget.setLayout(self._eastLayout)
        self._eastWidget.setMaximumWidth(150)
        self._eastWidget.setMinimumWidth(100)
        return self._eastWidget

    def drawableProductsChanged(self):
        # self.removeItem(self._eastLayout)
        self._eastWidget.close()
        east = self.getEastLayout()
        self.slave.addWidget(east)
        self.update()

        # self._eastLayout.setVisible(False)
        # self._eastLayout.setVisible(True)

    def wireChoiceWorker(self):
        sender = self.sender()
        if sender == self._noneWireButton:
            self._event_manager.toggleWires(None)
            # print "None is selected"
        if sender == self._wireButton:
            self._event_manager.toggleWires('wire',stage = self._stage)
            # print "Wire is selected"
        if sender == self._rawDigitButton:
            self._event_manager.toggleWires('rawdigit',stage = self._stage)
            # print "Raw digit is selected"

        self._view_manager.drawPlanes(self._event_manager)
        # if self._wireDrawBox.isChecked():
        #   self._event_manager.toggleWires(True)
        # else:
        #   self._event_manager.toggleWires(False)

        # self._view_manager.drawPlanes(self._event_manager)

    def stageSelectHandler(self, _str):
        self._stage = _str
        if _str == "all":
            self._stage = None
        for box in self._listOfRecoBoxes:
            box.selectStage(_str)
        # print str

    def noiseFilterWorker(self):
        if self._noiseFilterBox.isChecked():
            self._event_manager.toggleNoiseFilter(True)
        else:
            self._event_manager.toggleNoiseFilter(False)

        self._view_manager.drawPlanes(self._event_manager)

    # def truthDrawBoxWorker(self):
    #     if self._truthDrawBox.isChecked():
    #         self._event_manager.toggleTruth(True)
    #     else:
    #         self._event_manager.toggleTruth(False)

    #     self._event_manager.drawFresh()
    #     # gui.py defines the message bar and handler, connect it to this:

    def recoBoxHandler(self, text):
        sender = self.sender()
        # print sender.product(), "was changed to" , text
        if text == "--Select--" or text == "--None--":
            self._event_manager.redrawProduct(sender.name(), None, self._view_manager)
            return
        else:
            # Get the full product obj for this:
            prod = sender.productObj(text, self._stage)
            self._event_manager.redrawProduct(sender.name(), prod, self._view_manager)

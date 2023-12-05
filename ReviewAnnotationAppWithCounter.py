import os
import shutil
import sys
import numpy
import cv2
import pandas
import math
import time
import csv

from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QSpacerItem, QFileDialog, QTabWidget, QComboBox, QCheckBox, QSlider, QMainWindow, QLineEdit
from PyQt6.QtGui import QImage, QPixmap, QShortcut, QKeySequence
from superqt import QRangeSlider

if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_counter.csv")):
    FIX_COUNTER = pandas.read_csv(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "fix_counter.csv"))
    FIX_COUNTER = pandas.concat([FIX_COUNTER, pandas.DataFrame({"Video": [None], "Overall Task":[
                                0], "Missing box":[0], "Edit box":[0], "Time":[time.time()], "Total":[0], "Pass":[False]})])
    FIX_COUNTER.index = [i for i in range(len(FIX_COUNTER.index))]
else:
    FIX_COUNTER = pandas.DataFrame({"Video": [None], "Overall Task": [0], "Missing box": [
                                   0], "Edit box": [0], "Time": [time.time()], "Total": [0], "Pass": [False]})


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super(QLabel, self).__init__(parent)
        self.setMouseTracking(False)


class AnnotationReviewer(QWidget):
    def __init__(self):
        super().__init__()
        self.modifyBBoxStarted = False
        self.imgShape = (480, 640, 3)
        self.cursorCoordinates = (0, 0)
        self.labelType = None
        self.setMouseTracking(False)
        self.setWindowTitle("Annotation Reviewer")
        self.setGeometry(500, 200, 1250, 500)
        self.addWidgetsToWindow()
        self.setupButtonConnections()
        self.show()

    def addWidgetsToWindow(self):
        # self.mainWindow = window
        titleMsg = QLabel("<h1>Annotation Reviewer<h1>")
        titleMsg.move(20, 20)
        mainLayout = QHBoxLayout()

        #############################
        # Create Image manipulations layout
        #############################
        layout = QVBoxLayout()
        layout.addWidget(titleMsg)
        self.selectImageDirButton = QPushButton("Select Image Directory")
        layout.addWidget(self.selectImageDirButton)
        self.imageDirectoryLabel = QLabel("Image Directory: ")
        layout.addWidget(self.imageDirectoryLabel)
        layout.addItem(QSpacerItem(100, 20))

        self.addNewLabelWidgetLayout = QGridLayout()
        self.addNewLabelButton = QPushButton("Add new label")
        self.newLabelLineEdit = QLineEdit("Label name")
        self.newLabelLineEdit.visible = False
        self.addNewLabelButton.visible = False
        self.addNewLabelWidgetLayout.addWidget(self.addNewLabelButton, 6, 0)
        self.addNewLabelWidgetLayout.addWidget(self.newLabelLineEdit, 6, 1)
        layout.addLayout(self.addNewLabelWidgetLayout)
        layout.addItem(QSpacerItem(100, 20))

        self.removeAndRepairButton = QPushButton("Remove and Repair Glitches")
        layout.addWidget(self.removeAndRepairButton)
        layout.addItem(QSpacerItem(100, 20))
        self.removeImageButton = QPushButton("Remove Image")
        layout.addWidget(self.removeImageButton)
        layout.addItem(QSpacerItem(100, 20))
        self.flipImageHButton = QPushButton("Flip image horizontally")
        self.flipAllHButton = QPushButton("Flip all images horizontally")
        self.flipImageVButton = QPushButton("Flip image vertically")
        self.flipAllVButton = QPushButton("Flip all images vertically")
        layout.addWidget(self.flipImageHButton)
        layout.addWidget(self.flipAllHButton)
        layout.addWidget(self.flipImageVButton)
        layout.addWidget(self.flipAllVButton)
        self.saveButton = QPushButton("Save Changes")
        self.messageLabel = QLabel("")
        layout.addItem(QSpacerItem(100, 20))
        layout.addWidget(self.saveButton)
        layout.addWidget(self.messageLabel)
        mainLayout.addLayout(layout)

        mainLayout.addItem(QSpacerItem(20, 100))
        #############################
        # Create Image layout
        #############################
        imageLayout = QVBoxLayout()
        self.imageLabel = ImageLabel()
        image = numpy.zeros((480, 640, 3))
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        qImage = QImage(image.data, width, height,
                        bytesPerLine, QImage.Format.Format_RGB888)
        pixelmap = QPixmap.fromImage(qImage)
        self.imageLabel.setPixmap(pixelmap)
        imageLayout.addWidget(self.imageLabel)
        self.imageSlider = QSlider(Qt.Orientation.Horizontal)
        self.imageSlider.setEnabled(False)
        imageLayout.addWidget(self.imageSlider)
        imageScrollButtonLayout = QHBoxLayout()
        self.previousButton = QPushButton("Previous Image (p)")
        self.previousButton.setEnabled(False)
        self.nextButton = QPushButton("Next Image (n)")
        self.nextButton.setEnabled(False)
        imageScrollButtonLayout.addWidget(self.previousButton)
        imageScrollButtonLayout.addWidget(self.nextButton)
        imageLayout.addLayout(imageScrollButtonLayout)
        mainLayout.addLayout(imageLayout)

        mainLayout.addItem(QSpacerItem(20, 100))
        #############################
        # Create Label manipulations layout
        #############################
        labellayout = QVBoxLayout()
        self.labelTypeSelectorComboBox = QComboBox()
        self.labelTypeSelectorComboBox.addItems(["Select label type"])
        labellayout.addWidget(self.labelTypeSelectorComboBox)
        self.setupLabelTypeToolLayout()

        self.labelToolTabWidget = QTabWidget()
        self.classificationToolWidget = QWidget()
        classificationLayout = QVBoxLayout()
        self.setupClassificationToolLayout(classificationLayout)
        self.classificationToolWidget.setLayout(classificationLayout)
        self.labelToolTabWidget.addTab(
            self.classificationToolWidget, "Classification")
        self.detectionToolWidget = QWidget()
        detectionLayout = QVBoxLayout()
        self.setupDetectionToolLayout(detectionLayout)
        self.detectionToolWidget.setLayout(detectionLayout)
        self.labelToolTabWidget.addTab(self.detectionToolWidget, "Detection")
        self.segmentationToolWidget = QWidget()
        segmentationLayout = QVBoxLayout()
        self.setupSegmentationToolLayout(segmentationLayout)
        self.segmentationToolWidget.setLayout(segmentationLayout)
        self.labelToolTabWidget.addTab(
            self.segmentationToolWidget, "Segmentation")
        labellayout.addWidget(self.labelToolTabWidget)
        self.approvalCheckBox = QCheckBox("Approved")
        self.approvalRemainingLabel = QLabel("")
        self.selectCleanDirButton = QPushButton("Select Image Directory")
        self.cleanDirectoryLabel = QLabel("Clean Image Directory: ")
        self.transferImagesButton = QPushButton("Transfer Images & Labels")
        self.transferImagesButton.setEnabled(False)
        labellayout.addWidget(self.approvalCheckBox)
        labellayout.addWidget(self.approvalRemainingLabel)
        labellayout.addWidget(self.selectCleanDirButton)
        labellayout.addWidget(self.cleanDirectoryLabel)
        labellayout.addWidget(self.transferImagesButton)
        mainLayout.addLayout(labellayout)

        self.setLayout(mainLayout)
        self.setupHotkeys()

    def setupHotkeys(self):
        saveShortcut = QShortcut(self)
        saveShortcut.setKey("Ctrl+s")
        saveShortcut.activated.connect(self.onSaveButtonClicked)

        approveShortcut = QShortcut(self)
        approveShortcut.setKey("y")
        approveShortcut.activated.connect(self.onApprovalKeyPressed)

        verticalFlipShortcut = QShortcut(self)
        verticalFlipShortcut.setKey("v")
        verticalFlipShortcut.activated.connect(self.flipImageVButton.click)

        allVerticalFlipShortcut = QShortcut(self)
        allVerticalFlipShortcut.setKey("Ctrl+v")
        allVerticalFlipShortcut.activated.connect(self.flipAllVButton.click)

        horizontalFlipShortcut = QShortcut(self)
        horizontalFlipShortcut.setKey("h")
        horizontalFlipShortcut.activated.connect(self.flipImageHButton.click)

        allhorizontalFlipShortcut = QShortcut(self)
        allhorizontalFlipShortcut.setKey("Ctrl+h")
        allhorizontalFlipShortcut.activated.connect(self.flipAllHButton.click)

        nextShortcut = QShortcut(self)
        nextShortcut.setKey("n")
        nextShortcut.activated.connect(self.nextButton.click)

        previousShortcut = QShortcut(self)
        previousShortcut.setKey("p")
        previousShortcut.activated.connect(self.previousButton.click)

    def setupLabelTypeToolLayout(self):
        self.labelTypeSelectorComboBox.currentIndexChanged.connect(
            self.newLabelSelected)
        self.addNewLabelButton.clicked.connect(
            self.addNewLabelToFile)

    def addNewLabelToFile(self): 
        if not self.newLabelLineEdit.text() == "Label name":
            self.labelFile[self.newLabelLineEdit.text()]=["[]" for i in self.labelFile.index]
            
            self.labelTypeSelectorComboBox.addItems(
                [str(self.newLabelLineEdit.text())])
            self.labelTypeSelectorComboBox.setCurrentText(self.newLabelLineEdit.text())       

    
    def newLabelSelected(self):
        if self.labelTypeSelectorComboBox.currentText() == "Select label type":
            self.newLabelLineEdit.visible = True
            self.addNewLabelButton.visible = True
        else:
            self.newLabelLineEdit.visible = False
            self.addNewLabelButton.visible = False

    def setupClassificationToolLayout(self, layout):

        self.labelSelectorComboBox = QComboBox()
        self.labelSelectorComboBox.addItem("Select label")
        self.labelSelectorComboBox.addItem("Add new label")
        self.applyPreviousLabelButton = QPushButton("Apply previous label")
        self.blockApplyPreviousLabelButton = QPushButton(
            "Bulk apply previous label")
        self.addNewClassificationButton = QPushButton("Add new class")
        self.addNewClassificationLineEdit = QLineEdit("Class name")

        # self.labelSelectorComboBox.currentIndexChanged.connect(self.addNewClassToClassification)

        layout.addWidget(self.labelSelectorComboBox)
        layout.addWidget(self.applyPreviousLabelButton)
        layout.addWidget(self.blockApplyPreviousLabelButton)
        layout.addWidget(self.addNewClassificationButton)
        layout.addWidget(self.addNewClassificationLineEdit)

    # def addNewClassToClassification(self):

    def setupDetectionToolLayout(self, layout):
        self.step1Widget = QWidget()
        self.createStep1Widget()
        layout.addWidget(self.step1Widget)

    def setupSegmentationToolLayout(self, layout):
        self.segmentationLabel = QLabel()
        image = numpy.zeros((240, 320, 3))
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        qImage = QImage(image.data, width, height,
                        bytesPerLine, QImage.Format.Format_RGB888)
        pixelmap = QPixmap.fromImage(qImage)
        self.segmentationLabel.setPixmap(pixelmap)
        layout.addWidget(self.segmentationLabel)
        self.blankSegmentationButton = QPushButton("Make blank")
        layout.addWidget(self.blankSegmentationButton)
        self.blankSegmentationButton.clicked.connect(
            self.onMakeSegmentationBlank)
        self.blankSegmentationButton.setEnabled(False)

    def onMakeSegmentationBlank(self):
        segmentationFileName = self.labelFile[self.labelType][self.currentIndex]
        if "segmentation" in segmentationFileName:
            segImage = cv2.imread(os.path.join(
                self.imageDirectory, segmentationFileName))
            segImage = segImage[:, :, 0]
            newSegImage = numpy.zeros(segImage.shape)
            cv2.imwrite(os.path.join(self.imageDirectory,
                        segmentationFileName), newSegImage)
            self.setSegmentationImage(segmentationFileName)
        else:
            self.setSegmentationImage(None)

    def setSegmentationImage(self, fileName=None):
        if fileName == None:
            image = numpy.zeros((240, 320, 3))
        else:
            image = cv2.imread(os.path.join(self.imageDirectory, fileName))
            height, width, channel = image.shape
            image = cv2.resize(
                image, (round(height/2), round(width/2)), interpolation=cv2.INTER_CUBIC)
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        qImage = QImage(image.data, width, height,
                        bytesPerLine, QImage.Format.Format_RGB888)
        pixelmap = QPixmap.fromImage(qImage)
        self.segmentationLabel.setPixmap(pixelmap)

    def createStep1Widget(self):
        step1Layout = QVBoxLayout()
        self.fliplabelsVButton = QPushButton("Flip boxes vertically")
        self.fliplabelsHButton = QPushButton("Flip boxes horizontally")
        self.flipAllLabelsVButton = QPushButton("Flip all boxes vertically")
        self.flipAllLabelsHButton = QPushButton("Flip all boxes horizontally")
        self.swapXandYButton = QPushButton("Swap X and Y coordinates")
        self.applyPreviousBoxesButton = QPushButton("Apply previous boxes")
        self.acceptDetectionLayout = QHBoxLayout()
        self.acceptButton = QPushButton("Accept All")
        self.rejectButton = QPushButton("Delete current box")
        self.acceptDetectionLayout.addWidget(self.acceptButton)
        self.acceptDetectionLayout.addWidget(self.rejectButton)
        step1Layout.addWidget(self.fliplabelsVButton)
        step1Layout.addWidget(self.flipAllLabelsVButton)
        step1Layout.addWidget(self.fliplabelsHButton)
        step1Layout.addWidget(self.flipAllLabelsHButton)
        step1Layout.addWidget(self.swapXandYButton)
        step1Layout.addWidget(self.applyPreviousBoxesButton)

        self.detectionStep3Layout = QGridLayout()
        self.currentBoxSelectorLabel = QLabel("Current box")
        self.detectionStep3Layout.addWidget(self.currentBoxSelectorLabel, 1, 0)
        self.currentBoxSelector = QComboBox()
        self.detectionStep3Layout.addWidget(self.currentBoxSelector, 1, 1)

        self.xCoordinateSliderLabel = QLabel("X coordinates")
        self.detectionStep3Layout.addWidget(self.xCoordinateSliderLabel, 2, 0)
        self.xCoordinateSlider = QRangeSlider(Qt.Orientation.Horizontal)
        self.xCoordinateSlider.setMinimum(0)
        self.xCoordinateSlider.setMaximum(self.imgShape[1])
        self.detectionStep3Layout.addWidget(self.xCoordinateSlider, 2, 1)

        self.yCoordinateSliderLabel = QLabel("Y coordinates")
        self.detectionStep3Layout.addWidget(self.yCoordinateSliderLabel, 3, 0)
        self.yCoordinateSlider = QRangeSlider(Qt.Orientation.Horizontal)
        self.yCoordinateSlider.setMinimum(0)
        self.yCoordinateSlider.setMaximum(self.imgShape[0])
        self.detectionStep3Layout.addWidget(self.yCoordinateSlider, 3, 1)

        self.addNewBoxButton = QPushButton("Add new box")
        self.detectionStep3Layout.addWidget(self.addNewBoxButton, 4, 0)
        self.addNewBoxSelector = QComboBox()
        self.detectionStep3Layout.addWidget(self.addNewBoxSelector, 4, 1)
        self.addNewBoxSelector.addItems(["Add new class"])

        self.addNewClassButton = QPushButton("Add new class")
        self.newClassLineEdit = QLineEdit("Class name")
        self.newClassLineEdit.visible = False
        self.addNewClassButton.visible = False
        self.detectionStep3Layout.addWidget(self.addNewClassButton, 5, 0)
        self.detectionStep3Layout.addWidget(self.newClassLineEdit, 5, 1)
        step1Layout.addLayout(self.detectionStep3Layout)
        step1Layout.addLayout(self.acceptDetectionLayout)
        self.step1Widget.setLayout(step1Layout)

        # connections
        self.fliplabelsVButton.clicked.connect(self.onFlipLabelsVertically)
        self.fliplabelsHButton.clicked.connect(self.onFlipLabelsHorizontally)
        self.flipAllLabelsVButton.clicked.connect(
            self.onFlipAllLabelsVertically)
        self.flipAllLabelsHButton.clicked.connect(
            self.onFlipAllLabelsHorizontally)
        self.swapXandYButton.clicked.connect(self.onSwapXandYLabels)
        self.applyPreviousBoxesButton.clicked.connect(
            self.onApplyPreviousBoxes)
        self.acceptButton.clicked.connect(self.onApprovalKeyPressed)
        self.rejectButton.clicked.connect(self.deleteCurrentBox)
        self.currentBoxSelector.currentIndexChanged.connect(
            self.updateCoordinateSliders)
        self.xCoordinateSlider.sliderMoved.connect(self.updateBBoxCoordinates)
        self.xCoordinateSlider.sliderReleased.connect(self.updateEditCount)
        self.yCoordinateSlider.sliderMoved.connect(self.updateBBoxCoordinates)
        self.yCoordinateSlider.sliderReleased.connect(self.updateEditCount)
        self.addNewBoxButton.clicked.connect(self.addNewBox)
        self.addNewBoxSelector.currentIndexChanged.connect(
            self.newClassSelected)
        self.addNewClassButton.clicked.connect(
            self.addNewClassesToNewBoxSelector)

    def setupButtonConnections(self):
        self.selectImageDirButton.clicked.connect(self.onSelectImageDirectory)
        self.removeAndRepairButton.clicked.connect(
            self.onRepairGlitchesClicked)
        self.removeImageButton.clicked.connect(self.onRemoveImageClicked)
        self.flipImageHButton.clicked.connect(self.onFlipImageHClicked)
        self.flipAllHButton.clicked.connect(self.onFlipAllImageHClicked)
        self.flipImageVButton.clicked.connect(self.onFlipImageVClicked)
        self.flipAllVButton.clicked.connect(self.onFlipAllImageVClicked)
        self.saveButton.clicked.connect(self.onSaveButtonClicked)
        self.imageSlider.valueChanged.connect(self.onSliderMoved)
        self.previousButton.clicked.connect(self.showPreviousImage)
        self.nextButton.clicked.connect(self.showNextImage)
        self.labelTypeSelectorComboBox.currentIndexChanged.connect(
            self.updateLabelSelector)
        self.labelSelectorComboBox.currentIndexChanged.connect(
            self.updateLabel)
        self.applyPreviousLabelButton.clicked.connect(self.applyPreviousLabel)
        self.blockApplyPreviousLabelButton.clicked.connect(
            self.blockApplyPreviousLabel)
        self.addNewClassificationButton.clicked.connect(
            self.addNewClassification)
        self.approvalCheckBox.clicked.connect(self.approvalStatusChanged)
        self.selectCleanDirButton.clicked.connect(self.onSelectCleanDirectory)
        self.transferImagesButton.clicked.connect(self.onTransferImagesClicked)
        # self.imageLabel.mousePressEvent.connect(self.onImageClicked)
        # self.imageLabel.mouseReleaseEvent.connect(self.onImageClickReleased)

    def addNewClassification(self):
        if self.addNewClassificationLineEdit.text() != "Class name":
            self.labelSelectorComboBox.addItem(
                self.addNewClassificationLineEdit.text())

    def applyPreviousLabel(self):
        labelFound = False
        ind = self.currentIndex - 1
        if ind > 0:
            prevLabel = self.labelFile[self.labelType][ind]
            self.labelFile[self.labelType][self.currentIndex] = prevLabel
            FIX_COUNTER["Overall Task"][FIX_COUNTER.index[-1]] += 1
            labelFound = True
        if not labelFound:
            self.messageLabel.setText("Could not find previous label to apply")

    def blockApplyPreviousLabel(self):
        if self.currentIndex > 0:
            prevLabel = self.labelFile[self.labelType][self.currentIndex-1]
            currentLabel = self.labelFile[self.labelType][self.currentIndex]
            ind = self.currentIndex
            while ind < len(self.labelFile.index) and self.labelFile[self.labelType][ind] == currentLabel:
                self.labelFile[self.labelType][ind] = prevLabel
                ind += 1
                FIX_COUNTER["Overall Task"][FIX_COUNTER.index[-1]] += 1

    def mouseMoveEvent(self, event):
        if "bounding box" in str(self.labelType) and self.modifyBBoxStarted:
            cursorPosition = event.pos()
            cursorPosition = (cursorPosition.x(), cursorPosition.y())
            imageWidgetPosition = (self.imageLabel.x(), self.imageLabel.y())
            imageXCoordinate = max(
                0, min(self.imgShape[1], cursorPosition[0]-imageWidgetPosition[0]))
            imageYCoordinate = max(
                0, min(self.imgShape[0], cursorPosition[1]-imageWidgetPosition[1]))
            boxName = self.currentBoxSelector.currentText()
            bbox = self.bboxDictionary[boxName]
            bbox["xmin"] = min(imageXCoordinate, self.startingPoint[0])
            bbox["ymin"] = min(imageYCoordinate, self.startingPoint[1])
            bbox["xmax"] = max(imageXCoordinate, self.startingPoint[0])
            bbox["ymax"] = max(imageYCoordinate, self.startingPoint[1])
            bboxes = [self.bboxDictionary[x] for x in self.bboxDictionary]
            self.setImageWithDetections(bboxes, updateSliders=False)

    def mousePressEvent(self, event):
        if "bounding box" in str(self.labelType):
            cursorPosition = event.pos()
            cursorPosition = (cursorPosition.x(), cursorPosition.y())
            imageWidgetPosition = (self.imageLabel.x(), self.imageLabel.y())
            if cursorPosition[0] - imageWidgetPosition[0] >= 0 and cursorPosition[0] - imageWidgetPosition[0] <= self.imgShape[1] and cursorPosition[1] - imageWidgetPosition[1] >= 0 and cursorPosition[1] - imageWidgetPosition[1] <= self.imgShape[0]:
                self.modifyBBoxStarted = True

                imageXCoordinate = max(
                    0, min(self.imgShape[1], cursorPosition[0] - imageWidgetPosition[0]))
                imageYCoordinate = max(
                    0, min(self.imgShape[0], cursorPosition[1] - imageWidgetPosition[1]))
                self.startingPoint = (imageXCoordinate, imageYCoordinate)
                boxName = self.currentBoxSelector.currentText()
                bbox = self.bboxDictionary[boxName]
                bbox["xmin"] = imageXCoordinate
                bbox["ymin"] = imageYCoordinate
                bbox["xmax"] = imageXCoordinate
                bbox["ymax"] = imageYCoordinate
                bboxes = [self.bboxDictionary[x] for x in self.bboxDictionary]
                self.setImageWithDetections(bboxes, updateSliders=False)

    def mouseReleaseEvent(self, event):
        if "bounding box" in str(self.labelType):
            cursorPosition = event.pos()
            cursorPosition = (cursorPosition.x(), cursorPosition.y())
            imageWidgetPosition = (self.imageLabel.x(), self.imageLabel.y())
            if cursorPosition[0] - imageWidgetPosition[0] >= 0 and cursorPosition[0] - imageWidgetPosition[0] <= self.imgShape[1] and cursorPosition[1] - imageWidgetPosition[1] >= 0 and cursorPosition[1] - imageWidgetPosition[1] <= self.imgShape[0]:
                self.modifyBBoxStarted = False
                imageXCoordinate = max(
                    0, min(self.imgShape[1], cursorPosition[0] - imageWidgetPosition[0]))
                imageYCoordinate = max(
                    0, min(self.imgShape[0], cursorPosition[1] - imageWidgetPosition[1]))
                boxName = self.currentBoxSelector.currentText()
                bbox = self.bboxDictionary[boxName]
                bbox["xmin"] = min(imageXCoordinate, self.startingPoint[0])
                bbox["ymin"] = min(imageYCoordinate, self.startingPoint[1])
                bbox["xmax"] = max(imageXCoordinate, self.startingPoint[0])
                bbox["ymax"] = max(imageYCoordinate, self.startingPoint[1])
                bboxes = [self.bboxDictionary[x] for x in self.bboxDictionary]
                self.setImageWithDetections(bboxes)
                ind = self.currentBoxSelector.findText(boxName)
                self.currentBoxSelector.setCurrentIndex(ind)
                FIX_COUNTER["Edit box"][FIX_COUNTER.index[-1]] += 1

    def checkForMissingImages(self):
        indexesToRemove = []
        for i in self.labelFile.index:
            imagePath = os.path.join(
                self.imageDirectory, self.labelFile["FileName"][i])
            if not os.path.exists(imagePath):
                indexesToRemove.append(i)
        self.labelFile = self.labelFile.drop(indexesToRemove)
        self.labelFile.index = [i for i in range(len(self.labelFile.index))]
    
    def onSelectImageDirectory(self):
        window = QWidget()
        window.setWindowTitle("Select Image Directory")
        self.imageDirectory = QFileDialog.getExistingDirectory(window, "C://")
        self.labelTypeSelectorComboBox.setCurrentText("Select label type")
        videoId = os.path.basename(os.path.dirname(self.imageDirectory))
        subtype = os.path.basename(self.imageDirectory)
        FIX_COUNTER["Video"][FIX_COUNTER.index[-1]] = self.imageDirectory
        file = os.path.join(self.imageDirectory,"{}_{}_Labels.csv".format(videoId, subtype))
        if not (os.path.exists(file)):
            listJpgFiles = [f for f in os.listdir(self.imageDirectory) if os.path.isfile(os.path.join(self.imageDirectory, f)) and f.lower().endswith(".jpg")]
            with open(file, "w+", newline='') as f:
                writer = csv.writer(f)
                header = ['FileName']
                writer.writerow(header)
                writer.writerows([[jpgFile] for jpgFile in listJpgFiles])
        if os.path.exists(file):
            #print("foundLabelFile")
            self.previousButton.setEnabled(True)
            self.nextButton.setEnabled(True)
            self.imageSlider.setEnabled(True)
            self.videoID = videoId
            self.subtype = subtype
            self.labelFile = pandas.read_csv(os.path.join(
                self.imageDirectory, "{}_{}_Labels.csv".format(videoId, subtype)))
            self.checkForMissingImages()
            self.imageSlider.setMinimum(0)
            self.imageSlider.setMaximum(len(self.labelFile.index)-1)
            self.imageDirectoryLabel.setText(
                "Image Directory: \n{}".format(self.imageDirectory))
            self.setImage(self.labelFile["FileName"][0])
            FIX_COUNTER["Total"][FIX_COUNTER.index[-1]
                                 ] = len(self.labelFile.index)
            self.currentIndex = 0
            self.getReviewStatus()
            self.updateLabelUI()
        elif os.path.exists(os.path.join(self.imageDirectory, "{}_Labels.csv".format(subtype))):
            self.videoID = subtype
            self.subtype = None
            self.previousButton.setEnabled(True)
            self.nextButton.setEnabled(True)
            self.imageSlider.setEnabled(True)
            self.labelFile = pandas.read_csv(os.path.join(
                self.imageDirectory, "{}_Labels.csv".format(subtype)))
            self.checkForMissingImages()
            self.imageSlider.setMinimum(0)
            self.imageSlider.setMaximum(len(self.labelFile.index)-1)
            self.imageDirectoryLabel.setText(
                "Image Directory: \n\n{}".format(self.imageDirectory))
            self.setImage(self.labelFile["FileName"][0])
            self.currentIndex = 0
            self.updateLabelUI()
            self.getReviewStatus()
            FIX_COUNTER["Total"][FIX_COUNTER.index[-1]
                                 ] = len(self.labelFile.index)
        else:
            self.previousButton.setEnabled(False)
            self.nextButton.setEnabled(False)
            self.imageSlider.setEnabled(False)
            self.imageDirectoryLabel.setText(
                "Image Directory: \n\n{}".format("Could not find label file in folder"))
            self.setImage()

    def onSelectCleanDirectory(self):
        window = QWidget()
        window.setWindowTitle("Select Clean Image Directory")
        self.cleanDirectory = QFileDialog.getExistingDirectory(window, "C://")
        self.cleanDirectoryLabel.setText(
            "Clean Image Directory: \n\n{}".format(self.cleanDirectory))

    def onTransferImagesClicked(self):
        try:
            if self.subtype == None:
                labelFileName = "{}/{}_Labels.csv".format(
                    self.videoID, self.videoID)
                videoPath = self.videoID
            else:
                labelFileName = "{}/{}/{}_{}_Labels.csv".format(
                    self.videoID, self.subtype, self.videoID, self.subtype)
                videoPath = os.path.join(self.videoID, self.subtype)
            if not os.path.exists(os.path.join(self.cleanDirectory, self.videoID)):
                os.mkdir(os.path.join(self.cleanDirectory, self.videoID))
            if self.subtype != None and not os.path.exists(os.path.join(self.cleanDirectory, self.videoID, self.subtype)):
                os.mkdir(os.path.join(self.cleanDirectory,
                         self.videoID, self.subtype))
            if not os.path.exists(os.path.join(self.cleanDirectory, labelFileName)):
                correctedLabelFile = pandas.DataFrame()
                correctedLabelFile["FileName"] = self.labelFile["FileName"]
                correctedLabelFile["Time Recorded"] = self.labelFile["Time Recorded"]
                correctedLabelFile[self.labelType] = self.labelFile[self.labelType]
                correctedLabelFile.to_csv(os.path.join(
                    self.cleanDirectory, labelFileName), index=False)
            else:
                self.existingFile = pandas.read_csv(
                    os.path.join(self.cleanDirectory, labelFileName))
                if len(self.existingFile.index) >= len(self.labelFile.index):
                    self.existingFile[self.labelType] = self.labelFile[self.labelType]
                    self.existingFile.to_csv(os.path.join(
                        self.cleanDirectory, labelFileName), index=False)
                else:
                    self.messageLabel.setText(
                        "Mismatched number of images in clean directory")
                    return
            for i in self.labelFile.index:
                try:
                    shutil.copy(os.path.join(self.imageDirectory, self.labelFile["FileName"][i]),
                                os.path.join(self.cleanDirectory, videoPath, self.labelFile["FileName"][i]))
                    if "segmentation" in self.labelFile[self.labelType][i]:
                        shutil.copy(os.path.join(self.imageDirectory, self.labelFile[self.labelType][i]),
                                    os.path.join(self.cleanDirectory, videoPath, self.labelFile[self.labelType][i]))
                except FileNotFoundError:
                    self.messageLabel.setText(
                        "Could not find file: {}".format(self.labelFile["FileName"][i]))
            self.messageLabel.setText(
                "Copied images and labels to clean directory")
        except AttributeError:
            self.messageLabel.setText(
                "Must select clean directory location first")

    def getReviewStatus(self):
        currentPath = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(os.path.join(currentPath, "ReviewStatuses")):
            os.mkdir(os.path.join(currentPath, "ReviewStatuses"))
        if self.subtype != None:
            vidReviewStatusFileName = "{}_{}_reviewStatus.csv".format(
                self.videoID, self.subtype)
        else:
            vidReviewStatusFileName = "{}_reviewStatus.csv".format(
                self.videoID)
        self.videoStatusPath = os.path.join(
            currentPath, "ReviewStatuses", vidReviewStatusFileName)
        print(self.videoStatusPath)
        if not os.path.exists(self.videoStatusPath):
            self.videoStatus = pandas.DataFrame()
            for col in self.labelFile.columns:
                if col != "FileName" and col != "Time Recorded" and not "Unnamed" in col:
                    self.videoStatus[col] = [
                        False for i in self.labelFile.index]
        else:
            self.videoStatus = pandas.read_csv(self.videoStatusPath)
            if len(self.videoStatus.index) > len(self.labelFile.index):
                indexesToRemove = [
                    x for x in self.videoStatus.index if not x in self.labelFile.index]
                self.videoStatus = self.videoStatus.drop(indexesToRemove)
            elif len(self.videoStatus.index) < len(self.labelFile.index):
                indexesToAdd = len(
                    [x for x in self.labelFile.index if not x in self.videoStatus.index])
                rowsToAdd = {}
                for col in self.labelFile.columns:
                    if col != "FileName" and col != "Time Recorded" and not "Unnamed" in col:
                        rowsToAdd[col] = [False for i in range(indexesToAdd)]
                self.videoStatus = pandas.concat(
                    [self.videoStatus, pandas.DataFrame(rowsToAdd)])
                self.videoStatus.index = [
                    i for i in range(len(self.videoStatus.index))]

    def updateLabelUI(self):
        numItems = self.labelTypeSelectorComboBox.count()
        for i in range(numItems-1, 0, -1):
            self.labelTypeSelectorComboBox.removeItem(i)
        self.labelTypeSelectorComboBox.addItems(
            [col for col in self.labelFile.columns if col != "FileName" and col != "Time Recorded" and not "Unnamed" in col])

    def updateLabelSelector(self):
        self.labelType = self.labelTypeSelectorComboBox.currentText()
        prevLabels = self.labelSelectorComboBox.count()
        if prevLabels > 2:
            for i in range(prevLabels - 1, 1, -1):
                self.labelSelectorComboBox.removeItem(i)
        if self.labelType != "Select label type":
            if "bounding box" in self.labelType:
                self.labelFile[self.labelType] = [
                    eval(str(self.labelFile[self.labelType][i])) for i in self.labelFile.index]
                self.detectionLabels = self.getClassNames()
                self.addClassesToNewBoxSelector()
                self.blankSegmentationButton.setEnabled(False)
                self.setImageWithDetections(
                    self.labelFile[self.labelType][self.currentIndex])
            elif "segmentation" in self.labelFile[self.labelType][self.currentIndex]:
                self.blankSegmentationButton.setEnabled(True)
                self.setSegmentationImage(
                    self.labelFile[self.labelType][self.currentIndex])
            else:
                self.blankSegmentationButton.setEnabled(False)
                labels = self.labelFile[self.labelType].unique()
                self.labelSelectorComboBox.addItems(labels)
                self.labelSelectorComboBox.setCurrentText(
                    self.labelFile[self.labelType][self.currentIndex])
            try:
                self.approvalStatus = self.videoStatus[self.labelType][self.currentIndex]
                if self.approvalStatus:
                    self.approvalCheckBox.setChecked(True)
                else:
                    self.approvalCheckBox.setChecked(False)
            except KeyError:
                self.videoStatus[self.labelType] = [
                    False for i in self.labelFile.index]
                self.approvalStatus = False
                self.approvalCheckBox.setChecked(False)
            self.updateApprovalStatusLabel()

    def getClassNames(self):
        uniqueNames = []
        for i in self.labelFile.index:
            bboxes = self.labelFile[self.labelType][i]
            if isinstance(bboxes, dict):
                bboxes = [bboxes]
                self.labelFile[self.labelType][i] = bboxes
            for bbox in bboxes:
                if not bbox["class"] in uniqueNames:
                    uniqueNames.append(bbox["class"])

        return sorted(uniqueNames)

    def addClassesToNewBoxSelector(self):
        self.addNewBoxSelector.addItems(self.detectionLabels)

    def addNewClassesToNewBoxSelector(self):
        if not self.newClassLineEdit.text() == "Class name":
            self.addNewBoxSelector.addItems(
                [str(self.newClassLineEdit.text())])
            self.addNewBoxSelector.setCurrentText(self.newClassLineEdit.text())

    def findClosestBox(self, className):
        bestBox = None
        i = self.currentIndex
        while i > max(0, self.currentIndex-10) and bestBox == None:
            prevBBoxes = self.labelFile[self.labelType][i]
            for box in prevBBoxes:
                if box["class"] == className:
                    bestBox = box.copy()
            i -= 1
        if bestBox == None:
            i = self.currentIndex
            while i < min(len(self.labelFile.index), self.currentIndex + 10) and bestBox == None:
                prevBBoxes = self.labelFile[self.labelType][i]
                for box in prevBBoxes:
                    if box["class"] == className:
                        bestBox = box.copy()
                i += 1
        if bestBox == None:
            bestBox = {"class": className,
                       "xmin": (self.imgShape[1]//2)-50,
                       "xmax": (self.imgShape[1]//2)+50,
                       "ymin": (self.imgShape[0] // 2) - 50,
                       "ymax": (self.imgShape[0] // 2) + 50}
        return bestBox

    def addNewBox(self):
        FIX_COUNTER["Missing box"][FIX_COUNTER.index[-1]] += 1
        newBoxClass = self.addNewBoxSelector.currentText()
        closestBox = self.findClosestBox(newBoxClass)
        if str(closestBox) in str(self.labelFile[self.labelType][self.currentIndex]):
            closestBox["xmin"] += 1
            closestBox["ymin"] += 1
        print(self.labelFile[self.labelType][self.currentIndex])
        self.labelFile[self.labelType][self.currentIndex].append(closestBox)
        print(self.labelFile[self.labelType][self.currentIndex])
        self.setImageWithDetections(
            self.labelFile[self.labelType][self.currentIndex].copy())
        self.currentBoxSelector.setCurrentIndex(
            self.currentBoxSelector.count()-1)

    def newClassSelected(self):
        if self.addNewBoxSelector.currentText() == "Add new class":
            self.newClassLineEdit.visible = True
            self.addNewClassButton.visible = True
        else:
            self.newClassLineEdit.visible = False
            self.addNewClassButton.visible = False

    def createDetectionCheckBoxes(self):
        self.detectionCheckBoxes = {}
        self.detectionClassCheckBoxLayout.addWidget(QLabel("Present"), 1, 0)
        self.detectionClassCheckBoxLayout.addWidget(QLabel("Correct"), 1, 1)
        self.checkBoxList = [[], [], []]
        for i in range(len(self.detectionLabels)):
            label = self.detectionLabels[i]
            presentCheckBox = QCheckBox()
            correctCheckBox = QCheckBox()
            classLabel = QLabel(label)
            self.checkBoxList[0].append(label)
            self.checkBoxList[1].append(presentCheckBox)
            self.checkBoxList[2].append(correctCheckBox)
            self.detectionCheckBoxes[label] = [
                presentCheckBox, correctCheckBox]
            self.detectionClassCheckBoxLayout.addWidget(
                presentCheckBox, i+2, 0)
            self.detectionClassCheckBoxLayout.addWidget(
                correctCheckBox, i+2, 1)
            self.detectionClassCheckBoxLayout.addWidget(classLabel, i + 2, 2)
        self.nextStepButton = QPushButton("Next")
        self.detectionClassCheckBoxLayout.addWidget(
            self.nextStepButton, len(self.detectionLabels)+2, 2, 1, 2)
        self.nextStepButton.clicked.connect(self.proceedToNextStepButton)

    def onFlipLabelsVertically(self, boxIndex=-1):
        FIX_COUNTER["Edit box"][FIX_COUNTER.index[-1]] += 1
        if boxIndex == -1:
            boxIndex = self.currentIndex
        bboxes = self.labelFile[self.labelType][boxIndex]
        img = cv2.imread(os.path.join(self.imageDirectory,
                         self.labelFile["FileName"][self.currentIndex]))
        imgHeight = img.shape[0]
        for bbox in bboxes:
            oldYmin = int(bbox["ymin"])
            oldYmax = int(bbox["ymax"])
            bbox["ymin"] = imgHeight-oldYmax
            bbox["ymax"] = imgHeight-oldYmin
            bbox["xmin"] = int(bbox["xmin"])
            bbox["xmax"] = int(bbox["xmax"])
        self.labelFile[self.labelType][boxIndex] = bboxes.copy()
        self.setImageWithDetections(
            self.labelFile[self.labelType][self.currentIndex])

    def onFlipAllLabelsVertically(self):
        for i in self.labelFile.index:
            self.onFlipLabelsVertically(boxIndex=i)

    def onFlipAllLabelsHorizontally(self):
        for i in self.labelFile.index:
            self.onFlipLabelsHorizontally(boxIndex=i)

    def onFlipLabelsHorizontally(self, boxIndex=-1):
        FIX_COUNTER["Edit box"][FIX_COUNTER.index[-1]] += 1
        if boxIndex == -1:
            boxIndex = self.currentIndex
        bboxes = self.labelFile[self.labelType][boxIndex]
        img = cv2.imread(os.path.join(self.imageDirectory,
                         self.labelFile["FileName"][self.currentIndex]))
        imgWidth = img.shape[1]
        for bbox in bboxes:
            oldXmin = int(bbox["xmin"])
            oldXmax = int(bbox["xmax"])
            bbox["xmin"] = imgWidth - oldXmax
            bbox["xmax"] = imgWidth - oldXmin
            bbox["ymin"] = int(bbox["ymin"])
            bbox["ymax"] = int(bbox["ymax"])
        self.labelFile[self.labelType][boxIndex] = bboxes.copy()
        self.setImageWithDetections(
            self.labelFile[self.labelType][self.currentIndex])

    def onSwapXandYLabels(self):
        FIX_COUNTER["Edit box"][FIX_COUNTER.index[-1]] += 1
        bboxes = self.labelFile[self.labelType][self.currentIndex]
        for bbox in bboxes:
            oldXmin = int(bbox["xmin"])
            oldXmax = int(bbox["xmax"])
            oldYmin = int(bbox["ymin"])
            oldYmax = int(bbox["ymax"])
            bbox["ymin"] = oldXmin
            bbox["ymax"] = oldXmax
            bbox["xmin"] = oldYmin
            bbox["xmax"] = oldYmax
        self.labelFile[self.labelType][self.currentIndex] = bboxes
        self.setImageWithDetections(
            self.labelFile[self.labelType][self.currentIndex])

    def onApplyPreviousBoxes(self):
        boxesFound = False
        ind = self.currentIndex-1
        while ind >= 0 and not boxesFound:
            prevBoxes = [x.copy() for x in self.labelFile[self.labelType][ind]]
            FIX_COUNTER["Missing box"][FIX_COUNTER.index[-1]] += len(prevBoxes)
            if len(prevBoxes) > 0:
                self.setImageWithDetections(prevBoxes)
                boxesFound = True
            ind -= 1
        if not boxesFound:
            self.messageLabel.setText("Could not find previous boxes to apply")

    def removeDuplicateBoxes(self, bboxes):
        indsToRemove = []
        for i in range(len(bboxes)):
            for j in range(i, len(bboxes)):
                if i != j and bboxes[i]["class"] == bboxes[j]["class"] and not j in indsToRemove:
                    if bboxes[i]["xmin"] == bboxes[j]["xmin"] and bboxes[i]["xmax"] == bboxes[j]["xmax"] and bboxes[i]["ymin"] == bboxes[j]["ymin"] and bboxes[i]["ymax"] == bboxes[j]["ymax"]:
                        indsToRemove.append(j)
        for i in range(len(indsToRemove)-1, -1, -1):
            del bboxes[indsToRemove[i]]
        return bboxes

    def removeAllItems(self, comboBox):
        for i in range(comboBox.count()-1, -1, -1):
            comboBox.removeItem(i)

    def updateDetectionLabels(self, bboxes, updateSliders=True):
        self.bboxDictionary = {}
        classCounts = {}
        bboxes = self.removeDuplicateBoxes(bboxes)
        self.labelFile[self.labelType][self.currentIndex] = bboxes
        self.removeAllItems(self.currentBoxSelector)
        for box in bboxes:
            className = box["class"]
            if not className in classCounts:
                classCounts[className] = 1
            else:
                classCounts[className] += 1
            boxName = "{} ({})".format(className, classCounts[className])
            self.bboxDictionary[boxName] = box
            self.currentBoxSelector.addItem(boxName)
        if updateSliders:
            self.updateCoordinateSliders()

    def updateCoordinateSliders(self):
        try:
            currentBoxName = self.currentBoxSelector.currentText()
            currentBox = self.bboxDictionary[currentBoxName]
            self.xCoordinateSlider.blockSignals(True)
            self.yCoordinateSlider.blockSignals(True)
            self.xCoordinateSlider.setValue(
                (int(currentBox["xmin"]), int(currentBox["xmax"])))
            self.yCoordinateSlider.setValue(
                (self.imgShape[0]-int(currentBox["ymax"]), self.imgShape[0]-int(currentBox["ymin"])))
            self.xCoordinateSlider.blockSignals(False)
            self.yCoordinateSlider.blockSignals(False)
        except KeyError:
            pass

    def updateBBoxCoordinates(self):
        # FIX_COUNTER["Edit box"][FIX_COUNTER.index[-1]] += 1
        currentBoxName = self.currentBoxSelector.currentText()
        currentBox = self.bboxDictionary[currentBoxName]
        xSliderValues = self.xCoordinateSlider.value()
        ySliderValues = self.yCoordinateSlider.value()
        currentBox["xmin"] = xSliderValues[0]
        currentBox["xmax"] = xSliderValues[1]
        currentBox["ymin"] = self.imgShape[0]-ySliderValues[1]
        currentBox["ymax"] = self.imgShape[0]-ySliderValues[0]
        self.setImageWithDetections(
            [self.bboxDictionary[x] for x in self.bboxDictionary], updateSliders=False)

    def updateEditCount(self):
        FIX_COUNTER["Edit box"][FIX_COUNTER.index[-1]] += 1

    def deleteCurrentBox(self):
        FIX_COUNTER["Edit box"][FIX_COUNTER.index[-1]] += 1
        currentBoxName = self.currentBoxSelector.currentText()
        try:
            del self.bboxDictionary[currentBoxName]
            self.setImageWithDetections(
                [self.bboxDictionary[x] for x in self.bboxDictionary])
        except KeyError:
            pass

    def updateLabel(self, indexValue):
        self.labelType = self.labelTypeSelectorComboBox.currentText()
        if self.labelType != "Select label type":
            if indexValue < 0:
                try:
                    self.labelSelectorComboBox.setCurrentText(
                        self.labelFile[self.labelType][self.currentIndex])
                except TypeError:
                    self.labelSelectorComboBox.setCurrentText("Bounding box")
                    self.setImageWithDetections(
                        self.labelFile[self.labelType][self.currentIndex])
                if "segmentation" in self.labelFile[self.labelType][self.currentIndex]:
                    self.setSegmentationImage(
                        self.labelFile[self.labelType][self.currentIndex])
                try:
                    self.approvalStatus = self.videoStatus[self.labelType][self.currentIndex]
                except KeyError:
                    self.videoStatus = pandas.concat([self.videoStatus, pandas.DataFrame(dict(
                        zip(self.videoStatus.columns, [[False] for x in self.videoStatus.columns])))])
                    self.videoStatus.index = [
                        x for x in range(len(self.videoStatus.index))]
                    self.approvalStatus = self.videoStatus[self.labelType][len(
                        self.videoStatus.index)-1]
                if self.approvalStatus:
                    self.approvalCheckBox.setChecked(True)
                else:
                    self.approvalCheckBox.setChecked(False)

            else:
                label = self.labelSelectorComboBox.currentText()
                if label != "Select label" and label != "Add new label":
                    if label != self.labelFile[self.labelType][self.currentIndex]:
                        FIX_COUNTER["Overall Task"][FIX_COUNTER.index[-1]] += 1
                    self.labelFile[self.labelType][self.currentIndex] = label
                    self.approvalCheckBox.setChecked(False)

    def onApprovalKeyPressed(self):
        if self.labelTypeSelectorComboBox.currentText() != "Select label type":
            self.approvalStatus = True
            self.approvalCheckBox.setChecked(True)
            self.approvalStatusChanged()
            self.nextButton.click()

    def approvalStatusChanged(self):
        self.approvalStatus = self.approvalCheckBox.isChecked()
        self.videoStatus[self.labelType][self.currentIndex] = self.approvalStatus
        self.videoStatus.to_csv(self.videoStatusPath, index=False)
        self.updateApprovalStatusLabel()

    def updateApprovalStatusLabel(self):
        if not self.labelType in self.videoStatus.columns:
            print("her")
            self.videoStatus[self.labelType] = [False for i in self.videoStatus.index]
        approvalCounts = self.videoStatus[self.labelType].value_counts()
        print(self.videoStatus.index)
        if len(approvalCounts.index) == 1:
            try:
                self.numRemaining = approvalCounts[False]
                self.numApproved = 0
            except KeyError:
                self.numApproved = approvalCounts[True]
                self.numRemaining = 0
        else:
            self.numRemaining = approvalCounts[False]
            self.numApproved = approvalCounts[True]
        self.approvalRemainingLabel.setText(
            "{} / {} labels approved".format(self.numApproved, len(self.labelFile.index)))
        if self.numApproved >= len(self.labelFile.index):
            self.transferImagesButton.setEnabled(True)
        else:
            self.transferImagesButton.setEnabled(False)

    def setImage(self, fileName=None):
        if fileName == None:
            image = numpy.zeros((480, 640, 3))
            self.imgShape = image.shape
            height, width, channel = image.shape
            bytesPerLine = 3 * width
            qImage = QImage(image.data, width, height,
                            bytesPerLine, QImage.Format.Format_RGB888)
            pixelmap = QPixmap.fromImage(qImage)
        else:
            img = cv2.imread(os.path.join(self.imageDirectory, fileName))
            self.imgShape = img.shape
            pixelmap = QPixmap(os.path.join(self.imageDirectory, fileName))
        self.imageLabel.setPixmap(pixelmap)

    def setImageWithDetections(self, bboxes, updateSliders=True):
        img = cv2.imread(os.path.join(self.imageDirectory,
                         self.labelFile["FileName"][self.currentIndex]))
        self.imgShape = img.shape
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # bboxes = self.labelFile[self.labelType][self.currentIndex]
        if isinstance(bboxes, dict):
            bboxes = [bboxes]
        for bbox in bboxes:
            img = cv2.rectangle(img, (int(bbox["xmin"]), int(bbox["ymin"])), (int(
                bbox["xmax"]), int(bbox["ymax"])), (255, 0, 0), 2)
            cv2.putText(img,
                        bbox["class"], (int(bbox["xmin"]),
                                        int(bbox["ymin"]) - 10),
                        0,
                        0.5,
                        (255, 0, 0),
                        thickness=1,
                        lineType=cv2.LINE_AA)
        height, width, channel = img.shape
        bytesPerLine = 3 * width
        qImage = QImage(img.data, width, height, bytesPerLine,
                        QImage.Format.Format_RGB888)
        pixelmap = QPixmap.fromImage(qImage)
        self.imageLabel.setPixmap(pixelmap)
        self.labelFile[self.labelType][self.currentIndex] = bboxes
        print(self.labelFile[self.labelType][self.currentIndex])
        if updateSliders:
            self.updateDetectionLabels(bboxes, updateSliders)

    def onSliderMoved(self):
        self.currentIndex = self.imageSlider.value()
        if self.currentIndex == 0:
            self.previousButton.setEnabled(False)
            self.nextButton.setEnabled(True)
        elif self.currentIndex == self.imageSlider.maximum():
            self.nextButton.setEnabled(False)
            self.previousButton.setEnabled(True)
        print(self.labelFile["FileName"])
        self.setImage(self.labelFile["FileName"][self.currentIndex])
        self.updateLabel(indexValue=-1)

    def showPreviousImage(self):
        self.nextButton.setEnabled(True)
        if self.currentIndex > 0:
            self.currentIndex -= 1
        if self.currentIndex == 0:
            self.previousButton.setEnabled(False)
        self.imageSlider.setValue(self.currentIndex)
        self.setImage(self.labelFile["FileName"][self.currentIndex])
        self.updateLabel(indexValue=-1)

    def showNextImage(self):
        self.previousButton.setEnabled(True)
        if self.currentIndex < len(self.labelFile.index)-1:
            self.currentIndex += 1
        if self.currentIndex == len(self.labelFile.index)-1:
            self.nextButton.setEnabled(False)
        self.imageSlider.setValue(self.currentIndex)
        self.setImage(self.labelFile["FileName"][self.currentIndex])
        self.updateLabel(indexValue=-1)

    def onSaveButtonClicked(self):
        if self.subtype == None:
            labelFilePath = os.path.join(
                self.imageDirectory, "{}_Labels.csv".format(self.videoID))

        else:
            labelFilePath = os.path.join(
                self.imageDirectory, "{}_{}_Labels.csv".format(self.videoID, self.subtype))

        try:
            self.labelFile.to_csv(labelFilePath, index=False)
            self.messageLabel.setText("Changes saved")
        except:
            tempFilePath = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), os.path.basename(labelFilePath))
            self.messageLabel.setText("Permission denied on {}\nSaving copy to: {}".format(
                labelFilePath, tempFilePath))
        self.videoStatus.to_csv(self.videoStatusPath, index=False)

    def onRepairGlitchesClicked(self):
        numGlitches = 0
        maxIndex = self.labelFile.index[-1]
        maxTime = math.ceil(float(self.labelFile["Time Recorded"][maxIndex]))
        indexesToRemove = []
        for i in range(1, maxTime + 1):
            images = self.labelFile.loc[
                (self.labelFile["Time Recorded"] > i - 1) & (self.labelFile["Time Recorded"] <= i)]
            if len(images.index) > 30:
                numGlitches += 1
                for k in range(10):
                    glitchedImages = images.loc[(self.labelFile["Time Recorded"] > (i - 1) + (k / 10.0)) & (
                        self.labelFile["Time Recorded"] <= (i - 1) + ((k + 1) / 10.0))]
                    if len(glitchedImages) > 3:
                        for j in glitchedImages.index:
                            indexesToRemove.append(j)
        self.labelFile = self.labelFile.drop(indexesToRemove)
        self.videoStatus = self.videoStatus.drop(indexesToRemove)
        self.labelFile.index = [i for i in range(len(self.labelFile.index))]
        self.videoStatus.index = [
            i for i in range(len(self.videoStatus.index))]
        self.messageLabel.setText(
            "Removed {} glitched frames".format(len(indexesToRemove)))
        self.imageSlider.setMaximum(len(self.labelFile.index))

    def onRemoveImageClicked(self):
        rowToDrop = self.currentIndex
        self.labelFile = self.labelFile.drop(rowToDrop)
        self.videoStatus = self.videoStatus.drop(rowToDrop)
        self.labelFile.index = [i for i in range(len(self.labelFile.index))]
        self.videoStatus.index = [
            i for i in range(len(self.videoStatus.index))]
        if self.currentIndex > self.labelFile.index[-1]:
            self.currentIndex = self.labelFile.index[-1]
        self.setImage(self.labelFile["FileName"][self.currentIndex])
        self.messageLabel.setText("Image Removed")
        FIX_COUNTER["Total"][FIX_COUNTER.index[-1]] -= 1
        # self.imageSlider.setMaximum(len(self.labelFile.index))

    def onFlipImageHClicked(self):
        imagePath = os.path.join(
            self.imageDirectory, self.labelFile["FileName"][self.currentIndex])
        image = cv2.imread(imagePath)
        image = cv2.flip(image, 1)
        cv2.imwrite(imagePath, image)
        # self.setImage(self.labelFile["FileName"][self.currentIndex])

    def onFlipAllImageHClicked(self):
        for i in self.labelFile.index:
            if os.path.exists(imagePath):
                imagePath = os.path.join(
                    self.imageDirectory, self.labelFile["FileName"][i])
                image = cv2.imread(imagePath)
                image = cv2.flip(image, 1)
                cv2.imwrite(imagePath, image)
            else:
                self.labelFile.drop([i])
        self.setImage(self.labelFile["FileName"][self.currentIndex])

    def onFlipImageVClicked(self):
        imagePath = os.path.join(
            self.imageDirectory, self.labelFile["FileName"][self.currentIndex])
        image = cv2.imread(imagePath)
        image = cv2.flip(image, 0)
        cv2.imwrite(imagePath, image)
        self.setImage(self.labelFile["FileName"][self.currentIndex])

    def onFlipAllImageVClicked(self):
        for i in self.labelFile.index:
            imagePath = os.path.join(
                self.imageDirectory, self.labelFile["FileName"][i])
            if os.path.exists(imagePath):
                image = cv2.imread(imagePath)
                image = cv2.flip(image, 0)
                cv2.imwrite(imagePath, image)
            else:
                self.labelFile.drop([i])
        self.setImage(self.labelFile["FileName"][self.currentIndex])


if __name__ == "__main__":
    app = QApplication([])
    anReviewer = AnnotationReviewer()
    app.exec()
    FIX_COUNTER["Time"][FIX_COUNTER.index[-1]] = time.time() - \
        FIX_COUNTER["Time"][FIX_COUNTER.index[-1]]
    FIX_COUNTER["Pass"][FIX_COUNTER.index[-1]] = (FIX_COUNTER["Overall Task"][FIX_COUNTER.index[-1]]/FIX_COUNTER["Total"][FIX_COUNTER.index[-1]] <= 0.1) and (
        FIX_COUNTER["Missing box"][FIX_COUNTER.index[-1]] + FIX_COUNTER["Edit box"][FIX_COUNTER.index[-1]])/(2*FIX_COUNTER["Total"][FIX_COUNTER.index[-1]]) <= 0.1
    FIX_COUNTER.to_csv(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "fix_counter.csv"), index=False)
    sys.exit()

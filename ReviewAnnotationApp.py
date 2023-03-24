import os
import shutil
import sys
import numpy
import cv2
import pandas
import math

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication,QLabel,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QPushButton,QSpacerItem,QFileDialog,QTabWidget,QComboBox,QCheckBox,QSlider
from PyQt6.QtGui import QImage,QPixmap,QShortcut,QKeySequence
class AnnotationReviewer:
    def addWidgetsToWindow(self,window):
        self.mainWindow = window
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
        self.removeAndRepairButton = QPushButton("Remove and Repair Glitches")
        layout.addWidget(self.removeAndRepairButton)
        layout.addItem(QSpacerItem(100,20))
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
        layout.addItem(QSpacerItem(100,20))
        layout.addWidget(self.saveButton)
        layout.addWidget(self.messageLabel)
        mainLayout.addLayout(layout)

        mainLayout.addItem(QSpacerItem(20,100))
        #############################
        # Create Image layout
        #############################
        imageLayout = QVBoxLayout()
        self.imageLabel = QLabel()
        image = numpy.zeros((480,640,3))
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        qImage = QImage(image.data,width,height,bytesPerLine,QImage.Format.Format_RGB888)
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
        self.labelTypeSelectorComboBox.addItem("Select label type")
        labellayout.addWidget(self.labelTypeSelectorComboBox)
        self.labelToolTabWidget = QTabWidget()
        self.classificationToolWidget = QWidget()
        classificationLayout = QVBoxLayout()
        self.setupClassificationToolLayout(classificationLayout)
        self.classificationToolWidget.setLayout(classificationLayout)
        self.labelToolTabWidget.addTab(self.classificationToolWidget,"Classification")
        self.detectionToolWidget = QWidget()
        detectionLayout = QVBoxLayout()
        self.setupDetectionToolLayout(detectionLayout)
        self.detectionToolWidget.setLayout(detectionLayout)
        self.labelToolTabWidget.addTab(self.detectionToolWidget, "Detection")
        self.segmentationToolWidget = QWidget()
        segmentationLayout = QVBoxLayout()
        self.setupSegmentationToolLayout(segmentationLayout)
        self.segmentationToolWidget.setLayout(segmentationLayout)
        self.labelToolTabWidget.addTab(self.segmentationToolWidget, "Segmentation")
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

        window.setLayout(mainLayout)
        self.setupHotkeys()

    def setupHotkeys(self):
        saveShortcut = QShortcut(self.mainWindow)
        saveShortcut.setKey("Ctrl+s")
        saveShortcut.activated.connect(self.onSaveButtonClicked)

        approveShortcut = QShortcut(self.mainWindow)
        approveShortcut.setKey("y")
        approveShortcut.activated.connect(self.onApprovalKeyPressed)

        verticalFlipShortcut = QShortcut(self.mainWindow)
        verticalFlipShortcut.setKey("v")
        verticalFlipShortcut.activated.connect(self.flipImageVButton.click)

        allVerticalFlipShortcut = QShortcut(self.mainWindow)
        allVerticalFlipShortcut.setKey("Ctrl+v")
        allVerticalFlipShortcut.activated.connect(self.flipAllVButton.click)

        horizontalFlipShortcut = QShortcut(self.mainWindow)
        horizontalFlipShortcut.setKey("h")
        horizontalFlipShortcut.activated.connect(self.flipImageHButton.click)

        allhorizontalFlipShortcut = QShortcut(self.mainWindow)
        allhorizontalFlipShortcut.setKey("Ctrl+h")
        allhorizontalFlipShortcut.activated.connect(self.flipAllHButton.click)

        nextShortcut = QShortcut(self.mainWindow)
        nextShortcut.setKey("n")
        nextShortcut.activated.connect(self.nextButton.click)

        previousShortcut = QShortcut(self.mainWindow)
        previousShortcut.setKey("p")
        previousShortcut.activated.connect(self.previousButton.click)

    def setupClassificationToolLayout(self,layout):

        self.labelSelectorComboBox = QComboBox()
        self.labelSelectorComboBox.addItem("Select label")
        self.labelSelectorComboBox.addItem("Add new label")

        layout.addWidget(self.labelSelectorComboBox)


    def setupDetectionToolLayout(self, layout):
        self.step1Widget = QWidget()
        self.createStep1Widget()
        self.step2Widget = QWidget()
        self.createStep2Widget()
        self.step3Widget = QWidget()
        self.createStep3Widget()

        layout.addWidget(self.step1Widget)
        layout.addWidget(self.step2Widget)
        layout.addWidget(self.step3Widget)

    def setupSegmentationToolLayout(self,layout):
        self.segmentationLabel = QLabel()
        image = numpy.zeros((240,320,3))
        height, width,channel = image.shape
        bytesPerLine = 3 * width
        qImage = QImage(image.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        pixelmap = QPixmap.fromImage(qImage)
        self.segmentationLabel.setPixmap(pixelmap)
        layout.addWidget(self.segmentationLabel)
        self.blankSegmentationButton = QPushButton("Make blank")
        layout.addWidget(self.blankSegmentationButton)
        self.blankSegmentationButton.clicked.connect(self.onMakeSegmentationBlank)
        self.blankSegmentationButton.setEnabled(False)

    def onMakeSegmentationBlank(self):
        segmentationFileName = self.labelFile[self.labelType][self.currentIndex]
        if "segmentation" in segmentationFileName:
            segImage = cv2.imread(os.path.join(self.imageDirectory,segmentationFileName))
            segImage = segImage[:,:,0]
            newSegImage = numpy.zeros(segImage.shape)
            cv2.imwrite(os.path.join(self.imageDirectory,segmentationFileName),newSegImage)
            self.setSegmentationImage(segmentationFileName)
        else:
            self.setSegmentationImage(None)

    def setSegmentationImage(self,fileName=None):
        if fileName == None:
            image = numpy.zeros((240,320,3))
        else:
            image = cv2.imread(os.path.join(self.imageDirectory,fileName))
            height,width,channel = image.shape
            image = cv2.resize(image,(round(height/2),round(width/2)),interpolation=cv2.INTER_CUBIC)
        height, width,channel = image.shape
        bytesPerLine = 3 * width
        qImage = QImage(image.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        pixelmap = QPixmap.fromImage(qImage)
        self.segmentationLabel.setPixmap(pixelmap)

    def createStep1Widget(self):
        step1Layout = QVBoxLayout()
        self.instructionLabel = QLabel("Step 1: Accept all boxes?")
        self.fliplabelsVButton = QPushButton("Flip boxes vertically")
        self.fliplabelsHButton = QPushButton("Flip boxes horizontally")
        self.swapXandYButton = QPushButton("Swap X and Y coordinates")
        self.acceptDetectionLayout = QHBoxLayout()
        self.acceptButton = QPushButton("Accept All")
        self.rejectButton = QPushButton("Next step")
        self.acceptDetectionLayout.addWidget(self.acceptButton)
        self.acceptDetectionLayout.addWidget(self.rejectButton)
        step1Layout.addWidget(self.instructionLabel)
        step1Layout.addWidget(self.fliplabelsVButton)
        step1Layout.addWidget(self.fliplabelsHButton)
        step1Layout.addWidget(self.swapXandYButton)
        step1Layout.addLayout(self.acceptDetectionLayout)
        self.step1Widget.setLayout(step1Layout)

        #connections
        self.fliplabelsVButton.clicked.connect(self.onFlipLabelsVertically)
        self.fliplabelsHButton.clicked.connect(self.onFlipLabelsHorizontally)
        self.swapXandYButton.clicked.connect(self.onSwapXandYLabels)
        self.acceptButton.clicked.connect(self.onApprovalKeyPressed)
        self.rejectButton.clicked.connect(self.onStep1NextClicked)

    def createStep2Widget(self):
        self.detectionClassCheckBoxLayout = QGridLayout()
        self.step2InstructionsLabel = QLabel("Review individual boxes")
        self.detectionClassCheckBoxLayout.addWidget(self.step2InstructionsLabel, 0, 0, 1, -1)
        self.step2Widget.setLayout(self.detectionClassCheckBoxLayout)
        self.step2Widget.setVisible(False)

    def createStep3Widget(self):
        self.step3Widget.setVisible(False)

    def setupButtonConnections(self):
        self.selectImageDirButton.clicked.connect(self.onSelectImageDirectory)
        self.removeAndRepairButton.clicked.connect(self.onRepairGlitchesClicked)
        self.removeImageButton.clicked.connect(self.onRemoveImageClicked)
        self.flipImageHButton.clicked.connect(self.onFlipImageHClicked)
        self.flipAllHButton.clicked.connect(self.onFlipAllImageHClicked)
        self.flipImageVButton.clicked.connect(self.onFlipImageVClicked)
        self.flipAllVButton.clicked.connect(self.onFlipAllImageVClicked)
        self.saveButton.clicked.connect(self.onSaveButtonClicked)
        self.imageSlider.valueChanged.connect(self.onSliderMoved)
        self.previousButton.clicked.connect(self.showPreviousImage)
        self.nextButton.clicked.connect(self.showNextImage)
        self.labelTypeSelectorComboBox.currentIndexChanged.connect(self.updateLabelSelector)
        self.labelSelectorComboBox.currentIndexChanged.connect(self.updateLabel)
        self.approvalCheckBox.clicked.connect(self.approvalStatusChanged)
        self.selectCleanDirButton.clicked.connect(self.onSelectCleanDirectory)
        self.transferImagesButton.clicked.connect(self.onTransferImagesClicked)

    def onSelectImageDirectory(self):
        window = QWidget()
        window.setWindowTitle("Select Image Directory")
        self.imageDirectory = QFileDialog.getExistingDirectory(window,"C://")
        self.labelTypeSelectorComboBox.setCurrentText("Select label type")
        videoId = os.path.basename(os.path.dirname(self.imageDirectory))
        subtype = os.path.basename(self.imageDirectory)

        if os.path.exists(os.path.join(self.imageDirectory,"{}_{}_Labels.csv".format(videoId,subtype))):
            self.previousButton.setEnabled(True)
            self.nextButton.setEnabled(True)
            self.imageSlider.setEnabled(True)
            self.videoID = videoId
            self.subtype = subtype
            self.labelFile = pandas.read_csv(os.path.join(self.imageDirectory,"{}_{}_Labels.csv".format(videoId,subtype)))
            self.imageSlider.setMinimum(0)
            self.imageSlider.setMaximum(len(self.labelFile.index)-1)
            self.imageDirectoryLabel.setText("Image Directory: \n{}".format(self.imageDirectory))
            self.setImage(self.labelFile["FileName"][0])

            self.currentIndex = 0
            self.updateLabelUI()
            self.getReviewStatus()
        elif os.path.exists(os.path.join(self.imageDirectory,"{}_Labels.csv".format(subtype))):
            self.videoID = subtype
            self.subtype = None
            self.previousButton.setEnabled(True)
            self.nextButton.setEnabled(True)
            self.imageSlider.setEnabled(True)
            self.labelFile = pandas.read_csv(os.path.join(self.imageDirectory, "{}_Labels.csv".format(subtype)))
            self.imageSlider.setMinimum(0)
            self.imageSlider.setMaximum(len(self.labelFile.index)-1)
            self.imageDirectoryLabel.setText("Image Directory: \n\n{}".format(self.imageDirectory))
            self.setImage(self.labelFile["FileName"][0])
            self.currentIndex = 0
            self.updateLabelUI()
            self.getReviewStatus()
        else:
            self.previousButton.setEnabled(False)
            self.nextButton.setEnabled(False)
            self.imageSlider.setEnabled(False)
            self.imageDirectoryLabel.setText("Image Directory: \n\n{}".format("Could not find label file in folder"))
            self.setImage()

    def onSelectCleanDirectory(self):
        window = QWidget()
        window.setWindowTitle("Select Clean Image Directory")
        self.cleanDirectory = QFileDialog.getExistingDirectory(window,"C://")
        self.cleanDirectoryLabel.setText("Clean Image Directory: \n\n{}".format(self.cleanDirectory))

    def onTransferImagesClicked(self):
        try:
            if self.subtype == None:
                labelFileName = "{}/{}_Labels.csv".format(self.videoID,self.videoID)
                videoPath = self.videoID
            else:
                labelFileName = "{}/{}/{}_{}_Labels.csv".format(self.videoID, self.subtype,self.videoID,self.subtype)
                videoPath = os.path.join(self.videoID,self.subtype)
            if not os.path.exists(os.path.join(self.cleanDirectory,self.videoID)):
                os.mkdir(os.path.join(self.cleanDirectory,self.videoID))
            if self.subtype!= None and not os.path.exists(os.path.join(self.cleanDirectory,self.videoID,self.subtype)):
                os.mkdir(os.path.join(self.cleanDirectory,self.videoID,self.subtype))
            if not os.path.exists(os.path.join(self.cleanDirectory,labelFileName)):
                correctedLabelFile = pandas.DataFrame()
                correctedLabelFile["FileName"] = self.labelFile["FileName"]
                correctedLabelFile["Time Recorded"] = self.labelFile["Time Recorded"]
                correctedLabelFile[self.labelType] = self.labelFile[self.labelType]
                correctedLabelFile.to_csv(os.path.join(self.cleanDirectory,labelFileName),index = False)
            else:
                self.existingFile = pandas.read_csv(os.path.join(self.cleanDirectory,labelFileName))
                if len(self.existingFile.index)>= len(self.labelFile.index):
                    self.existingFile[self.labelType] = self.labelFile[self.labelType]
                    self.existingFile.to_csv(os.path.join(self.cleanDirectory,labelFileName),index = False)
                else:
                    self.messageLabel.setText("Mismatched number of images in clean directory")
                    return
            for i in self.labelFile.index:
                try:
                    shutil.copy(os.path.join(self.imageDirectory,self.labelFile["FileName"][i]),
                                os.path.join(self.cleanDirectory,videoPath,self.labelFile["FileName"][i]))
                    if "segmentation" in self.labelFile[self.labelType][i]:
                        shutil.copy(os.path.join(self.imageDirectory, self.labelFile[self.labelType][i]),
                                    os.path.join(self.cleanDirectory, videoPath, self.labelFile[self.labelType][i]))
                except FileNotFoundError:
                    self.messageLabel.setText("Could not find file: {}".format(self.labelFile["FileName"][i]))
            self.messageLabel.setText("Copied images and labels to clean directory")
        except AttributeError:
            self.messageLabel.setText("Must select clean directory location first")


    def getReviewStatus(self):
        currentPath = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(os.path.join(currentPath,"ReviewStatuses")):
            os.mkdir(os.path.join(currentPath,"ReviewStatuses"))
        if self.subtype!=None:
            vidReviewStatusFileName = "{}_{}_reviewStatus.csv".format(self.videoID,self.subtype)
        else:
            vidReviewStatusFileName = "{}_reviewStatus.csv".format(self.videoID)
        self.videoStatusPath = os.path.join(currentPath,"ReviewStatuses",vidReviewStatusFileName)
        if not os.path.exists(self.videoStatusPath):
            self.videoStatus = pandas.DataFrame()
            for col in self.labelFile.columns:
                if col != "FileName" and col != "Time Recorded" and not "Unnamed" in col:
                    self.videoStatus[col] = [False for i in self.labelFile.index]
        else:
            self.videoStatus = pandas.read_csv(self.videoStatusPath)


    def updateLabelUI(self):
        numItems = self.labelTypeSelectorComboBox.count()
        for i in range(numItems-1,0,-1):
            self.labelTypeSelectorComboBox.removeItem(i)
        self.labelTypeSelectorComboBox.addItems([col for col in self.labelFile.columns if col != "FileName" and col != "Time Recorded" and not "Unnamed" in col])

    def updateLabelSelector(self):
        self.labelType = self.labelTypeSelectorComboBox.currentText()
        prevLabels = self.labelSelectorComboBox.count()
        if prevLabels > 2:
            for i in range(prevLabels - 1, 1, -1):
                self.labelSelectorComboBox.removeItem(i)
        if self.labelType != "Select label type":
            if "bounding box" in self.labelType:
                self.labelFile[self.labelType] = [eval(str(self.labelFile[self.labelType][i])) for i in self.labelFile.index]
                self.detectionLabels = self.getClassNames()
                self.createDetectionCheckBoxes()
                self.blankSegmentationButton.setEnabled(False)
            elif "segmentation" in self.labelFile[self.labelType][self.currentIndex]:
                self.blankSegmentationButton.setEnabled(True)
                self.setSegmentationImage(self.labelFile[self.labelType][self.currentIndex])
            else:
                self.blankSegmentationButton.setEnabled(False)
                labels = self.labelFile[self.labelType].unique()
                self.labelSelectorComboBox.addItems(labels)
                self.labelSelectorComboBox.setCurrentText(self.labelFile[self.labelType][self.currentIndex])
            try:
                self.approvalStatus = self.videoStatus[self.labelType][self.currentIndex]
                if self.approvalStatus:
                    self.approvalCheckBox.setChecked(True)
                else:
                    self.approvalCheckBox.setChecked(False)
            except KeyError:
                self.videoStatus[self.labelType] = [False for i in self.videoStatus.index]
                self.approvalStatus = False
                self.approvalCheckBox.setChecked(False)
            self.updateApprovalStatusLabel()

    def getClassNames(self):
        uniqueNames = []
        for i in self.labelFile.index:
            bboxes = self.labelFile[self.labelType][i]
            for bbox in bboxes:
                if not bbox["class"] in uniqueNames:
                    uniqueNames.append(bbox["class"])
        return sorted(uniqueNames)

    def createDetectionCheckBoxes(self):
        self.detectionCheckBoxes = {}
        self.detectionClassCheckBoxLayout.addWidget(QLabel("Present"),1,0)
        self.detectionClassCheckBoxLayout.addWidget(QLabel("Missing"), 1, 1)
        for i in range(len(self.detectionLabels)):
            label = self.detectionLabels[i]
            presentCheckBox = QCheckBox()
            missingCheckBox = QCheckBox()
            classLabel = QLabel(label)
            self.detectionCheckBoxes[label] = [presentCheckBox,missingCheckBox]
            self.detectionClassCheckBoxLayout.addWidget(presentCheckBox,i+2,0)
            self.detectionClassCheckBoxLayout.addWidget(missingCheckBox,i+2,1)
            self.detectionClassCheckBoxLayout.addWidget(classLabel, i + 2, 2)
        self.nextStepButton = QPushButton("Next")
        self.detectionClassCheckBoxLayout.addWidget(self.nextStepButton,len(self.detectionLabels)+2,2,1,2)
        self.nextStepButton.clicked.connect(self.proceedToNextStepButton)

    def onFlipLabelsVertically(self):
        bboxes = self.labelFile[self.labelType][self.currentIndex]
        img = cv2.imread(os.path.join(self.imageDirectory,self.labelFile["FileName"][self.currentIndex]))
        imgHeight = img.shape[0]
        for bbox in bboxes:
            oldYmin = bbox["ymin"]
            oldYmax = bbox["ymax"]
            bbox["ymin"] = imgHeight-oldYmax
            bbox["ymax"] = imgHeight-oldYmin
        self.labelFile[self.labelType][self.currentIndex] = bboxes
        self.updateDetectionLabels()

    def onFlipLabelsHorizontally(self):
        bboxes = self.labelFile[self.labelType][self.currentIndex]
        img = cv2.imread(os.path.join(self.imageDirectory, self.labelFile["FileName"][self.currentIndex]))
        imgWidth = img.shape[1]
        for bbox in bboxes:
            oldXmin = bbox["xmin"]
            oldXmax = bbox["xmax"]
            bbox["xmin"] = imgWidth - oldXmax
            bbox["xmax"] = imgWidth - oldXmin
        self.labelFile[self.labelType][self.currentIndex] = bboxes
        self.updateDetectionLabels()

    def onSwapXandYLabels(self):
        bboxes = self.labelFile[self.labelType][self.currentIndex]
        for bbox in bboxes:
            oldXmin = bbox["xmin"]
            oldXmax = bbox["xmax"]
            oldYmin = bbox["ymin"]
            oldYmax = bbox["ymax"]
            bbox["ymin"] = oldXmin
            bbox["ymax"] = oldXmax
            bbox["xmin"] = oldYmin
            bbox["xmax"] = oldYmax
        self.labelFile[self.labelType][self.currentIndex] = bboxes
        self.updateDetectionLabels()

    def onStep1NextClicked(self):
        self.step1Widget.setVisible(False)
        self.step2Widget.setVisible(True)

    def updateDetectionLabels(self,bboxes):
        pass

    def proceedToNextStepButton(self):
        pass

    def updateLabel(self,indexValue):
        self.labelType = self.labelTypeSelectorComboBox.currentText()
        if self.labelType != "Select label type":
            if indexValue <0:
                try:
                    self.labelSelectorComboBox.setCurrentText(self.labelFile[self.labelType][self.currentIndex])
                except TypeError:
                    self.labelSelectorComboBox.setCurrentText("Bounding box")
                if "segmentation" in self.labelFile[self.labelType][self.currentIndex]:
                    self.setSegmentationImage(self.labelFile[self.labelType][self.currentIndex])
                if type(self.labelFile[self.labelType][self.currentIndex]) == "list":
                    self.updateDetectionLabels(self.labelFile[self.labelType][self.currentIndex])
                self.approvalStatus = self.videoStatus[self.labelType][self.currentIndex]
                if self.approvalStatus:
                    self.approvalCheckBox.setChecked(True)
                else:
                    self.approvalCheckBox.setChecked(False)
            else:
                label =self.labelSelectorComboBox.currentText()
                if label != "Select label" and label!= "Add new label":
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
        self.videoStatus.to_csv(self.videoStatusPath,index=False)
        self.updateApprovalStatusLabel()

    def updateApprovalStatusLabel(self):
        approvalCounts = self.videoStatus[self.labelType].value_counts()
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

    def setImage(self,fileName=None):
        if fileName == None:
            image = numpy.zeros((480, 640, 3))
            height, width, channel = image.shape
            bytesPerLine = 3 * width
            qImage = QImage(image.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
            pixelmap = QPixmap.fromImage(qImage)
        else:
            pixelmap = QPixmap(os.path.join(self.imageDirectory,fileName))
        self.imageLabel.setPixmap(pixelmap)

    def onSliderMoved(self):
        self.currentIndex = self.imageSlider.value()
        if self.currentIndex == 0:
            self.previousButton.setEnabled(False)
            self.nextButton.setEnabled(True)
        elif self.currentIndex == self.imageSlider.maximum():
            self.nextButton.setEnabled(False)
            self.previousButton.setEnabled(True)
        self.setImage(self.labelFile["FileName"][self.currentIndex])
        self.updateLabel(indexValue=-1)

    def showPreviousImage(self):
        self.nextButton.setEnabled(True)
        if self.currentIndex > 0:
            self.currentIndex -=1
        if self.currentIndex == 0:
            self.previousButton.setEnabled(False)
        self.imageSlider.setValue(self.currentIndex)
        self.setImage(self.labelFile["FileName"][self.currentIndex])
        self.updateLabel(indexValue=-1)

    def showNextImage(self):
        self.previousButton.setEnabled(True)
        if self.currentIndex <len(self.labelFile.index)-1:
            self.currentIndex +=1
        if self.currentIndex == len(self.labelFile.index)-1:
            self.nextButton.setEnabled(False)
        self.imageSlider.setValue(self.currentIndex)
        self.setImage(self.labelFile["FileName"][self.currentIndex])
        self.updateLabel(indexValue=-1)

    def onSaveButtonClicked(self):
        if self.subtype == None:
            self.labelFile.to_csv(os.path.join(self.imageDirectory,"{}_Labels.csv".format(self.videoID)),index=False)
        else:
            self.labelFile.to_csv(os.path.join(self.imageDirectory, "{}_{}_Labels.csv".format(self.videoID,self.subtype)),index=False)
        self.videoStatus.to_csv(self.videoStatusPath, index=False)
        self.messageLabel.setText("Changes saved")

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
        self.videoStatus.index = [i for i in range(len(self.videoStatus.index))]
        self.messageLabel.setText("Removed {} glitched frames".format(len(indexesToRemove)))
        self.imageSlider.setMaximum(len(self.labelFile.index))

    def onRemoveImageClicked(self):
        rowToDrop = self.currentIndex
        self.labelFile = self.labelFile.drop(rowToDrop)
        self.videoStatus = self.videoStatus.drop(rowToDrop)
        self.labelFile.index = [i for i in range(len(self.labelFile.index))]
        self.videoStatus.index = [i for i in range(len(self.videoStatus.index))]
        if self.currentIndex > self.labelFile.index[-1]:
            self.currentIndex = self.labelFile.index[-1]
        self.setImage(self.labelFile["FileName"][self.currentIndex])
        self.messageLabel.setText("Image Removed")
        #self.imageSlider.setMaximum(len(self.labelFile.index))

    def onFlipImageHClicked(self):
        imagePath = os.path.join(self.imageDirectory,self.labelFile["FileName"][self.currentIndex])
        image = cv2.imread(imagePath)
        image = cv2.flip(image,1)
        cv2.imwrite(imagePath,image)
        #self.setImage(self.labelFile["FileName"][self.currentIndex])

    def onFlipAllImageHClicked(self):
        for i in self.labelFile.index:
            imagePath = os.path.join(self.imageDirectory,self.labelFile["FileName"][i])
            image = cv2.imread(imagePath)
            image = cv2.flip(image, 1)
            cv2.imwrite(imagePath,image)
        self.setImage(self.labelFile["FileName"][self.currentIndex])

    def onFlipImageVClicked(self):
        imagePath = os.path.join(self.imageDirectory,self.labelFile["FileName"][self.currentIndex])
        image = cv2.imread(imagePath)
        image = cv2.flip(image, 0)
        cv2.imwrite(imagePath,image)
        self.setImage(self.labelFile["FileName"][self.currentIndex])

    def onFlipAllImageVClicked(self):
        for i in self.labelFile.index:
            imagePath = os.path.join(self.imageDirectory, self.labelFile["FileName"][i])
            image = cv2.imread(imagePath)
            image = cv2.flip(image, 0)
            cv2.imwrite(imagePath,image)
        self.setImage(self.labelFile["FileName"][self.currentIndex])

    def main(self):
        app = QApplication([])
        window = QWidget()
        window.setWindowTitle("Annotation Reviewer")
        window.setGeometry(500,200,1250,500)
        self.addWidgetsToWindow(window)
        self.setupButtonConnections()
        window.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    app = AnnotationReviewer()
    app.main()
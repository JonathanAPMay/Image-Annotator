#import libraries
import tkinter
from tkinter.filedialog import askopenfilename
from PIL import ImageTk, Image
from pycocotools.coco import COCO
import cv2
import numpy as np
from imantics import BBox, Image as img, Mask, Category, Polygons

#Window set up
window = tkinter.Tk()
window.title("Image Annotator")

#set up scrollbars
yScrollbar = tkinter.Scrollbar(window)
yScrollbar.pack( side = "right", fill = "y" )
xScrollbar = tkinter.Scrollbar(window, orient = "horizontal")
xScrollbar.pack( side = "bottom", fill = "y")

#Annotation creation variables
CoordCount = 0
xClick = 0
yClick = 0
xClick2 = 0
yClick2 = 0
separatePolygons = 0
bBoxCoords = []
bBoxLabels = []
polygonCoords = []
polygonLabels = []

#Set bbox colour default
lineColour = "Black"
#Set tool default
currentTool = "Bounding Box"

#set up canvas
tempImage = ImageTk.PhotoImage(Image.open("tempImage.png"))
canvas = tkinter.Canvas(window, width = tempImage.width(), height = tempImage.height(), xscrollcommand = xScrollbar.set, yscrollcommand = yScrollbar.set)
canvas.update_idletasks()

#config scrollbars to canvas
yScrollbar.config(command = canvas.yview)
xScrollbar.config(command = canvas.xview)

#show template image
imageView = canvas.create_image(0,0,anchor = "nw",image = tempImage, tags = "image")
canvas.pack(fill = "both",expand = "yes")

#Pop up window when saving an annotaation with no CNN input
def noCNNMaskPopUpWindow():
   popUp = tkinter.Toplevel(window)
   popUp.geometry("250x100")
   label = tkinter.Label(popUp, text="There is no mask created\nfrom the machine model.\nOnly saving user bounding boxes.")
   label.pack()
   button = tkinter.Button(popUp, text = "Ok", command = lambda:closeTopWindow(popUp))
   button.pack(pady=5, side="bottom")

#Pop up window when saving
def annotationSavePopUpWindow(location):
   popUp = tkinter.Toplevel(window)
   popUp.geometry("250x75")
   label = tkinter.Label(popUp, text="Annotations saved to:\n./" + location)
   label.pack()
   button = tkinter.Button(popUp, text = "Ok", command = lambda:closeTopWindow(popUp))
   button.pack(pady=5, side="bottom")
   
#close popUpWindow
def closeTopWindow(top):
   top.destroy()
   
#close popUpWindow
def closeMultipleTopWindows(top, top2):
   top.destroy()
   top2.destroy()
   
#close specifically the annotation window and place the label onto the canvas for polygons
def closePolygonAnnotationWindow(top, userInput):
    global separatePolygons
    top.destroy()
    polygonLabels.append(userInput)
    leftmostX = polygonCoords[separatePolygons][0]
    rightmostX = polygonCoords[separatePolygons][0]
    highestY = polygonCoords[separatePolygons][1]
    lowestY = polygonCoords[separatePolygons][1]
    for i in range(separatePolygons, (separatePolygons + len(polygonCoords[separatePolygons:]))):
        if polygonCoords[i][0] < leftmostX:
            leftmostX = polygonCoords[i][0]
        if polygonCoords[i][0] > rightmostX:
            rightmostX = polygonCoords[i][0]
        if polygonCoords[i][1] < highestY:
            highestY = polygonCoords[i][1]
        if polygonCoords[i][1] > lowestY:
            lowestY = polygonCoords[i][1]
    separatePolygons = len(polygonCoords)
    canvas.create_text(((leftmostX + (rightmostX - leftmostX)/2)), ((highestY + (lowestY - highestY)/2)), tag = "annotations", text = userInput, fill="black")
    

#close specifically the annotation window and place the label onto the canvas for bboxes
def closeAnnotationWindow(top, userInput):
    top.destroy()
    bBoxLabels.append(userInput)
    canvas.create_text(((xClick + (xClick2 - xClick)/2)), ((yClick + (yClick2 - yClick)/2)), tag = "annotations", text = userInput, fill="black")
   
#failed new image
def imageFailPopUpWindow():
    #Create a Toplevel window
    popUp = tkinter.Toplevel(window)
    popUp.geometry("250x75")
    label = tkinter.Label(popUp, text="Opening an image failed.")
    label.pack()
    button = tkinter.Button(popUp, text = "Ok", command = lambda:closeTopWindow(popUp))
    button.pack(pady = 5, side="bottom")

#failed creating a mask new image
def imageOrCNNFailPopUpWindow():
    #Create a Toplevel window
    popUp = tkinter.Toplevel(window)
    popUp.geometry("400x75")
    label = tkinter.Label(popUp, text="Opening an image or detection of any objects in the image failed.")
    label.pack()
    button = tkinter.Button(popUp, text = "Ok", command = lambda:closeTopWindow(popUp))
    button.pack(pady = 5, side="bottom")
   
#delete the most recent bounding box if it wasn't given a label
def deleteUnlabeledRectPopUpWindow(top):
    #Create a Toplevel window
    popUp = tkinter.Toplevel(window)
    popUp.geometry("400x75")
    label = tkinter.Label(popUp, text="Cancelled labelling, deleting bounding box.")
    mostRecent = canvas.find_withtag("box")[-1]
    if mostRecent:
        canvas.delete(mostRecent)
    label.pack()
    button = tkinter.Button(popUp, text = "Ok", command = lambda:closeMultipleTopWindows(popUp, top))
    button.pack(pady = 5, side="bottom")
    popUp.protocol("WM_DELETE_WINDOW", lambda:closeMultipleTopWindows(popUp, top))
   
#delete the most recent bounding box if it wasn't given a label
def deleteUnlabeledPolygonPopUpWindow(top):
    #Create a Toplevel window
    popUp = tkinter.Toplevel(window)
    popUp.geometry("400x75")
    label = tkinter.Label(popUp, text="Cancelled labelling, deleting polygon.")
    mostRecent = canvas.find_withtag("polygon")[-1]
    if mostRecent:
        canvas.delete(mostRecent)
    label.pack()
    del polygonCoords[separatePolygons:]
    button = tkinter.Button(popUp, text = "Ok", command = lambda:closeMultipleTopWindows(popUp, top))
    button.pack(pady = 5, side="bottom")
    popUp.protocol("WM_DELETE_WINDOW", lambda:closeMultipleTopWindows(popUp, top))
   
#Annotation window
def annotationPopUpWindow():
    #Create a Toplevel window
    global inputAnnotation
    global currentTool
    popUp = tkinter.Toplevel()
    popUp.geometry("250x75")
    label = tkinter.Label(popUp, text="Input the item's name:")
    inputAnnotation = tkinter.Entry(popUp)
    inputAnnotation.pack()
    label.pack()
    popUp.focus_force()
    if currentTool == "Bounding Box":
        button = tkinter.Button(popUp, text = "Confirm", command = lambda:closeAnnotationWindow(popUp, inputAnnotation.get()))
        button.pack(pady=5, side="bottom")
        popUp.protocol("WM_DELETE_WINDOW", lambda:deleteUnlabeledRectPopUpWindow(popUp))
    elif currentTool == "Polygon":
        button = tkinter.Button(popUp, text = "Confirm", command = lambda:closePolygonAnnotationWindow(popUp, inputAnnotation.get()))
        button.pack(pady=5, side="bottom")
        popUp.protocol("WM_DELETE_WINDOW", lambda:deleteUnlabeledPolygonPopUpWindow(popUp))

#Pop up stating that no saving occurs if no file has been loaded
def noFileToSavePopUpWindow():
    popUp = tkinter.Toplevel(window)
    popUp.geometry("250x100")
    label = tkinter.Label(popUp, text="No file is loaded, no saving has occurred.")
    label.pack()
    button = tkinter.Button(popUp, text = "Ok", command = lambda:closeTopWindow(popUp))
    button.pack(pady=5, side="bottom")
    
#Open an image already annotated
def openDatasetFile():
    global bBoxCoords
    global bBoxLabels
    global polygonCoords
    global polygonLabels
    global file
    global forTkinterImage
    #global saveMask
    global coco
    file = askopenfilename()
    #saveMask = "NULL"
    try:
        askedImage = Image.open(file)
        askedImage = imageAbove1080p(askedImage)
        #check if it is a dataset file that the user created and load annotations
        canvas.delete("box")
        bBoxCoords = []
        canvas.delete("annotations")
        bBoxLabels = []
        canvas.delete("polygon")
        polygonCoords = []
        polygonLabels = []
        datasetFile = file.split("/")
        datasetFileName, datasetFileIdFormat = datasetFile[-1].split(".")
        annotationFile = "./coco/annotation %s.json" % (datasetFileName,)
        coco = COCO(annotationFile)
        idNum = 1
        attemptLoadAnn = True
        while attemptLoadAnn:
            try:
                annotation = coco.loadAnns(idNum)
                shape = annotation[0]["segmentation"]
                if len(shape[0]) == 8:
                    x = annotation[0]["bbox"][0]
                    y = annotation[0]["bbox"][1]
                    x2 = annotation[0]["bbox"][0] + annotation[0]["bbox"][2]
                    y2= annotation[0]["bbox"][1] + annotation[0]["bbox"][3]
                    canvas.create_rectangle(x, y, x2, y2, tags = "box", outline = lineColour)
                    bBoxCoords.append([x, y, x2, y2])
                    bBoxLabels.append(getAnnotationLabel(annotation))
                else:
                    canvas.create_line(shape, tags = "polygon", fill = lineColour)
                    for i in range(len(shape)):
                        polygonCoords.append(shape[i])
                    polygonLabels.append(getAnnotationLabel(annotation))
                box = annotation[0]["bbox"]
                canvas.create_text((box[0] + box[2]/2), (box[1] + box[3]/2), tag = "annotations", text = getAnnotationLabel(annotation), fill = "red")
                idNum += 1
            except:
               attemptLoadAnn = False
        forTkinterImage = ImageTk.PhotoImage(askedImage)
        canvas.itemconfig(imageView, image = forTkinterImage)
        yScrollbar.config(command = canvas.yview)
        xScrollbar.config(command = canvas.xview)
    except:
        imageFailPopUpWindow()

def getAnnotationLabel(ann):
    labelId = ann[0]["category_id"]
    label = coco.loadCats(labelId)[0]["name"]
    return label

#run a pretrained machine learning model to guess what is on the image, marking areas as regions of interest, no labels loaded currently
def runMaskCRNN():
    global file
    #global saveMask
    global autoImage
    global askedImage
    global bBoxCoords
    global bBoxLabels
    global polygonCoords
    global polygonLabels
    file = askopenfilename()
    try:
        askedImage = Image.open(file)
        canvas.delete("box")
        bBoxCoords = []
        canvas.delete("annotations")
        bBoxLabels = []
        canvas.delete("polygon")
        polygonCoords = []
        polygonLabels = []
        askedImage = imageAbove1080p(askedImage)
        cv2Image = cv2.cvtColor(np.array(askedImage), cv2.COLOR_RGB2BGR)
        graphPath = "frozen_inference_graph_coco.pb"
        modelPath = "mask_rcnn_inception_v2_coco_2018_01_28.pbtxt"
        net = cv2.dnn.readNetFromTensorflow(graphPath, modelPath)
        colors = np.random.randint(125, 255, (100, 3))
        height, width, _ = cv2Image.shape
        blackImageArray = np.zeros((height, width, 3), np.uint8)
        blackImageArray[:] = (0, 0, 0)
        blob = cv2.dnn.blobFromImage(cv2Image, swapRB=True)
        net.setInput(blob)
        boxes, masks = net.forward(["detection_out_final", "detection_masks"])
        detectionCount = boxes.shape[2]
        for i in range(detectionCount):
            box = boxes[0, 0, i]
            classId = box[1]
            score = box[2]
            if score < 0.5:
                 continue
            x = int(box[3] * width)
            y = int(box[4] * height)
            x2 = int(box[5] * width)
            y2 = int(box[6] * height)
            roi = blackImageArray[y: y2, x: x2]
            roiHeight, roiWidth, _ = roi.shape
            canvas.create_text((x2 - (x2/10)), (y2 - (y2/8)), tag = "annotations", text = str(i), fill="black")
            mask = masks[i, int(classId)]
            mask = cv2.resize(mask, (roiWidth, roiHeight))
            _, mask = cv2.threshold(mask, 0.5, 255, cv2.THRESH_BINARY)
            #saveMask = mask
            contours, _ = cv2.findContours(np.array(mask, np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            color = colors[int(classId)]
            for cnt in contours:
                cv2.fillPoly(roi, [cnt], (int(color[0]), int(color[1]), int(color[2])))
        blackImagePIL = Image.fromarray(blackImageArray)
        blendedImage = Image.blend(askedImage, blackImagePIL, 0.6)
        autoImage = ImageTk.PhotoImage(blendedImage)
        canvas.itemconfig(imageView, image = autoImage)
        noAutoLabelWarningPopUpWindow()
    except:
        imageOrCNNFailPopUpWindow()

#Warning indicating that labels aren't created when running the machine learning model
def noAutoLabelWarningPopUpWindow():
    popUp = tkinter.Toplevel(window)
    popUp.geometry("500x110")
    popUp.focus_force()
    label = tkinter.Label(popUp, text="WARNING: Labels aren't generated with the machine learning model currently.\nPlease draw a bounding box on any regions and label accordingly,\nNumber labels are placed as well as possible to see which regions were highlighted first.\nThis mask is not saved and only serves to find objects to annotate.")
    label.pack()
    button = tkinter.Button(popUp, text = "Ok", command = lambda:closeTopWindow(popUp))
    button.pack(pady=5, side="bottom")
    
#Just a notification stating that the user has not inputted to the image and thus will only save
def noUserInputPopUpWindow():
    popUp = tkinter.Toplevel(window)
    popUp.geometry("250x100")
    label = tkinter.Label(popUp, text="There are no bounding boxes\ncreated by the user.\nOnly saving machine model mask.")
    label.pack()
    button = tkinter.Button(popUp, text = "Ok", command = lambda:closeTopWindow(popUp))
    button.pack(pady=5, side="bottom")

#Pop up stating that no saving occurs if no file has been loaded
def doNotSavePopUpWindow():
    popUp = tkinter.Toplevel(window)
    popUp.geometry("350x50")
    label = tkinter.Label(popUp, text="You cannot save when viewing an already annotated image.")
    label.pack()
    button = tkinter.Button(popUp, text = "Ok", command = lambda:closeTopWindow(popUp))
    button.pack(pady=5, side="bottom")

 #Saving annotations on image to file
def saveCOCOFormat():
    global file
    splitFile = file.split("/")
    fileName, _ = splitFile[-1].split(".")
    image = img.from_path(file)
    showBboxPopUpOnce = True
    #showMaskPopUpOnce = True
    for i in range(len(bBoxLabels)):
        try:
            bbox = BBox(bBoxCoords[i])
            image.add(bbox, category = Category(bBoxLabels[i]))
        except:
            if showBboxPopUpOnce:
                noUserInputPopUpWindow()
                showBboxPopUpOnce = False
        """try:
            CNNMask = cv2.resize(saveMask, (image.width, image.height))
            CNNMask = Mask(CNNMask)
            image.add(CNNMask, category = Category(bBoxLabels[i]))
        except:
            if showMaskPopUpOnce:
                noCNNMaskPopUpWindow()
                showMaskPopUpOnce = False"""
    polygons = polygonCoords
    polygonIndexCount = 1
    labelIndexCount = 0
    while polygons:
        if polygons[0] == polygons[polygonIndexCount]:
            polygon = Polygons(polygons[0:polygonIndexCount+1])
            image.add(polygon, category = Category(polygonLabels[labelIndexCount]))
            del polygons[0:polygonIndexCount+1]
            labelIndexCount += 1
            polygonIndexCount = 1
        else:
            polygonIndexCount += 1
    cocoimage = image.export(style = "coco")
    saveLoc = "coco/annotation %s.json" % (fileName,)
    image.save(saveLoc, style = "coco")
    annotationSavePopUpWindow(saveLoc)

def imageAbove1080p(chosenImage):
    if chosenImage.height > 1080:
        proportionY = (chosenImage.height / 1080)
        resizedX = int (chosenImage.width / proportionY)
        resizedY = int (chosenImage.height / proportionY)
        ImageResize = (resizedX, resizedY)
        resizedImage = chosenImage.resize(ImageResize)
    elif chosenImage.width > 1920:
        proportionX = (chosenImage.width / 1920)
        resizedX = int (chosenImage.width / proportionX)
        resizedY = int (chosenImage.height / proportionX)
        ImageResize = (resizedX, resizedY)
        resizedImage = chosenImage.resize(ImageResize)
    else:
        resizedImage = chosenImage
    return resizedImage
    
#Open a new image
def openFile():
    global file
    global adjustedImage
    #global saveMask
    global bBoxCoords
    global bBoxLabels
    global polygonCoords
    global polygonLabels
    file = askopenfilename()
    #saveMask = "NULL"
    try:
        askedImage = Image.open(file)
        canvas.delete("box")
        bBoxCoords = []
        canvas.delete("annotations")
        bBoxLabels = []
        canvas.delete("polygon")
        polygonCoords = []
        polygonLabels = []
        adjustedImage = ImageTk.PhotoImage(imageAbove1080p(askedImage))
        canvas.itemconfig(imageView, image = adjustedImage)
        yScrollbar.config(command = canvas.yview)
        xScrollbar.config(command = canvas.xview)
    except:
        imageFailPopUpWindow()
    
#Menu set up
mn = tkinter.Menu(window) 
window.config(menu = mn)

#Get bbox colour menu choice 
def colour(menu, indexVal):
    global lineColour
    if (1 <= indexVal <= 4):
        lineColour = menu.entrycget(indexVal, "label")

def tool(menu, indexVal):
    global currentTool
    if (1 <= indexVal <= 2):
        currentTool = menu.entrycget(indexVal, "label")
        
#File menu set up
fileMenu = tkinter.Menu(mn) 
mn.add_cascade(label = "File", menu = fileMenu) 
fileMenu.add_command(label = "New Image", command = openFile) 
fileMenu.add_command(label = "View Annotated Image", command = openDatasetFile)
fileMenu.add_command(label = "Attempt Automatic Segmentation on New Image", command = runMaskCRNN)
fileMenu.add_command(label = "Save", command = saveCOCOFormat) 
fileMenu.add_command(label = "Exit", command = window.quit) 
#Bbox menu set up
bboxMenu = tkinter.Menu(mn) 
mn.add_cascade(label = "Line Colours", menu = bboxMenu)
bboxMenu.add_command(label = "Black", command = lambda:colour(bboxMenu, 1)) 
bboxMenu.add_command(label = "Blue", command = lambda:colour(bboxMenu, 2)) 
bboxMenu.add_command(label = "Red", command = lambda:colour(bboxMenu, 3)) 
bboxMenu.add_command(label = "Green", command = lambda:colour(bboxMenu, 4))
#Different tools menu set up
toolMenu = tkinter.Menu(mn) 
mn.add_cascade(label = "Drawing Tools", menu = toolMenu)
toolMenu.add_command(label = "Bounding Box", command = lambda:tool(toolMenu, 1))
toolMenu.add_command(label = "Polygon", command = lambda:tool(toolMenu, 2))

#Bbox coordinates
def clickHandler(event):
    global xClick
    global yClick
    global xClick2
    global yClick2
    global CoordCount
    global currentTool
    x, y = event.x, event.y
    CoordCount += 1
    if currentTool == "Bounding Box":
        if CoordCount == 1:
            xClick = x
            yClick = y
        if CoordCount > 1:
            xClick2 = x
            yClick2 = y
            if xClick > x:
                if yClick > y:
                    bBoxCoords.append([x, y, xClick, yClick])
                else:
                    bBoxCoords.append([x, yClick, xClick, y])
            elif yClick > y:
                bBoxCoords.append([xClick, y, x, yClick])
            else:
                bBoxCoords.append([xClick, yClick, x, y])
            canvas.create_rectangle(xClick, yClick, x, y, tags = "box", outline = lineColour)
            CoordCount = 0
            annotationPopUpWindow()
    elif currentTool == "Polygon":
        if CoordCount == 1:
            xClick = x
            yClick = y
        elif CoordCount > 1:
            xClick2 = x
            yClick2 = y
            if [xClick, yClick] in polygonCoords:
                pass
            else:
                polygonCoords.append([xClick, yClick])
            polygonCoords.append([x, y])
            canvas.create_line(xClick, yClick, x, y, tags = "line", fill = lineColour)
            xClick = xClick2
            yClick = yClick2
            CoordCount = 1
        
def motionHandler(event):
    global xClick
    global yClick
    global CoordCount
    global currentTool
    x, y = event.x, event.y
    if currentTool == "Bounding Box":
        if CoordCount == 1:
            canvas.delete("temp")
            canvas.create_rectangle(xClick, yClick, x, y, tags = "temp", outline = lineColour)
        else:
            canvas.delete("temp")
    elif currentTool == "Polygon":
        if CoordCount == 1:
            canvas.delete("temp")
            canvas.create_line(xClick, yClick, x, y, tags = "temp", fill = lineColour)
        else:
            canvas.delete("temp")
        
def rightClickHandler(event):
    global CoordCount
    global currentTool
    global separatePolygons
    if currentTool == "Bounding Box":
        CoordCount = 0
    elif currentTool == "Polygon":
        if not polygonCoords:
            CoordCount = 0
        else:
            try:
                if polygonCoords[-1] == polygonCoords[separatePolygons]:
                    pass
                else:
                    polygonCoords.append(polygonCoords[separatePolygons])
                canvas.create_line(polygonCoords[separatePolygons:], tags = "polygon", fill = lineColour)
                annotationPopUpWindow()
                canvas.delete("line")
                CoordCount = 0
            except:
                pass
            
canvas.bind("<Button-3>", rightClickHandler)        
canvas.bind("<Button>", clickHandler)
canvas.bind("<Motion>", motionHandler)
                 
window.mainloop()
import maya.cmds as cmds
import maya.app.general.positionAlongCurve as pos
import math as m
import re
from functools import wraps

'''   
    -------------------------------------------------
    this tool creates an automatic hand rig
    using 2 methods:
    
    method 1:
    users specify the positions of control vertices
    and the rig joints will created along those 
    control points.
    
    method 2:
    users paint the faces of the main fingers tips
    and palm of hands, the algorithm will interpolate
    positions between these hand positions and create 
    a general hand rig.  
    --------------------------------------------------
'''

#-------------------------ERROR HANDLING-----------------------
def RuntimeErrorDecorator(fn):
    '''
       debugs RuntimeErrors.
    '''
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (RuntimeError):
            print( 'window already exists with this name' )
    return wrapper

def componentErrorDecorator(fn):
    '''
        debugs component type RuntimeErrors.
    '''
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            object = cmds.ls(sl=True, fl=True)
            component = re.search('(?<=\.)(.*?)(?=\[)', object[0]).group(0)
            if component!='':
                return fn(*args, **kwargs)
            else:
                print( 'Incorrect component type. Please select mesh components.' )              
        except (TypeError, IndexError):
            print( 'Incorrect geometry type. Please select object component' )
    return wrapper   

def isObjectSelected():
    '''
        detects whether any object exists in scene and is currenly selected.
        If such an object/objects exist in scene, return boolean statement.
    '''
    geometry = cmds.ls(geometry=True)
    if len(geometry)>0:
        selectedObjs = cmds.ls(selection=True)
        if len(selectedObjs)>0:
            return True            
        else:
            return False
    else:
        return False
        
class curveCVcontrols:
    
    def __init__(self):
        self.isCurve = False

    def doesCurveExist(self):
        '''
            queries if a curve transform node exists in the scene.
        '''
        allObjects = cmds.ls()
        for i in allObjects:
            try:
                objectTransform = cmds.listRelatives(i, children=True)
                objectType = cmds.ls(objectTransform, showType=True)
                if len(objectType)>1:
                    if objectType[1] == 'nurbsCurve':
                        self.isCurve = True
            except ValueError:
                pass
        return self.isCurve

    def createDrawjoints(self, **kwargs):
        '''
            creates the joints based on drawn control vertices.
        '''
        curveExists = self.doesCurveExist()

        if not curveExists:
            print('No curve exists in scene. Please create a curve to continue.')
            return 

        type = cmds.ls(showType=True)
        spheres, curves = [], []
        for i in range(len(type)):
            if type[i]=='nurbsCurve':
                curveShape = type[i-1]
                curveTransform = cmds.pickWalk(curveShape, direction='up')
                curves.append(curveTransform)

        for i in range(len(curves)):
            for j in range(kwargs['number_carpals']):
                cmds.sphere(r=0.3)

        newType = cmds.ls(showType=True)
        for i in range(len(newType)):
            if newType[i]=='makeNurbSphere':
                geometry = newType[i+1]
                spheres.append(geometry)
        
        #place a sphere along the curve.
        iterator, sphereCount = 0, kwargs['number_carpals']
        cmds.jointDisplayScale(0.1)
        for i in range(len(curves)):
            cmds.select(curves[i], add=True)
            for j in range(iterator, sphereCount):
                cmds.select(spheres[j], add=True)

            pos.positionAlongCurve()

            for k in cmds.ls(sl=True):
                cmds.select(k, d=True)

            iterator += kwargs['number_carpals']
            sphereCount += kwargs['number_carpals']

        #iterate over each sphere position and place a joint
        iterator, sphereCount = 0, kwargs['number_carpals']
        for i in range(len(curves)):
            for j in range(iterator, sphereCount):
                translation = cmds.getAttr('{}.translate'.format(spheres[j]))[0]
                cmds.joint(n='joint_' + str(j), p=translation)

            for k in cmds.ls(sl=True):
                cmds.select(k, d=True)

            iterator += kwargs['number_carpals']
            sphereCount += kwargs['number_carpals']

        for i in range(len(spheres)): cmds.delete(spheres[i])
        for j in range(len(curves)): cmds.delete(curves[j])

        self.isCurve = False

    def deleteAllCurves(self, *args):
        '''
            deletes all curves in current scene.
        '''
        allObjects = cmds.ls()
        for i in allObjects:
            try:
                objectTransform = cmds.listRelatives(i, children=True)
                objectType = cmds.ls(objectTransform, showType=True)
                if len(objectType)>1:
                    if objectType[1] == 'nurbsCurve':
                        cmds.delete(i)
                else:
                    pass  
            except ValueError:
                pass
        
class paintHandControls:
    
    def getAverageComponentPos(self, objects):
        '''
                gets the average position of selected components.
        ''' 
        objectsConverted = [cmds.polyListComponentConversion(i, tv=True) for i in objects]
        newList = []
        for i in objectsConverted:
            for j in i:
                newList.append(j)
        noDups = cmds.ls(newList, fl=True)       
        findPositions = [ cmds.pointPosition(i) for i in noDups]
        xPos, yPos, zPos = [i[0] for i in findPositions],[i[1] for i in findPositions], [i[2] for i in findPositions]
        xFinal, yFinal, zFinal = sum(xPos)/len(findPositions), sum(yPos)/len(findPositions), sum(zPos)/len(findPositions)
        return xFinal, yFinal, zFinal 
    
    def createJoints(self, **kwargs):
        '''
            interpolate carpal joint positions based off knuckle and finger tip positions.
        '''
        cmds.jointDisplayScale( 0.1 )
        cmds.joint(n='base_Joint', p=kwargs['baseJoint'])

        for numFingers in range(5):

            squaredSum = [(kwargs['fingerTipPositions']['joint_' + str(numFingers)][i] - 
                            kwargs['knucklePositions']['knuckle_' + str(numFingers)][i])**2 for i in range(3) ]
            magnitude = m.sqrt(squaredSum[0] + squaredSum[1] + squaredSum[2])
            normalized = [(kwargs['fingerTipPositions']['joint_' + str(numFingers)][i] - 
                            kwargs['knucklePositions']['knuckle_' + str(numFingers)][i])/magnitude 
                                    for i in range(3)]   
            #finds the normalized positions of interpolated carpals.         
            
            cmds.joint(n='knuckle_' + str(numFingers), p=kwargs['knucklePositions']['knuckle_' + str(numFingers)])                
            
            if cmds.currentCtx(q=True)!='selectSuperContext':
                cmds.connectJoint('knuckle_' + str(numFingers), 'base_Joint', pm=True)
            #creates finger and knuckle joints
                        
            for k in range(1,kwargs['carpalNum']-1):                                 
                thirdPosition = [ kwargs['knucklePositions']['knuckle_' + str(numFingers)][i] + 
                                    normalized[i]*k*magnitude/kwargs['carpalNum'] for i in range(3)]
                cmds.joint(n='finger_' + str(numFingers) + '_carpal_' + str(k), p=thirdPosition)                
                
                if cmds.currentCtx(q=True)!='selectSuperContext':
                    cmds.connectJoint('finger_' + str(numFingers) + '_carpal_' + str(k), 'knuckle_' + str(numFingers), pm=True)
            
            cmds.joint(n='finger_' + str(numFingers), p=kwargs['fingerTipPositions']['joint_' + str(numFingers)])
            
            if cmds.currentCtx(q=True)!='selectSuperContext':
                cmds.connectJoint('finger_' + str(numFingers), 'knuckle_' + str(numFingers), pm=True)

            cmds.pickWalk('finger_' + str(numFingers), direction='up')
            cmds.pickWalk('knuckle_' + str(numFingers), direction='up')
        
    def undoSelection(self, *args):
        '''
            when the undo selection button is pressed by the user.
        '''
        cmds.undo()          
    
    def deleteAllJoints(self, *args):
        '''
            delete all joints if they exist in current scene.
        '''
        allObjects = cmds.ls()
        for i in allObjects:
            try:
                objectTransform = cmds.listRelatives(i, children=True)
                objectType = cmds.ls(objectTransform, showType=True)
                if len(objectType)>1:
                    if objectType[1] == 'joint':
                        cmds.delete(i)
                else:
                    pass  
            except ValueError:
                pass

class ctxControl:

    title = 'brushWindow'
    widthHeight = (500,150)
    brushWidgets = [None, None, None, None, None, None, None, None, None]
    ctxNames = ['curveDrawCtx2', 'curveCVctx1', 'artSelectCtx1']   
    ctxDetection = [False, False, False]
    currentCtx, position = None, None
    defaultNumCarpals = 5
    changed = False

    message='''
    About:
    ----------------------------------------------------
    This tool allows users to edit brush contexts and 
    select/or alter the state of mesh components.

    CURVE TOOLS:    
    -Whenever the curve draw tools are used the 'Number 
     of Joints' slider controls the number of joints 
     placed along that curve.
    -If multiple curves are selected, this tool will 
     position the specified number of joints along each 
     curve
    -The placement of joints along the curve are based 
     upon the direction to which the user originally 
     placed the curve i.e if the user wanted joints to 
     run up the finger, they should draw the curve from
     bottom up.
    -The user can optionally control the degree value of 
     the curve by using the degree slider within this 
     window. This changes the degree of the curve drawn 
     by creating more control points along the curve.

    PAINT HAND TOOLS:
    -This tool is controlled by the multiple checkboxes 
     within this window; each of which can alter the 
     state of selection using the brush context.
    -For general use, the replace radio button should be 
     used to determine the location of individual joints 
     along the hand.
    -This tool can be used to select face and vertex 
     component types from the selected mesh. 
    ----------------------------------------------------
    '''

    def __init__(self):
        self.brushWin = None   
        self.numCarpals = None
        self.startValue = None
        self._queryDirectory = None

    @property
    def queryDirectory(self):
        return self._queryDirectory

    @queryDirectory.setter
    def set_queryDirectory(self, value):
        self._queryDirectory = value

    def runAssociatedCtx(ctxName, *args):
        '''
            Updates the current context to the actively
            selected context.
        '''     
        def ctxDecorator(fn):
            @wraps(fn)
            def ctxWrapper(self, *args, **kwargs):
                if cmds.contextInfo(ctxName, exists=True):   
                    self.createBrushWindow()     
                    #creates brush window after context is updated
                    cmds.currentCtx(ctxName)
                    self.currentCtxName = ctxName                    
                    contextIndex = self.ctxNames.index(ctxName)
                    self.ctxDetection[contextIndex] = True
                    #set current context to last used tool.
                    cmds.setToolTo(ctxName)
                    cmds.scriptJob(uiDeleted=[self.brushWin, self.changeToSelectTool])
                else:
                    return fn(self, *args, **kwargs)
            return ctxWrapper
        return ctxDecorator
    
    def changeToSelectTool(self):
        '''
            after each context operation, change to default select tool.
        '''
        cmds.setToolTo('selectSuperContext')

    @runAssociatedCtx(ctxNames[0])
    def createCurveDrawCtx(self, *args):
        '''
            creates the curve draw tool at first function call.
        '''
        self.createBrushWindow()      
        cmds.curveSketchCtx(self.ctxNames[0], image1=ctxControl.queryDirectory + 'images\\pencilJoint icon64.png')
        self.currentCtxName = self.ctxNames[0]
        self.ctxDetection[0] = True
        cmds.setToolTo(self.ctxNames[0])
        cmds.scriptJob(uiDeleted=[self.brushWin, self.changeToSelectTool])

    @runAssociatedCtx(ctxNames[1])
    def createCurveCVCtx(self, *args):
        '''
            creates curve tool with control vertices.
        '''
        self.createBrushWindow()
        cmds.curveCVCtx(self.ctxNames[1], image1=ctxControl.queryDirectory + 'images\\curveJoint icon64.png')
        self.currentCtxName = self.ctxNames[1]
        self.ctxDetection[1] = True
        cmds.setToolTo(self.ctxNames[1])
        cmds.scriptJob(uiDeleted=[self.brushWin, self.changeToSelectTool])
        
    @runAssociatedCtx(ctxNames[2])
    def createArtSelectCtx(self, *args):
        '''
            creates art selection tool with dragSlider.
        '''
        self.createBrushWindow()
        cmds.artSelectCtx(self.ctxNames[2], image1=ctxControl.queryDirectory + 'images\\brushJoint icon64.png',
                        toggleall=True, dragSlider='radius')
        self.currentCtxName = self.ctxNames[2]
        self.ctxDetection[2] = True
        cmds.setToolTo(self.ctxNames[2])    
        cmds.scriptJob(uiDeleted=[self.brushWin, self.changeToSelectTool])        
        
    def paintControlsDetection(self, *args):
        '''
            detects paint controls from the user.
        '''
        queryBrushRadius = cmds.floatSliderGrp(self.brushWidgets[0], q=True, v=True)
        queryDegreeCtx = cmds.intSliderGrp(self.brushWidgets[1], q=True, v=True)
        queryShowBrush = cmds.checkBox(self.brushWidgets[3], q=True, v=True)
        queryShowVertex = cmds.checkBox(self.brushWidgets[4], q=True, v=True)
        queryTangent = cmds.checkBox(self.brushWidgets[5], q=True, v=True)
        queryReflection = cmds.checkBox(self.brushWidgets[6], q=True, v=True)
        querySelectAll = cmds.checkBox(self.brushWidgets[7], q=True, v=True)
        #query values from user
        
        queryPaintControl = [queryBrushRadius,queryDegreeCtx, queryShowBrush, queryShowVertex,
                            queryTangent, queryReflection, querySelectAll]
        paintControlDetect = [None, None, False, False, False, False, False, False]
        # append those values to a local list.
        
        for i in range(len(queryPaintControl)):
            if i>=0 and i<2:
                paintControlDetect[i] = queryPaintControl[i]
            elif queryPaintControl[i] is True:
                paintControlDetect[i] = True         
            
        for i in range(3):
            if self.ctxDetection[i]:
                print( 'ctx {} is activated'.format(self.ctxNames[i]))
                self.updateCtx(self.ctxNames[i], attributes=paintControlDetect)
                cmds.scriptJob(uiDeleted=[self.brushWin, 'cmds.ctxCompletion()'])
                    
    def updateCtx(self, ctxName, **kwargs):
        '''
            updates ctx values based on user specification
        '''
        if self.ctxDetection[2]:   
            cmds.artSelectCtx(self.ctxNames[2], e=True, radius=kwargs['attributes'][0], 
                                o=kwargs['attributes'][2], scv=kwargs['attributes'][3], ads=False, 
                                selectall=kwargs['attributes'][6], unselectall = not kwargs['attributes'][6],
                                tangentOutline=kwargs['attributes'][4], reflection=kwargs['attributes'][5])
        elif self.ctxDetection[1]:
            try:
                cmds.curveCVCtx(self.ctxNames[1], e=True, degree=int(kwargs['attributes'][1]))
            except RuntimeError:
                print('Cannot change curve degree during creation.')
            
    def resetControls(self, *args):
        '''
            resets all control ctx values to default.
        '''
        cmds.floatSliderGrp(self.brushWidgets[0], e=True, v=0.2)
        cmds.intSliderGrp(self.brushWidgets[1], e=True, v=5)
        cmds.intSliderGrp(self.brushWidgets[2], e=True, v=5)
        cmds.checkBox(self.brushWidgets[3], e=True, v=False)
        cmds.checkBox(self.brushWidgets[4], e=True, v=False)
        cmds.checkBox(self.brushWidgets[5], e=True, v=False)
        cmds.checkBox(self.brushWidgets[6], e=True, v=False)
        cmds.checkBox(self.brushWidgets[7], e=True, v=False)

    def findNumCarpals(self, *args):
        '''
            queries the number of carpals whenever joint slider is changed.
        '''
        self.numCarpals = cmds.intSliderGrp(self.brushWidgets[2], q=True, v=True)
        self.changed=True

    def commitChanges(self, *args):
        '''
            whenever the user presses the Done button, this code commits the 
            changes.
        '''
        self.changeToSelectTool()
        curveControls = curveCVcontrols()
        if self.ctxDetection[0] or self.ctxDetection[1]:
            try:
                if self.changed is False:
                    curveControls.createDrawjoints(number_carpals=self.defaultNumCarpals)
                else:
                    curveControls.createDrawjoints(number_carpals=self.numCarpals)
            except TypeError:
                curveControls.createDrawjoints(number_carpals=self.defaultNumCarpals)

    def information(self, *args):
        '''
            about the brush widget tool.
        '''
        cmds.confirmDialog( title='About', message=self.message, button=['OK'], 
                            defaultButton='OK', dismissString='OK' )

    def deleteActiveWindows(self, windowName):
        if cmds.window(windowName, exists=True):
            cmds.deleteUI(windowName)

    def createBrushWindow(self):
        '''
            creates a separate window for brush controls
        '''
        self.deleteActiveWindows(self.title)
        self.brushWin = cmds.window(self.title, widthHeight=self.widthHeight, resizeToFitChildren=True, sizeable=False, menuBar=True)

        cmds.menu(label='File', tearOff=True, allowOptionBoxes=False)
        cmds.menuItem(label='Reset All', command=self.resetControls)
        cmds.menu(label='Help')
        cmds.menuItem(label='About', command=self.information)
        
        cmds.rowColumnLayout(numberOfColumns=1)          
        self.brushWidgets[0] = cmds.floatSliderGrp(label='Brush Radius:', minValue=0.1, maxValue=10.0, value=0.2, field=True)
        self.brushWidgets[1] = cmds.intSliderGrp(label='Curve Degree:', minValue=3, maxValue=9, value=5, field=True)  
        self.brushWidgets[2] = cmds.intSliderGrp(label='Number Joints:', minValue=4, maxValue=9, value=5, field=True,
                                                    cc= lambda *args: self.findNumCarpals())   
        self.changed = False
        
        cmds.setParent('..')
        
        cmds.rowColumnLayout(numberOfColumns=3, columnOffset=[(1,'left',90), (2,'left',5)])
        cmds.text('Display:')
        self.brushWidgets[3] = cmds.checkBox('Show Brush', w=140)
        self.brushWidgets[4] = cmds.checkBox('Show Vertices')
        cmds.text('Options:')
        self.brushWidgets[5] = cmds.checkBox('Tangent Outline')
        self.brushWidgets[6] = cmds.checkBox('Reflection')
        cmds.text('Selection:')
        self.brushWidgets[7] = cmds.checkBox('Select All')
        cmds.setParent('..')

        cmds.rowColumnLayout(numberOfColumns=2)
        cmds.button('Edit brush', w=self.widthHeight[0]/2, command=self.paintControlsDetection)
        cmds.button('Finished Curves', w=self.widthHeight[0]/2, command=self.commitChanges)

        cmds.showWindow(self.title)
        
class mainUI(curveCVcontrols, paintHandControls, ctxControl):
    
    message = '''   
    ----------------------------------------------------
    this tool creates an automatic hand rig
    using 2 methods:
    
    method 1:
    users specify the positions of control vertices
    and the rig joints will created along those 
    control points.
    
    method 2:
    users paint the faces of the main fingers tips
    and palm of hands, the algorithm will interpolate
    positions between these hand positions and create 
    a general hand rig.  
    -----------------------------------------------------
    '''
    
    message2 = '''
    -----------------------------------------------------
    About:-
    
    Draw Curves tools:
    - The user is expected to draw a curve and the 
      program will inherently create joints as per the 
      average length of the curve and as many joints the
      user specifies in the user interface.
    - If a more general hand rig is a required outcome,
      then the user is encouraged to use the curve hand
      draw tool which averages the amount of joints 
      based upon the loose stroke and length of the drawn
      curve
    - For more accurate hand rigs, the user should 
      implement the draw EP curve tool, where they can
      indicate certain control points and alter the
      position and degree of those cv's to obtain a more
      precise result.
    - The undo selected is a way for the user to delete 
      any unrequired cv's should they have made a mistake
      or want to create a less intricate hand rig.
    
    Paint Hand Rig:
    - This tool interpolates the positions of rig joints
      based off the component selection i.e faces, edges 
      or verts painted by the user. 
    - Before starting, kindly indicate which hand the 
      joint will be intended for. Other selections are
      restricted until this information is supplied.
    - Whenever a joint is created -  or say a selection of
      faces is specified at the general position of that
      joint - please select the joint checkbox at the 
      relevant finger and thumb position where you want to 
      eventually place that joint.
    - While painting the selection, if at any
      time the user has misplaced or mistakenly selected
      components for joint placement, press the undo 
      selection to restart selection.
    -----------------------------------------------------
    '''  
    title = 'autoHandRig'
    #name of main window
    widthHeight = (515,150)    
    joints = [False, False, False, False, False] 
    knuckles = [False, False, False, False, False] 
    baseJoint = False
    baseJointPos = False
    #-------------------------------General UI---------------------------------
    
    def __init__(self): 
        self.isSelected= False 
        self.entered = False
        self.jointWidget, self.knuckleWidget = {}, {}
        self.baseJointWidget = {}
        self.widgets = {}
        self.listOfFingerPos, self.listOfKnucklePos = {}, {}
        for i in range(len(self.joints)): 
            self.listOfFingerPos['joint_' + str(i)] = False   
            self.listOfKnucklePos['knuckle_' + str(i)] = False
        
    def __str__(self):
        return self.message                                    
    
    def resetAllValues(self, *args):
        '''
            when the user wants to reset values for all commands.
        '''
        cmds.intSliderGrp(self.widgets['number_carpals'], e=True, v=3)
        for i in range(1,6): cmds.checkBox(self.jointWidget['joint_' + str(i)], e=True, v=False)
        for i in range(1,6): cmds.checkBox(self.knuckleWidget['knuckle_' + str(i)], e=True, v=False)
        cmds.checkBox(self.baseJointWidget['base_joint'], e=True, v=False)

    def queryDirectory(self, *pArgs):
        '''
            asks the user to enter the absolute file path towards the folder containing all the essential data for the program.
        '''
        currDirectory = cmds.promptDialog(title='Set current directory',
                                        message='Enter file path:',
                                        button = ['OK','Cancel'], defaultButton = 'OK',
                                        cancelButton='Cancel', dismissString='Cancel') # prompts the user to set the current directory
                                        # in windows system, the absolute file path should be '/' separated.
        newDirectory = ''
        if currDirectory == 'OK': # if the user selects the OK option, it will split the directory by '/' and replace every instance of it with '//'
            oldDirectory = cmds.promptDialog(q=True, text=True)
            for i in oldDirectory.split('\\'): # action to split the entered file path by '//'
                newDirectory += i + '\\'
            return newDirectory # concatenates strings separated by '//' within entered file path into a separate string variable
        # returns string variable containing concatenated strings
        else:
            print('No such file path exists in current directory.')  # if no such file path exists or is in the wrong format, informs users 'No such file path exists'
                
    def generalButtonDetection(self, *args):
        '''
            detection mechanism whenever any general buttons are
            clicked by the user.
        '''
        queryCarpals = cmds.intSliderGrp(self.widgets['number_carpals'], q=True, v=True)    
        queryFingerDetection = [cmds.checkBox(self.jointWidget['joint_' + str(i)], q=True, v=True) 
                                    for i in range(1,6)]
        queryKnuckleDetection = [cmds.checkBox(self.knuckleWidget['knuckle_' + str(i)], q=True, v=True) 
                                    for i in range(1,6)]   
        queryBaseJointDetection = cmds.checkBox(self.baseJointWidget['base_joint'], q=True, v=True)

        if queryBaseJointDetection:
            self.baseJoint = True
        if queryBaseJointDetection!=True:
            self.baseJoint = False
            self.baseJointPos = False

        for j in range(5):
            if (queryFingerDetection[j]):
                self.joints[j] = True
            if (queryKnuckleDetection[j]):
                self.knuckles[j] = True
            if (queryFingerDetection[j])!=True:
                self.joints[j] = False
                self.listOfFingerPos['finger_' + str(j)] = False 
            if (queryKnuckleDetection[j])!=True:
                self.knuckles[j] = False
                self.listOfKnucklePos['knuckle_' + str(j)] = False 
        #enable relevant joint controls based off user.
        
        self.queryJointPressed(carpalNum=queryCarpals)

    def unselectAll(self, *args):
        '''
            unselects all currently selected checkboxes for joints and knuckles
        '''
        cmds.checkBox(self.baseJointWidget['base_joint'], e=True, v=False)
        self.baseJoint = False
        self.baseJointPos = False

        for i in range(len(self.joints)):
            if self.joints[i] is True:
                self.joints[i] = False
                cmds.checkBox(self.jointWidget['joint_' + str(i+1)], e=True, v=False)

        for j in range(len(self.knuckles)):
            if self.knuckles[j] is True:
                self.knuckles[j] = False
                cmds.checkBox(self.knuckleWidget['knuckle_' + str(j+1)], e=True, v=False)

    @componentErrorDecorator
    def handleBaseJoint(self, objects):
        '''
            queries the values of base joint palm positions.
        '''
        paintHandRig = paintHandControls()      
        self.baseJointPos = paintHandRig.getAverageComponentPos(objects)

    @componentErrorDecorator
    def queryJointPressed(self, **kwargs):
        '''
            queries the joint pressed based off paint selection.
            Only works when a joint checkbox is pressed.
        '''  
        objects = cmds.ls(sl=True, fl=True)
        if len(objects)>=0:
            paintHandRig = paintHandControls()
            if self.baseJoint and self.baseJointPos==False: 
                self.handleBaseJoint(objects)

            for i in range(len(self.joints)):
                if self.joints[i] is True:                       
                    if self.listOfFingerPos['joint_' + str(i)]==False:
                        self.listOfFingerPos['joint_' + str(i)] = paintHandRig.getAverageComponentPos(objects)
                if self.knuckles[i] is True:                       
                    if self.listOfKnucklePos['knuckle_' + str(i)]==False:
                        self.listOfKnucklePos['knuckle_' + str(i)] = paintHandRig.getAverageComponentPos(objects)
                if not self.joints[i]:
                    self.listOfFingerPos['joint_' + str(i)] = False
                    self.joints[i]= False
                if not self.knuckles[i]:
                    self.listOfKnucklePos['knuckle_' + str(i)] = False
                    self.knuckles[i]= False        
            
            if all(self.knuckles)==True and all(self.joints)==True and self.baseJoint==True:
                paintHandRig.createJoints(carpalNum=kwargs['carpalNum'], fingerTipPositions=self.listOfFingerPos,
                                            knucklePositions=self.listOfKnucklePos, baseJoint=self.baseJointPos)
                self.baseJointPos = False
                ctxControl().changeToSelectTool()
            else:
                pass
        else:
            print( 'Please make a selection to see changes')     
            
    def explanation(self, *args):
        '''
            confirm dialog that explains the mechanics of the tools.
        '''
        cmds.confirmDialog( title='About', message=self.message2, button=['OK'], 
                            defaultButton='OK', dismissString='OK' )

    def changeJointDisplaySize(self, *args):
        '''
            changes the visible joint display scale
        '''           
        cmds.jointDisplayScale(cmds.floatSliderGrp(self.widgets['joint_display_scale'], q=True, v=True))
    
    @RuntimeErrorDecorator
    def mainWindow(self):
        '''
            the mainWindow containing all the functionality. 
            Called whenever geometry is selected in the viewport.
        '''
        paintControls = ctxControl()
        jointControls = paintHandControls()
        curveControls = curveCVcontrols()

        if self.entered is False:
            try:
                ctxControl.queryDirectory = self.queryDirectory()
            except ValueError:
                print("Invalid entry. Please enter the correct path")
            self.entered = True

        if cmds.window(self.title, exists=True): 
            cmds.deleteUI(self.title, window=True)

        cmds.window(self.title, widthHeight=self.widthHeight, resizeToFitChildren=True, sizeable=False, menuBar=True)   
        
        cmds.menu(label='File', tearOff=True, allowOptionBoxes=False)
        cmds.menuItem(label='Reset All', command=self.resetAllValues)
        cmds.menu( label='Help', helpMenu=True )
        cmds.menuItem(label='About', command = self.explanation)
        
        cmds.frameLayout('Curve Hand Rigger', width=self.widthHeight[0])
        cmds.rowColumnLayout(numberOfColumns=2)
        
        cmds.button('Draw Hand Curves', w=258, command = paintControls.createCurveDrawCtx)
        cmds.button('CV Hand Curves', w=258, command = paintControls.createCurveCVCtx)
        cmds.button('Delete Curves', w=258, command= curveControls.deleteAllCurves)
        cmds.button('Delete Joints', w=258, command=jointControls.deleteAllJoints)
                
        cmds.setParent('..')
        cmds.setParent('..')
        
        cmds.frameLayout('Paint Hand Rigger', width=self.widthHeight[0])

        cmds.rowColumnLayout(numberOfColumns=2) 
        cmds.text('',w=117)
        self.baseJointWidget['base_joint'] = cmds.checkBox('Palm', w=80, onCommand=self.generalButtonDetection)

        cmds.setParent('..')

        cmds.rowColumnLayout(numberOfColumns=7)  
        cmds.text('',w=72)
        cmds.text('Fingers:', w=45)
        self.jointWidget = {'joint_' + str(i): cmds.checkBox('Finger ' + str(i), w=80, 
                            onCommand=self.generalButtonDetection) for i in range(1,6)}
        
        cmds.setParent('..')
        
        cmds.rowColumnLayout(numberOfColumns=7) 
        cmds.text('',w=72)
        cmds.text('Knuckle:', w=45)
        self.knuckleWidget = {'knuckle_' + str(i): cmds.checkBox('Knuckle ' + str(i), w=80, 
                            onCommand=self.generalButtonDetection) for i in range(1,6)}
        
        cmds.setParent('..')
        cmds.rowColumnLayout(numberOfColumns=1)   
        self.widgets['number_carpals'] = cmds.intSliderGrp(label='No. Carpal Joints:', minValue=4, maxValue=10, value=4, field=True)        
        self.widgets['joint_display_scale'] = cmds.floatSliderGrp(label='Joint Display:', minValue=0.1, maxValue=0.3, value=0.2, field=True,
                                                                    dc = lambda *args: self.changeJointDisplaySize(), precision=3)
        cmds.setParent('..')

        cmds.rowColumnLayout(numberOfColumns=3)  
        cmds.button('Paint Selection', w=172, command=paintControls.createArtSelectCtx)
        cmds.button('Unselect All', w=172, command=self.unselectAll)
        cmds.button('Undo selection', w=172, command=jointControls.undoSelection)
        
        cmds.showWindow(self.title)       

if __name__=='__main__':
    mainUse = mainUI()
    print( mainUse )
    mainUse.mainWindow()

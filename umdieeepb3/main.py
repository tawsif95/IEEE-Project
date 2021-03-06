import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQuick import QQuickView

from PyQt5.QtQml import QQmlComponent, QQmlEngine

from engine import PhotoBoothEngine

# Main Function
if __name__ == '__main__':
    # Create main app
    myApp = QApplication(sys.argv)
    # Create a label and set its properties
    appLabel = QQuickView()
    appLabel.setSource(QUrl('main.qml'))
    #appLabel.load(QUrl('main2.qml'))

    # Show the Label
    appLabel.show()
    
    # Create a QML engine.
    engine = QQmlEngine()
    
    # Initialize PhotoBoothEngine.
    pbengine = PhotoBoothEngine()
    pbengine.on_status.connect(appLabel.rootObject().status)
    pbengine.on_update_filter_preview.connect(appLabel.rootObject().updateImageFilterPreview)
    
    appLabel.rootContext().setContextProperty('pbengine', pbengine)

    # Create a component factory and load the QML script.
    print("Hello")
    component = QQmlComponent(appLabel.engine())
    component.loadUrl(QUrl('TextStatusFly.qml'))
    
    print("Hello2")
    asdf = component.create(appLabel.rootContext())
    
    print("Hello3")
    asdf.setParentItem(appLabel.rootObject())
    asdf.setParent(appLabel.rootObject())
    
    print("Hello4")
    #asdf.setProperty("targetX", 100)
    asdf.setProperty("objectName", "textStatusBar")
    
    print("Hello5")
    appLabel.rootContext().setContextProperty('textStatusBar', asdf)
    
    asdf.setProperty("parentSet", True)
    
    #asdf.setProperty("y", 100)
    
    #print(appLabel)
    #print(appLabel.rootObject())
    #print(asdf)
    #print(asdf.x)
    #print(asdf.y)
    
    #block = appLabel.rootObject().create("TextPopup.qml", parent)
    #print(block)
    #block.x = 100
    #block.y = 200
    
    # Execute the Application and Exit
    myApp.exec_()
    sys.exit()

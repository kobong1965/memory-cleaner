import QtQuick

Rectangle {
    property color fillColor: "#F8FAFD"
    property color strokeColor: "#DCE3EC"
    property real panelRadius: 18

    color: fillColor
    radius: panelRadius
    border.width: 1
    border.color: strokeColor
    antialiasing: true
}

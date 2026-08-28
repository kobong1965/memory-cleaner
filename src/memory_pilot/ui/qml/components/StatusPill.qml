import QtQuick

Rectangle {
    id: pill

    property string text: ""
    property string tone: "normal"

    implicitWidth: label.implicitWidth + 20
    implicitHeight: 24
    radius: 12
    antialiasing: true
    color: tone === "protected" ? "#FFF0D8"
         : tone === "restricted" ? "#F2EAFD"
         : tone === "system" ? "#E8EEF5"
         : "#E3F6EF"

    Text {
        id: label
        anchors.centerIn: parent
        text: pill.text
        color: pill.tone === "protected" ? "#9A5C00"
             : pill.tone === "restricted" ? "#73509E"
             : pill.tone === "system" ? "#53657C"
             : "#167A61"
        font.family: "Microsoft YaHei UI"
        font.pixelSize: 10
        font.weight: Font.Medium
    }
}

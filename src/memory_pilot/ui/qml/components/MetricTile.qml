import QtQuick

Rectangle {
    id: tile

    property string label: ""
    property string value: "—"
    property string helper: ""
    property color accent: "#1769FF"

    implicitWidth: 160
    implicitHeight: 94
    radius: 15
    color: "#F7F9FC"
    border.width: 1
    border.color: "#E2E8F0"
    antialiasing: true

    Rectangle {
        x: 14
        y: 16
        width: 4
        height: 18
        radius: 2
        color: tile.accent
    }

    Text {
        x: 27
        y: 15
        text: tile.label
        color: "#718096"
        font.family: "Microsoft YaHei UI"
        font.pixelSize: 11
    }

    Text {
        x: 14
        y: 42
        width: parent.width - 28
        text: tile.value
        color: "#14213A"
        font.family: "Segoe UI Variable Display"
        font.pixelSize: 19
        font.weight: Font.DemiBold
        elide: Text.ElideRight
    }

    Text {
        x: 14
        y: 70
        width: parent.width - 28
        text: tile.helper
        color: "#8A97A8"
        font.family: "Microsoft YaHei UI"
        font.pixelSize: 10
        elide: Text.ElideRight
    }
}

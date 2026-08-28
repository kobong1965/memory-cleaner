import QtQuick
import QtQuick.Controls

Button {
    id: cell

    property bool active: false
    property bool descending: false
    property int textAlignment: Text.AlignLeft

    implicitHeight: 36
    padding: 0
    flat: true

    contentItem: Text {
        text: cell.text + (cell.active ? (cell.descending ? "  ↓" : "  ↑") : "")
        color: cell.active ? "#165DFF" : "#6E7C90"
        font.family: "Microsoft YaHei UI"
        font.pixelSize: 11
        font.weight: cell.active ? Font.DemiBold : Font.Medium
        horizontalAlignment: cell.textAlignment
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        color: cell.hovered ? "#EDF3FA" : "transparent"
        radius: 8
    }
}

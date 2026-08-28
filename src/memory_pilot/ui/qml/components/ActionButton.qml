import QtQuick
import QtQuick.Controls

Button {
    id: control

    property string tone: "primary"
    property color primaryStart: "#1769FF"
    property color primaryEnd: "#2E7CF6"
    property color textColor: tone === "primary" ? "#FFFFFF" : "#20304A"

    implicitHeight: 42
    implicitWidth: 126
    leftPadding: 18
    rightPadding: 18
    enabled: !controller.busy

    contentItem: Text {
        text: control.text
        color: control.enabled ? control.textColor : "#8C99AA"
        font.family: "Microsoft YaHei UI"
        font.pixelSize: 13
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        radius: 12
        antialiasing: true
        border.width: control.tone === "primary" ? 0 : 1
        border.color: control.hovered ? "#B6C5D7" : "#D4DDE8"
        color: control.tone === "primary" ? control.primaryStart : (control.hovered ? "#FFFFFF" : "#F4F7FA")
        gradient: control.tone === "primary" ? primaryGradient : null
        opacity: control.down ? 0.82 : (control.enabled ? 1.0 : 0.62)

        Gradient {
            id: primaryGradient
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: control.primaryStart }
            GradientStop { position: 1.0; color: control.primaryEnd }
        }
    }
}

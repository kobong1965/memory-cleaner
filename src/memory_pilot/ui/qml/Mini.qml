import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Window {
    id: window

    width: 286
    height: 158
    visible: true
    color: "transparent"
    title: "Memory Pilot 迷你悬浮版"
    flags: Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint

    Rectangle {
        id: glassCard
        anchors.fill: parent
        anchors.margins: 1
        radius: 25
        antialiasing: true
        border.width: 1
        border.color: "#B8FFFFFF"
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#F7F9FFFF" }
            GradientStop { position: 0.55; color: "#F5F3FCFF" }
            GradientStop { position: 1.0; color: "#F3EAF3FF" }
        }

        Rectangle {
            x: -44
            y: 82
            width: 168
            height: 112
            radius: 56
            color: "#2639C8B4"
            antialiasing: true
        }

        Rectangle {
            x: 188
            y: -48
            width: 134
            height: 116
            radius: 58
            color: "#214A8FFF"
            antialiasing: true
        }

        Rectangle {
            x: 22
            y: 1
            width: parent.width - 44
            height: 1
            color: "#DFFFFFFF"
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            onClicked: function(mouse) {
                if (mouse.button === Qt.RightButton)
                    contextMenu.popup()
            }
        }

        Item {
            x: 12
            y: 8
            width: 222
            height: 36
            DragHandler {
                target: null
                acceptedButtons: Qt.LeftButton
                onActiveChanged: if (active) window.startSystemMove()
            }
        }

        Row {
            x: 18
            y: 15
            spacing: 7

            Rectangle {
                width: 7
                height: 7
                radius: 4
                anchors.verticalCenter: parent.verticalCenter
                color: controller.busy ? "#FFB648" : "#22B99A"
            }
            Text {
                text: controller.busy ? "MEMORY · WORKING" : "MEMORY · LIVE"
                color: "#596A81"
                font.family: "Segoe UI Variable Text"
                font.pixelSize: 9
                font.weight: Font.DemiBold
                font.letterSpacing: 0.8
            }
        }

        Button {
            id: menuButton
            x: 242
            y: 8
            width: 34
            height: 32
            Accessible.name: "打开菜单"
            onClicked: contextMenu.popup(width - contextMenu.width - 4, height + 4)
            contentItem: Text {
                text: "•••"
                color: "#5A6B82"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.family: "Segoe UI Variable Display"
                font.pixelSize: 11
                font.weight: Font.Bold
            }
            background: Rectangle {
                radius: 10
                color: menuButton.hovered ? "#79FFFFFF" : "transparent"
            }
        }

        Text {
            x: 18
            y: 43
            text: controller.usageText
            color: "#10213B"
            font.family: "Segoe UI Variable Display"
            font.pixelSize: 34
            font.weight: Font.Bold
        }

        Text {
            x: 118
            y: 56
            text: controller.availableText
            color: "#53657C"
            font.family: "Microsoft YaHei UI"
            font.pixelSize: 11
        }

        Rectangle {
            x: 18
            y: 94
            width: 250
            height: 8
            radius: 4
            color: "#81FFFFFF"
            border.width: 1
            border.color: "#51FFFFFF"

            Rectangle {
                width: Math.max(8, parent.width * controller.usagePercent / 100)
                height: parent.height
                radius: 4
                antialiasing: true
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "#20B9A5" }
                    GradientStop { position: 0.52; color: "#258AF3" }
                    GradientStop { position: 1.0; color: "#1769FF" }
                }
                Behavior on width {
                    NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
                }
            }
        }

        Text {
            x: 18
            y: 123
            width: 132
            text: controller.statusText
            color: "#5F7188"
            elide: Text.ElideRight
            font.family: "Microsoft YaHei UI"
            font.pixelSize: 10
        }

        ActionButton {
            x: 166
            y: 111
            width: 102
            height: 36
            implicitHeight: 36
            text: controller.busy ? "处理中…" : "释放内存"
            primaryStart: "#1769FF"
            primaryEnd: "#3389F4"
            onClicked: controller.releaseMemory()
            Accessible.name: "安全释放内存"
        }

        Menu {
            id: contextMenu
            width: 154

            MenuItem {
                text: "打开完整版"
                onTriggered: controller.openFullApp()
            }
            MenuItem {
                text: "立即刷新"
                onTriggered: controller.refresh()
            }
            MenuSeparator { }
            MenuItem {
                text: "退出悬浮版"
                onTriggered: controller.quit()
            }
        }
    }

    Shortcut { sequence: "F5"; onActivated: controller.refresh() }
    Shortcut { sequence: "Ctrl+L"; onActivated: controller.releaseMemory() }
    Shortcut { sequence: "Ctrl+O"; onActivated: controller.openFullApp() }
    Shortcut { sequence: "Ctrl+Q"; onActivated: controller.quit() }
    Shortcut { sequence: "Shift+F10"; onActivated: contextMenu.popup(18, 38) }
    Shortcut { sequence: "Return"; onActivated: controller.releaseMemory() }
    Shortcut { sequence: "Space"; onActivated: controller.releaseMemory() }
}

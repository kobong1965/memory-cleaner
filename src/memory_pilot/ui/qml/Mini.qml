import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Window {
    id: window

    function openDeepCleanPanel() {
        thresholdSlider.value = controller.deepCleanMinutes
        deepCleanPanel.open()
        controller.prepareDeepClean()
    }

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
            width: 54
            text: controller.statusText
            color: "#5F7188"
            elide: Text.ElideRight
            font.family: "Microsoft YaHei UI"
            font.pixelSize: 9
        }

        ActionButton {
            x: 76
            y: 111
            width: 86
            height: 36
            implicitHeight: 36
            tone: "secondary"
            text: "深度清理"
            onClicked: window.openDeepCleanPanel()
            Accessible.name: "设置并执行深度清理"
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
            MenuItem {
                text: "深度清理…"
                onTriggered: window.openDeepCleanPanel()
            }
            MenuSeparator { }
            MenuItem {
                text: "退出悬浮版"
                onTriggered: controller.quit()
            }
        }

        Popup {
            id: deepCleanPanel
            x: 8
            y: 7
            width: 270
            height: 144
            padding: 0
            modal: true
            focus: true
            closePolicy: Popup.CloseOnEscape

            onClosed: previewDebounce.stop()

            background: Rectangle {
                radius: 20
                antialiasing: true
                color: "#FCF9FCFF"
                border.width: 1
                border.color: "#D4FFFFFF"

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    radius: 19
                    color: "transparent"
                    border.width: 1
                    border.color: "#7BB7C8DC"
                }
            }

            contentItem: Item {
                Text {
                    x: 16
                    y: 12
                    text: "深度清理"
                    color: "#12243E"
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }

                Text {
                    x: 174
                    y: 13
                    width: 80
                    text: Math.round(thresholdSlider.value) + " 分钟"
                    color: thresholdSlider.value === 0 ? "#C4652A" : "#40556F"
                    horizontalAlignment: Text.AlignRight
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }

                Slider {
                    id: thresholdSlider
                    x: 16
                    y: 35
                    width: 238
                    height: 22
                    from: 0
                    to: 60
                    stepSize: 1
                    enabled: !controller.busy
                    value: controller.deepCleanMinutes
                    Accessible.name: "未使用时间，0 到 60 分钟"
                    Accessible.description: "程序超过该时间没有成为前台窗口时进入深度清理预览"
                    onMoved: previewDebounce.restart()

                    background: Rectangle {
                        x: thresholdSlider.leftPadding
                        y: thresholdSlider.topPadding + thresholdSlider.availableHeight / 2 - height / 2
                        width: thresholdSlider.availableWidth
                        height: 5
                        radius: 3
                        color: "#D8E1EC"

                        Rectangle {
                            width: thresholdSlider.visualPosition * parent.width
                            height: parent.height
                            radius: 3
                            color: "#2389E8"
                        }
                    }

                    handle: Rectangle {
                        x: thresholdSlider.leftPadding + thresholdSlider.visualPosition * (thresholdSlider.availableWidth - width)
                        y: thresholdSlider.topPadding + thresholdSlider.availableHeight / 2 - height / 2
                        width: 15
                        height: 15
                        radius: 8
                        color: thresholdSlider.pressed ? "#EAF5FF" : "#FFFFFF"
                        border.width: 2
                        border.color: "#2389E8"
                    }
                }

                Text {
                    x: 16
                    y: 61
                    width: 238
                    text: controller.deepCleanPreviewText
                    color: "#263A54"
                    elide: Text.ElideRight
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                }

                Text {
                    x: 16
                    y: 79
                    width: 238
                    text: controller.deepCleanCandidateNames
                    color: "#66788E"
                    elide: Text.ElideRight
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 9
                }

                Text {
                    x: 16
                    y: 96
                    text: "仅正常关闭；未保存内容仍可提示或取消"
                    color: "#7A614F"
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 8
                }

                Button {
                    x: 91
                    y: 112
                    width: 72
                    height: 26
                    text: "取消"
                    Accessible.name: "取消深度清理"
                    onClicked: deepCleanPanel.close()
                    contentItem: Text {
                        text: parent.text
                        color: "#4F6178"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.family: "Microsoft YaHei UI"
                        font.pixelSize: 10
                    }
                    background: Rectangle {
                        radius: 9
                        color: parent.hovered ? "#EAF0F6" : "#F2F5F8"
                        border.width: 1
                        border.color: "#D4DDE8"
                    }
                }

                Button {
                    x: 169
                    y: 112
                    width: 85
                    height: 26
                    enabled: controller.deepCleanCanRun && !controller.deepCleanPreviewBusy && !controller.busy
                    text: controller.busy ? "处理中…" : (controller.deepCleanPreviewBusy ? "检查中…" : "确认关闭")
                    Accessible.name: "确认正常关闭预览中的程序"
                    onClicked: controller.runDeepClean()
                    contentItem: Text {
                        text: parent.text
                        color: parent.enabled ? "#FFFFFF" : "#8D9BAD"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.family: "Microsoft YaHei UI"
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                    }
                    background: Rectangle {
                        radius: 9
                        color: parent.enabled ? (parent.down ? "#176FC5" : "#2389E8") : "#E1E7EE"
                    }
                }
            }

            Timer {
                id: previewDebounce
                interval: 260
                repeat: false
                onTriggered: {
                    controller.setDeepCleanMinutes(Math.round(thresholdSlider.value))
                    controller.prepareDeepClean()
                }
            }
        }
    }

    Shortcut { sequence: "F5"; onActivated: controller.refresh() }
    Shortcut { sequence: "Ctrl+L"; onActivated: controller.releaseMemory() }
    Shortcut { sequence: "Ctrl+D"; onActivated: window.openDeepCleanPanel() }
    Shortcut { sequence: "Ctrl+O"; onActivated: controller.openFullApp() }
    Shortcut { sequence: "Ctrl+Q"; onActivated: controller.quit() }
    Shortcut { sequence: "Shift+F10"; onActivated: contextMenu.popup(18, 38) }
    Shortcut { sequence: "Return"; onActivated: controller.releaseMemory() }
    Shortcut { sequence: "Space"; onActivated: controller.releaseMemory() }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: window

    width: 1240
    height: 780
    minimumWidth: 980
    minimumHeight: 640
    visible: true
    title: "Memory Pilot · 内存领航员"
    color: "#E9EEF5"

    readonly property color ink: "#122038"
    readonly property color muted: "#6F7D90"
    readonly property color cobalt: "#1769FF"
    readonly property color aqua: "#24B6A8"
    readonly property color canvas: "#EEF2F7"
    readonly property color panel: "#F9FBFD"
    readonly property color line: "#DCE3EC"

    background: Rectangle {
        color: window.canvas
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#E7EDF4" }
            GradientStop { position: 0.38; color: "#F1F4F8" }
            GradientStop { position: 1.0; color: "#EAF1F7" }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 212
            Layout.fillHeight: true
            color: "#0C1729"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 22
                spacing: 0

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 74

                    Rectangle {
                        id: brandMark
                        width: 38
                        height: 38
                        radius: 12
                        color: "#18345F"
                        border.width: 1
                        border.color: "#2D5484"

                        Rectangle {
                            x: 9
                            y: 10
                            width: 5
                            height: 18
                            radius: 3
                            color: "#56D7C4"
                        }
                        Rectangle {
                            x: 17
                            y: 6
                            width: 5
                            height: 24
                            radius: 3
                            color: "#58A3FF"
                        }
                        Rectangle {
                            x: 25
                            y: 14
                            width: 5
                            height: 12
                            radius: 3
                            color: "#FFFFFF"
                            opacity: 0.9
                        }
                    }

                    Text {
                        x: 50
                        y: 2
                        text: "Memory Pilot"
                        color: "#F5F8FC"
                        font.family: "Segoe UI Variable Display"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }
                    Text {
                        x: 50
                        y: 27
                        text: "内存领航员"
                        color: "#8191A8"
                        font.family: "Microsoft YaHei UI"
                        font.pixelSize: 10
                    }
                }

                Text {
                    text: "工作台"
                    color: "#62748F"
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 10
                    font.letterSpacing: 1.2
                    Layout.bottomMargin: 10
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 46
                    radius: 12
                    color: "#182A43"

                    Rectangle {
                        width: 3
                        height: 22
                        radius: 2
                        color: "#4DA8FF"
                        anchors.left: parent.left
                        anchors.leftMargin: 1
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 18
                        anchors.verticalCenter: parent.verticalCenter
                        text: "系统内存"
                        color: "#F5F8FC"
                        font.family: "Microsoft YaHei UI"
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                    }
                    Rectangle {
                        width: 7
                        height: 7
                        radius: 4
                        color: controller.busy ? "#FFB648" : "#42D4B3"
                        anchors.right: parent.right
                        anchors.rightMargin: 16
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Item { Layout.fillHeight: true }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 116
                    radius: 14
                    color: "#121F33"
                    border.width: 1
                    border.color: "#20324B"

                    Text {
                        x: 14
                        y: 14
                        text: "安全边界"
                        color: "#DCE7F5"
                        font.family: "Microsoft YaHei UI"
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                    }
                    Text {
                        x: 14
                        y: 39
                        width: parent.width - 28
                        text: "不结束进程\n不停止服务\n不删除文件"
                        color: "#7F91AA"
                        lineHeight: 1.45
                        font.family: "Microsoft YaHei UI"
                        font.pixelSize: 10
                    }
                }

                Text {
                    Layout.topMargin: 14
                    text: "Memory Pilot  0.2.5"
                    color: "#526681"
                    font.family: "Segoe UI Variable Text"
                    font.pixelSize: 9
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 28
                anchors.rightMargin: 28
                anchors.topMargin: 24
                anchors.bottomMargin: 22
                spacing: 16

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    spacing: 14

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1
                        Text {
                            text: "系统内存概览"
                            color: window.ink
                            font.family: "Segoe UI Variable Display"
                            font.pixelSize: 24
                            font.weight: Font.DemiBold
                        }
                        Text {
                            text: "实时查看进程占用，需要时安全归还闲置工作集。"
                            color: window.muted
                            font.family: "Microsoft YaHei UI"
                            font.pixelSize: 11
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: privilegeText.implicitWidth + 26
                        Layout.preferredHeight: 32
                        radius: 16
                        color: "#F9FBFD"
                        border.width: 1
                        border.color: window.line
                        Text {
                            id: privilegeText
                            anchors.centerIn: parent
                            text: controller.privilegeText
                            color: window.muted
                            font.family: "Microsoft YaHei UI"
                            font.pixelSize: 10
                        }
                    }
                }

                GlassPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 168
                    fillColor: "#F9FBFD"
                    strokeColor: "#D9E2EC"
                    panelRadius: 20

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 12

                        MemoryGauge {
                            Layout.preferredWidth: 140
                            Layout.preferredHeight: 140
                            value: controller.usagePercent
                            valueText: controller.usageText
                        }

                        Rectangle {
                            Layout.preferredWidth: 1
                            Layout.fillHeight: true
                            Layout.topMargin: 12
                            Layout.bottomMargin: 12
                            color: "#E2E8F0"
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            columns: window.width < 1100 ? 2 : 4
                            columnSpacing: 10
                            rowSpacing: 10

                            MetricTile {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                label: "已用 / 总计"
                                value: controller.usedText
                                helper: "物理内存"
                                accent: "#2787F5"
                            }
                            MetricTile {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                label: "当前可用"
                                value: controller.availableText
                                helper: "可立即分配"
                                accent: "#24B6A8"
                            }
                            MetricTile {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                label: "进程数量"
                                value: controller.processCountText
                                helper: "当前系统采样"
                                accent: "#FFB648"
                            }
                            MetricTile {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                label: "状态"
                                value: controller.busy ? "处理中" : "稳定"
                                helper: controller.privilegeText
                                accent: controller.busy ? "#FFB648" : "#42B895"
                            }
                        }
                    }
                }

                GlassPanel {
                    id: tablePanel
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    fillColor: "#F9FBFD"
                    strokeColor: "#D9E2EC"
                    panelRadius: 20

                    readonly property real innerWidth: Math.max(680, width - 40)
                    readonly property real nameWidth: Math.max(170, innerWidth * 0.20)
                    readonly property real pidWidth: 108
                    readonly property real statusWidth: 100
                    readonly property real cpuWidth: 82
                    readonly property real memoryWidth: 112
                    readonly property real pathWidth: Math.max(190, innerWidth - nameWidth - pidWidth - statusWidth - cpuWidth - memoryWidth)

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 20
                        anchors.rightMargin: 20
                        anchors.topMargin: 16
                        anchors.bottomMargin: 12
                        spacing: 0

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 44
                            spacing: 10

                            TextField {
                                id: searchField
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                leftPadding: 14
                                rightPadding: 14
                                placeholderText: "搜索名称、PID 或程序路径"
                                color: window.ink
                                placeholderTextColor: "#8996A8"
                                selectionColor: "#BBD7FF"
                                selectedTextColor: window.ink
                                font.family: "Microsoft YaHei UI"
                                font.pixelSize: 12
                                onTextChanged: controller.setSearch(text)
                                Accessible.name: "搜索进程"
                                background: Rectangle {
                                    radius: 12
                                    color: searchField.activeFocus ? "#FFFFFF" : "#F1F5F9"
                                    border.width: 1
                                    border.color: searchField.activeFocus ? "#6EA8FF" : "#DCE3EC"
                                }
                            }

                            Button {
                                id: groupedButton
                                Layout.preferredWidth: 112
                                Layout.preferredHeight: 40
                                checkable: true
                                checked: controller.grouped
                                onClicked: controller.setGrouped(checked)
                                Accessible.name: "按应用分组"
                                contentItem: Row {
                                    spacing: 8
                                    anchors.centerIn: parent
                                    Rectangle {
                                        width: 8
                                        height: 8
                                        radius: 4
                                        color: groupedButton.checked ? window.cobalt : "#AAB5C3"
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                    Text {
                                        text: "按应用分组"
                                        color: window.ink
                                        font.family: "Microsoft YaHei UI"
                                        font.pixelSize: 11
                                    }
                                }
                                background: Rectangle {
                                    radius: 12
                                    color: groupedButton.hovered ? "#FFFFFF" : "#F1F5F9"
                                    border.width: 1
                                    border.color: "#DCE3EC"
                                }
                            }

                            ActionButton {
                                Layout.preferredWidth: 98
                                text: controller.busy ? "处理中" : "刷新"
                                tone: "secondary"
                                onClicked: controller.refresh()
                                Accessible.name: "立即刷新进程列表"
                            }

                            ActionButton {
                                Layout.preferredWidth: 132
                                text: controller.busy ? "处理中…" : "安全释放内存"
                                onClicked: controller.releaseMemory()
                                Accessible.name: "安全释放内存"
                            }
                        }

                        Item { Layout.preferredHeight: 10 }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: "#E3E9F0"
                        }

                        Row {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 38
                            spacing: 0

                            HeaderCell {
                                width: tablePanel.nameWidth
                                text: "程序名称"
                                active: controller.sortKey === "name"
                                descending: controller.sortDescending
                                onClicked: controller.sortBy("name")
                            }
                            HeaderCell {
                                width: tablePanel.pidWidth
                                text: "PID / 数量"
                                active: controller.sortKey === "pid"
                                descending: controller.sortDescending
                                textAlignment: Text.AlignRight
                                onClicked: controller.sortBy("pid")
                            }
                            HeaderCell {
                                width: tablePanel.statusWidth
                                text: "状态"
                                active: controller.sortKey === "status"
                                descending: controller.sortDescending
                                textAlignment: Text.AlignHCenter
                                onClicked: controller.sortBy("status")
                            }
                            HeaderCell {
                                width: tablePanel.cpuWidth
                                text: "CPU"
                                active: controller.sortKey === "cpu"
                                descending: controller.sortDescending
                                textAlignment: Text.AlignRight
                                onClicked: controller.sortBy("cpu")
                            }
                            HeaderCell {
                                width: tablePanel.memoryWidth
                                text: "内存"
                                active: controller.sortKey === "memory"
                                descending: controller.sortDescending
                                textAlignment: Text.AlignRight
                                onClicked: controller.sortBy("memory")
                            }
                            HeaderCell {
                                width: tablePanel.pathWidth
                                text: "程序位置"
                                active: controller.sortKey === "path"
                                descending: controller.sortDescending
                                onClicked: controller.sortBy("path")
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: "#E3E9F0"
                        }

                        ListView {
                            id: processList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            model: processModel
                            boundsBehavior: Flickable.StopAtBounds
                            reuseItems: true

                            ScrollBar.vertical: ScrollBar {
                                policy: ScrollBar.AsNeeded
                                width: 8
                            }

                            delegate: Item {
                                id: processRow
                                required property int index
                                required property string processName
                                required property string pidLabel
                                required property string statusLabel
                                required property string cpuLabel
                                required property string memoryLabel
                                required property string pathLabel
                                required property string statusTone

                                width: processList.width
                                height: 45

                                Rectangle {
                                    anchors.fill: parent
                                    anchors.leftMargin: 1
                                    anchors.rightMargin: 1
                                    radius: 9
                                    color: rowHover.hovered ? "#EDF4FC" : (processRow.index % 2 ? "#F7F9FC" : "transparent")
                                }

                                HoverHandler { id: rowHover }

                                Row {
                                    anchors.fill: parent
                                    spacing: 0

                                    Text {
                                        width: tablePanel.nameWidth
                                        anchors.verticalCenter: parent.verticalCenter
                                        leftPadding: 8
                                        rightPadding: 10
                                        text: processRow.processName
                                        color: window.ink
                                        font.family: "Microsoft YaHei UI"
                                        font.pixelSize: 12
                                        font.weight: Font.Medium
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        width: tablePanel.pidWidth
                                        anchors.verticalCenter: parent.verticalCenter
                                        rightPadding: 10
                                        text: processRow.pidLabel
                                        color: window.muted
                                        horizontalAlignment: Text.AlignRight
                                        font.family: "Cascadia Mono"
                                        font.pixelSize: 10
                                        elide: Text.ElideRight
                                    }
                                    Item {
                                        width: tablePanel.statusWidth
                                        height: parent.height
                                        StatusPill {
                                            anchors.centerIn: parent
                                            text: processRow.statusLabel
                                            tone: processRow.statusTone
                                        }
                                    }
                                    Text {
                                        width: tablePanel.cpuWidth
                                        anchors.verticalCenter: parent.verticalCenter
                                        rightPadding: 8
                                        text: processRow.cpuLabel
                                        color: window.muted
                                        horizontalAlignment: Text.AlignRight
                                        font.family: "Segoe UI Variable Text"
                                        font.pixelSize: 11
                                    }
                                    Text {
                                        width: tablePanel.memoryWidth
                                        anchors.verticalCenter: parent.verticalCenter
                                        rightPadding: 10
                                        text: processRow.memoryLabel
                                        color: "#30435F"
                                        horizontalAlignment: Text.AlignRight
                                        font.family: "Segoe UI Variable Text"
                                        font.pixelSize: 11
                                        font.weight: Font.Medium
                                    }
                                    Text {
                                        width: tablePanel.pathWidth
                                        anchors.verticalCenter: parent.verticalCenter
                                        leftPadding: 8
                                        rightPadding: 8
                                        text: processRow.pathLabel
                                        color: "#7A8798"
                                        font.family: "Segoe UI Variable Text"
                                        font.pixelSize: 10
                                        elide: Text.ElideMiddle
                                    }
                                }
                            }

                            Text {
                                anchors.centerIn: parent
                                visible: processList.count === 0 && !controller.busy
                                text: "没有符合条件的进程\n请调整搜索条件"
                                horizontalAlignment: Text.AlignHCenter
                                lineHeight: 1.5
                                color: window.muted
                                font.family: "Microsoft YaHei UI"
                                font.pixelSize: 12
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: "#E3E9F0"
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 30
                            Text {
                                Layout.fillWidth: true
                                text: controller.statusText
                                color: window.muted
                                font.family: "Microsoft YaHei UI"
                                font.pixelSize: 10
                                elide: Text.ElideRight
                            }
                            Text {
                                text: controller.updatedText
                                color: "#8B98A9"
                                font.family: "Segoe UI Variable Text"
                                font.pixelSize: 10
                            }
                        }
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        height: 3
                        radius: 2
                        color: controller.busy ? window.cobalt : "transparent"
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        visible: controller.noticeVisible
        color: "#73101A2A"
        z: 20

        MouseArea { anchors.fill: parent }

        GlassPanel {
            width: 420
            height: 322
            anchors.centerIn: parent
            panelRadius: 24
            fillColor: "#FCFDFE"
            strokeColor: "#FFFFFF"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 14

                Rectangle {
                    Layout.preferredWidth: 44
                    Layout.preferredHeight: 44
                    radius: 22
                    color: "#E3F6EF"
                    Text {
                        anchors.centerIn: parent
                        text: "✓"
                        color: "#138064"
                        font.family: "Segoe UI Variable Display"
                        font.pixelSize: 22
                        font.weight: Font.Bold
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: controller.noticeTitle
                    color: window.ink
                    font.family: "Segoe UI Variable Display"
                    font.pixelSize: 20
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: controller.noticeBody
                    color: window.muted
                    wrapMode: Text.Wrap
                    lineHeight: 1.35
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 11
                }
                ActionButton {
                    Layout.alignment: Qt.AlignRight
                    text: "完成"
                    enabled: true
                    onClicked: controller.dismissNotice()
                    Accessible.name: "关闭结果窗口"
                }
            }
        }
    }

    Shortcut { sequence: "Ctrl+F"; onActivated: searchField.forceActiveFocus() }
    Shortcut { sequence: "F5"; onActivated: controller.refresh() }
    Shortcut { sequence: "Ctrl+L"; onActivated: controller.releaseMemory() }
}

import QtQuick

Item {
    id: gauge

    property real value: 0
    property string valueText: "—%"

    implicitWidth: 142
    implicitHeight: 142

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true

        onPaint: {
            const ctx = getContext("2d")
            const cx = width / 2
            const cy = height / 2
            const radius = Math.min(width, height) / 2 - 13
            const start = Math.PI * 0.72
            const sweep = Math.PI * 1.56
            const active = Math.max(0, Math.min(100, gauge.value)) / 100

            ctx.reset()
            ctx.lineCap = "round"
            ctx.lineWidth = 10
            ctx.strokeStyle = "#E3EAF2"
            ctx.beginPath()
            ctx.arc(cx, cy, radius, start, start + sweep, false)
            ctx.stroke()

            if (active > 0) {
                const gradient = ctx.createLinearGradient(18, height - 10, width - 12, 16)
                gradient.addColorStop(0, "#24B6A8")
                gradient.addColorStop(0.48, "#2787F5")
                gradient.addColorStop(1, "#165DFF")
                ctx.strokeStyle = gradient
                ctx.lineWidth = 11
                ctx.beginPath()
                ctx.arc(cx, cy, radius, start, start + sweep * active, false)
                ctx.stroke()
            }
        }

        Connections {
            target: gauge
            function onValueChanged() { canvas.requestPaint() }
        }
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 42
        text: gauge.valueText
        color: "#10203A"
        font.family: "Segoe UI Variable Display"
        font.pixelSize: 30
        font.weight: Font.Bold
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 82
        text: "内存使用"
        color: "#718096"
        font.family: "Microsoft YaHei UI"
        font.pixelSize: 11
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

pragma ComponentBehavior: Bound

ApplicationWindow {
    id: root
    required property QtObject controller
    visible: true
    width: 900
    height: 700
    minimumWidth: 800
    minimumHeight: 600
    title: "Smart Parking Admin"
    color: root.colors.bg

    // Color scheme matching original CSS
    property QtObject colors: QtObject {
        readonly property color bg: "#1a1a1a"
        readonly property color bgElevated: "#242424"
        readonly property color bgInput: "#2a2a2a"
        readonly property color border: "#333333"
        readonly property color text: "#e0e0e0"
        readonly property color textDim: "#808080"
        readonly property color accent: "#4a4a4a"
        readonly property color green: "#4ade80"
        readonly property color red: "#f87171"
        readonly property color yellow: "#fbbf24"
    }

    // Main content area
    Item {
        anchors.fill: parent

        // Connection Status Indicator (positioned absolutely like original)
        Rectangle {
            id: connectionStatus
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 16
            anchors.rightMargin: 24
            width: statusRow.width + 24
            height: 32
            radius: 6
            color: root.colors.bgElevated
            border.width: 1
            border.color: root.colors.border
            z: 100

            Row {
                id: statusRow
                anchors.centerIn: parent
                spacing: 8

                Rectangle {
                    id: statusDot
                    width: 8
                    height: 8
                    radius: 4
                    anchors.verticalCenter: parent.verticalCenter
                    color: {
                        switch(root.controller.connectionStatus) {
                            case "connected": return root.colors.green
                            case "connecting": return root.colors.yellow
                            case "error": return root.colors.red
                            default: return root.colors.textDim
                        }
                    }

                    SequentialAnimation on opacity {
                        running: root.controller.connectionStatus === "connecting"
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.4; duration: 500 }
                        NumberAnimation { to: 1.0; duration: 500 }
                    }
                }

                Text {
                    text: {
                        switch(root.controller.connectionStatus) {
                            case "connected": return "connected"
                            case "connecting": return "connecting..."
                            case "error": return "error"
                            default: return "disconnected"
                        }
                    }
                    color: {
                        switch(root.controller.connectionStatus) {
                            case "connected": return root.colors.green
                            case "error": return root.colors.red
                            default: return root.colors.textDim
                        }
                    }
                    font.pixelSize: 11
                }
            }
        }

        // Main layout
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 20

            // =========================================================
            // Top Row - Parking Spots
            // =========================================================
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 90
                spacing: 0

                // Available spots counter with divider
                Row {
                    spacing: 24

                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 0

                        Text {
                            text: root.controller.availableSpots
                            font.pixelSize: 48
                            font.weight: Font.Light
                            color: root.colors.text
                        }

                        Text {
                            text: "spots free"
                            font.pixelSize: 12
                            color: root.colors.textDim
                        }
                    }

                    // Vertical divider
                    Rectangle {
                        width: 1
                        height: 60
                        color: root.colors.border
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Item { width: 20 }

                // Parking spots row
                Row {
                    spacing: 12
                    Layout.fillWidth: true

                    Repeater {
                        model: 5

                        Rectangle {
                            required property int index
                            width: 80
                            height: 72
                            radius: 8
                            color: spotMouseArea.containsMouse ? root.colors.bgInput : root.colors.bgElevated

                            MouseArea {
                                id: spotMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.controller.toggleSpot(parent.index)
                            }

                            Column {
                                anchors.centerIn: parent
                                spacing: 8

                                Text {
                                    text: parent.parent.index + 1
                                    font.pixelSize: 18
                                    font.weight: Font.Medium
                                    color: root.colors.text
                                    anchors.horizontalCenter: parent.horizontalCenter
                                }

                                Rectangle {
                                    width: 12
                                    height: 12
                                    radius: 6
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    color: root.controller.isSpotOccupied(parent.parent.index) ? root.colors.red : root.colors.green
                                }
                            }
                        }
                    }
                }

                Item { Layout.fillWidth: true }
            }

            // =========================================================
            // Middle Row - Warning Control + Console (fills remaining space)
            // =========================================================
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 20

                // Warning Control Panel
                Rectangle {
                    Layout.preferredWidth: 160
                    Layout.fillHeight: true
                    radius: 8
                    color: root.colors.bgElevated

                    Column {
                        anchors.centerIn: parent
                        spacing: 16

                        // Light bulb indicator
                        Rectangle {
                            id: lightBulb
                            width: 32
                            height: 32
                            radius: 16
                            anchors.horizontalCenter: parent.horizontalCenter
                            color: root.controller.warningLight ? root.colors.red : root.colors.green

                            // Flash animation when warning is ON
                            SequentialAnimation on opacity {
                                id: flashAnimation
                                running: root.controller.warningLight
                                loops: Animation.Infinite
                                NumberAnimation { to: 0.3; duration: 300 }
                                NumberAnimation { to: 1.0; duration: 300 }
                            }
                        }

                        // Warn On button
                        Rectangle {
                            width: 120
                            height: 36
                            radius: 6
                            anchors.horizontalCenter: parent.horizontalCenter
                            color: {
                                if (root.controller.warningLight) return root.colors.accent
                                return warnOnMouse.containsMouse ? root.colors.accent : root.colors.bgInput
                            }

                            Text {
                                anchors.centerIn: parent
                                text: "warn on"
                                color: root.controller.warningLight || warnOnMouse.containsMouse ? root.colors.text : root.colors.textDim
                                font.pixelSize: 12
                            }

                            MouseArea {
                                id: warnOnMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.controller.setWarningOn()
                            }
                        }

                        // Warn Off button
                        Rectangle {
                            width: 120
                            height: 36
                            radius: 6
                            anchors.horizontalCenter: parent.horizontalCenter
                            color: {
                                if (!root.controller.warningLight) return root.colors.accent
                                return warnOffMouse.containsMouse ? root.colors.accent : root.colors.bgInput
                            }

                            Text {
                                anchors.centerIn: parent
                                text: "warn off"
                                color: !root.controller.warningLight || warnOffMouse.containsMouse ? root.colors.text : root.colors.textDim
                                font.pixelSize: 12
                            }

                            MouseArea {
                                id: warnOffMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.controller.setWarningOff()
                            }
                        }
                    }
                }

                // Console/Log Area
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 8
                    color: root.colors.bgElevated
                    clip: true

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 0

                        // Console header
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 44

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 16
                                anchors.rightMargin: 16

                                Text {
                                    text: "sensor log"
                                    font.pixelSize: 11
                                    color: root.colors.textDim
                                }

                                Item { Layout.fillWidth: true }

                                Rectangle {
                                    width: 50
                                    height: 24
                                    radius: 4
                                    color: "transparent"
                                    border.width: 1
                                    border.color: clearMouseArea.containsMouse ? root.colors.textDim : root.colors.border

                                    Text {
                                        anchors.centerIn: parent
                                        text: "clear"
                                        font.pixelSize: 11
                                        color: clearMouseArea.containsMouse ? root.colors.text : root.colors.textDim
                                    }

                                    MouseArea {
                                        id: clearMouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: root.controller.clearLogs()
                                    }
                                }
                            }

                            // Bottom border
                            Rectangle {
                                anchors.bottom: parent.bottom
                                width: parent.width
                                height: 1
                                color: root.colors.border
                            }
                        }

                        // Log output area
                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: true

                            ListView {
                                id: logListView
                                anchors.fill: parent
                                anchors.margins: 12
                                clip: true
                                model: root.controller.logModel
                                spacing: 4

                                ScrollBar.vertical: ScrollBar {
                                    width: 6
                                    policy: ScrollBar.AsNeeded
                                }

                                // Auto-scroll to bottom
                                onCountChanged: {
                                    Qt.callLater(function() {
                                        logListView.positionViewAtEnd()
                                    })
                                }

                                delegate: Row {
                                    id: logDelegate
                                    required property string timestamp
                                    required property string message
                                    width: logListView.width - 12
                                    spacing: 12
                                    topPadding: 2
                                    bottomPadding: 2

                                    Text {
                                        text: logDelegate.timestamp
                                        font.family: "SF Mono, Monaco, Consolas, monospace"
                                        font.pixelSize: 12
                                        color: root.colors.accent
                                        width: 60
                                    }

                                    Text {
                                        text: logDelegate.message
                                        font.family: "SF Mono, Monaco, Consolas, monospace"
                                        font.pixelSize: 12
                                        color: root.colors.textDim
                                        width: parent.width - 72
                                        wrapMode: Text.Wrap
                                    }
                                }
                            }

                            // Empty state
                            Text {
                                visible: logListView.count === 0
                                anchors.centerIn: parent
                                text: "No messages yet..."
                                color: root.colors.textDim
                                font.pixelSize: 12
                                font.italic: true
                            }
                        }
                    }
                }
            }

            // =========================================================
            // Bottom Row - Message Input
            // =========================================================
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                Text {
                    text: "display board"
                    font.pixelSize: 11
                    color: root.colors.textDim
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 52
                        radius: 6
                        color: root.colors.bgElevated
                        border.width: 1
                        border.color: messageInput.activeFocus ? root.colors.accent : root.colors.border

                        TextArea {
                            id: messageInput
                            anchors.fill: parent
                            anchors.margins: 4
                            leftPadding: 12
                            rightPadding: 12
                            topPadding: 8
                            bottomPadding: 8
                            color: root.colors.text
                            font.pixelSize: 13
                            placeholderText: "Enter message for display..."
                            placeholderTextColor: root.colors.textDim
                            wrapMode: TextArea.Wrap
                            background: null

                            text: root.controller.displayMessage
                            onTextChanged: {
                                if (text !== root.controller.displayMessage) {
                                    root.controller.setDisplayMessage(text)
                                }
                            }

                            Keys.onReturnPressed: function(event) {
                                if (!(event.modifiers & Qt.ShiftModifier)) {
                                    event.accepted = true
                                    root.controller.sendDisplayMessage()
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 80
                        Layout.preferredHeight: 52
                        radius: 6

                        property bool sendEnabled: root.controller.displayMessage.trim().length > 0

                        color: sendMouseArea.containsMouse && sendEnabled ? root.colors.accent : root.colors.bgElevated
                        border.width: 1
                        border.color: sendMouseArea.containsMouse && sendEnabled ? root.colors.accent : root.colors.border
                        opacity: sendEnabled ? 1.0 : 0.4

                        Text {
                            anchors.centerIn: parent
                            text: "send"
                            font.pixelSize: 12
                            color: root.colors.text
                        }

                        MouseArea {
                            id: sendMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: parent.sendEnabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                            onClicked: {
                                if (parent.sendEnabled) {
                                    root.controller.sendDisplayMessage()
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

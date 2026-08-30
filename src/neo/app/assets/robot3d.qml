import QtQuick
import QtQuick3D

Rectangle {
    id: scene
    color: "transparent"
    property string stateName: "idle"

    View3D {
        anchors.fill: parent
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Transparent
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.VeryHigh
        }
        PerspectiveCamera { position: Qt.vector3d(0, 10, 520); clipFar: 2000 }
        DirectionalLight { eulerRotation.x: -28; eulerRotation.y: -32; brightness: 1.25 }
        PointLight { position: Qt.vector3d(-160, 110, 220); color: "#a8d8ff"; brightness: 42 }
        PointLight { position: Qt.vector3d(170, -40, 160); color: "#9d72ff"; brightness: 34 }

        Node {
            id: robot
            position: Qt.vector3d(0, stateName === "thinking" ? -2 : 0, 0)
            eulerRotation.z: stateName === "thinking" ? -7 : 0
            Behavior on eulerRotation.z { NumberAnimation { duration: 380; easing.type: Easing.OutBack } }

            PrincipledMaterial { id: whiteShell; baseColor: "#ffffff"; metalness: 0.18; roughness: 0.16 }
            PrincipledMaterial { id: pearlShell; baseColor: "#edf5ff"; metalness: 0.3; roughness: 0.12 }
            PrincipledMaterial { id: graphite; baseColor: "#101826"; metalness: 0.72; roughness: 0.2 }
            PrincipledMaterial { id: cyanGlow; baseColor: "#62f7ff"; emissiveFactor: Qt.vector3d(1.4, 4.2, 4.8); roughness: 0.08 }
            PrincipledMaterial { id: violetGlow; baseColor: "#9e76ff"; emissiveFactor: Qt.vector3d(2.1, 1.0, 4.4); roughness: 0.08 }

            Model { source: "#Sphere"; scale: Qt.vector3d(1.02, .82, .74); y: 82; materials: [whiteShell] }
            Model { source: "#Sphere"; scale: Qt.vector3d(.82, .57, .16); y: 77; z: 65; materials: [graphite] }
            Model { source: "#Sphere"; scale: Qt.vector3d(.15, .18, .055); x: -28; y: 83; z: 83; materials: [cyanGlow] }
            Model { source: "#Sphere"; scale: Qt.vector3d(.15, .18, .055); x: 28; y: 83; z: 83; materials: [cyanGlow] }
            Model { source: "#Cube"; scale: Qt.vector3d(.18, .025, .025); y: 52; z: 83; eulerRotation.z: stateName === "success" ? 0 : 8; materials: [cyanGlow] }
            Model { source: "#Cube"; scale: Qt.vector3d(.2, .018, .018); x: -30; y: 108; z: 81; eulerRotation.z: -8; materials: [pearlShell] }
            Model { source: "#Cube"; scale: Qt.vector3d(.2, .018, .018); x: 30; y: 108; z: 81; eulerRotation.z: 8; materials: [pearlShell] }

            Node { id: leftEar; x: -85; y: 112; eulerRotation.z: -32
                Model { source: "#Cone"; scale: Qt.vector3d(.34, .58, .16); materials: [whiteShell] }
                Model { source: "#Cone"; z: 8; scale: Qt.vector3d(.21, .42, .08); materials: [cyanGlow] }
            }
            Node { id: rightEar; x: 85; y: 112; eulerRotation.z: 32
                Model { source: "#Cone"; scale: Qt.vector3d(.34, .58, .16); materials: [whiteShell] }
                Model { source: "#Cone"; z: 8; scale: Qt.vector3d(.21, .42, .08); materials: [violetGlow] }
            }

            Model { source: "#Sphere"; scale: Qt.vector3d(.65, .82, .5); y: -18; materials: [pearlShell] }
            Model { source: "#Sphere"; scale: Qt.vector3d(.5, .63, .08); y: -18; z: 47; materials: [whiteShell] }
            Model { source: "#Cylinder"; scale: Qt.vector3d(.28, .07, .28); y: 2; z: 48; eulerRotation.x: 90; materials: [cyanGlow] }
            Model { source: "#Torus"; scale: Qt.vector3d(.42,.08,.42); y: -42; z: 52; eulerRotation.x: 90; materials: [violetGlow] }

            Node { id: leftArm; x: -68; y: 2; eulerRotation.z: stateName === "thinking" ? -118 : -18
                Behavior on eulerRotation.z { NumberAnimation { duration: 420; easing.type: Easing.OutBack } }
                Model { source: "#Cylinder"; y: -25; scale: Qt.vector3d(.16, .48, .16); materials: [whiteShell] }
                Model { source: "#Sphere"; y: -54; scale: Qt.vector3d(.25, .25, .25); materials: [whiteShell] }
                Model { source: "#Torus"; y: -54; scale: Qt.vector3d(.18,.045,.18); materials: [cyanGlow] }
            }
            Node { id: rightArm; x: 68; y: 2; eulerRotation.z: stateName === "thinking" ? 40 : 18
                Behavior on eulerRotation.z { NumberAnimation { duration: 420; easing.type: Easing.OutBack } }
                Model { source: "#Cylinder"; y: -25; scale: Qt.vector3d(.16, .48, .16); materials: [whiteShell] }
                Model { source: "#Sphere"; y: -54; scale: Qt.vector3d(.25, .25, .25); materials: [whiteShell] }
                Model { source: "#Torus"; y: -54; scale: Qt.vector3d(.18,.045,.18); materials: [violetGlow] }
            }
            Node { id: leftLeg; x: -28; y: -88
                Model { source: "#Cylinder"; y: -16; scale: Qt.vector3d(.17, .38, .17); materials: [graphite] }
                Model { source: "#Sphere"; y: -40; z: 8; scale: Qt.vector3d(.32, .17, .45); materials: [whiteShell] }
            }
            Node { id: rightLeg; x: 28; y: -88
                Model { source: "#Cylinder"; y: -16; scale: Qt.vector3d(.17, .38, .17); materials: [graphite] }
                Model { source: "#Sphere"; y: -40; z: 8; scale: Qt.vector3d(.32, .17, .45); materials: [whiteShell] }
            }
            Model { visible: stateName === "thinking"; source: "#Torus"; y: 142; scale: Qt.vector3d(.75,.08,.75); materials: [violetGlow]
                NumberAnimation on eulerRotation.y { from: 0; to: 360; duration: 900; loops: Animation.Infinite }
            }
            Model { source: "#Torus"; y: -145; scale: Qt.vector3d(.72,.055,.72); materials: [cyanGlow]
                SequentialAnimation on scale {
                    loops: Animation.Infinite
                    Vector3dAnimation { to: Qt.vector3d(.9,.055,.9); duration: 650 }
                    Vector3dAnimation { to: Qt.vector3d(.62,.055,.62); duration: 650 }
                }
            }

            SequentialAnimation on y {
                loops: Animation.Infinite
                NumberAnimation { to: 4; duration: 760; easing.type: Easing.InOutSine }
                NumberAnimation { to: -3; duration: 760; easing.type: Easing.InOutSine }
            }
            SequentialAnimation {
                running: stateName === "walking"; loops: Animation.Infinite
                ParallelAnimation {
                    NumberAnimation { target: leftLeg; property: "eulerRotation.x"; to: 24; duration: 190 }
                    NumberAnimation { target: rightLeg; property: "eulerRotation.x"; to: -24; duration: 190 }
                }
                ParallelAnimation {
                    NumberAnimation { target: leftLeg; property: "eulerRotation.x"; to: -24; duration: 190 }
                    NumberAnimation { target: rightLeg; property: "eulerRotation.x"; to: 24; duration: 190 }
                }
            }
        }
    }
}

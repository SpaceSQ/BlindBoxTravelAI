// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "BlindBoxCore",
    platforms: [
        .iOS(.v17),
        .macOS(.v14),
    ],
    products: [
        .library(name: "BlindBoxCore", targets: ["BlindBoxCore"]),
    ],
    targets: [
        .target(name: "BlindBoxCore"),
        .testTarget(name: "BlindBoxCoreTests", dependencies: ["BlindBoxCore"]),
    ]
)

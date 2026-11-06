import Foundation
import Compression
import CryptoKit

/// `.bbx` 自有专有格式的载荷：完整行程订单 + 明文景点详情 + 创建者标注/点评。
///
/// 结构遵循交底书 §3.5：底层为包含完整行程 JSON、明文景点详情、出发参数及创建者标注点评的压缩包。
public struct BBXPackage: Codable, Equatable, Sendable {
    public let format: String
    public let version: Int
    public let order: PlanOrder
    public let spots: [Spot]
    public let createdAt: Date
    public let integrityHash: String

    public init(format: String, version: Int, order: PlanOrder, spots: [Spot], createdAt: Date, integrityHash: String) {
        self.format = format
        self.version = version
        self.order = order
        self.spots = spots
        self.createdAt = createdAt
        self.integrityHash = integrityHash
    }
}

extension BBXPackage: Identifiable {
    public var id: String { order.id }
}

public enum BBXError: Error, Equatable {
    case compressionFailed
    case decompressionFailed
    case integrityMismatch
    case unsupportedFormat
    case invalidURL
    case invalidDeepLink
}

/// `.bbx` 编解码器：JSON → zlib 压缩 → 字节流；支持 Base64 深链。
public enum BBXCodec {
    public static let format = "com.spacesq.blindboxtravel.bbx"
    public static let currentVersion = 1
    public static let urlScheme = "blindboxtravel"

    // MARK: - 构建 / 校验

    public static func makePackage(order: PlanOrder, spots: [Spot], now: Date = Date()) -> BBXPackage {
        BBXPackage(
            format: format,
            version: currentVersion,
            order: order,
            spots: spots,
            createdAt: now,
            integrityHash: integrityHash(order: order, spots: spots, createdAt: now)
        )
    }

    /// 完整性校验：重算 SHA256 与存储的 integrityHash 比对（防篡改）。
    public static func verify(_ package: BBXPackage) -> Bool {
        package.format == format
            && package.integrityHash == integrityHash(order: package.order, spots: package.spots, createdAt: package.createdAt)
    }

    // MARK: - 编码 / 解码

    public static func encode(_ package: BBXPackage) throws -> Data {
        let json = try jsonEncoder().encode(package)
        guard let gz = zlibCompress(json) else { throw BBXError.compressionFailed }
        return gz
    }

    public static func decode(_ data: Data) throws -> BBXPackage {
        guard let json = zlibDecompress(data) else { throw BBXError.decompressionFailed }
        let package = try jsonDecoder().decode(BBXPackage.self, from: json)
        guard package.format == format else { throw BBXError.unsupportedFormat }
        guard verify(package) else { throw BBXError.integrityMismatch }
        return package
    }

    // MARK: - 深链

    public static func deepLink(package: BBXPackage) throws -> URL {
        let data = try encode(package)
        var comps = URLComponents()
        comps.scheme = urlScheme
        comps.host = "import"
        comps.queryItems = [URLQueryItem(name: "payload", value: data.base64EncodedString())]
        guard let url = comps.url else { throw BBXError.invalidURL }
        return url
    }

    public static func parseDeepLink(_ url: URL) throws -> BBXPackage {
        guard let comps = URLComponents(url: url, resolvingAgainstBaseURL: false),
              comps.scheme == urlScheme,
              let payload = comps.queryItems?.first(where: { $0.name == "payload" })?.value,
              let data = Data(base64Encoded: payload) else {
            throw BBXError.invalidDeepLink
        }
        return try decode(data)
    }

    // MARK: - 内部

    private struct CanonicalPayload: Codable {
        let order: PlanOrder
        let spots: [Spot]
        let createdAt: Date
    }

    private static func integrityHash(order: PlanOrder, spots: [Spot], createdAt: Date) -> String {
        let payload = CanonicalPayload(order: order, spots: spots, createdAt: createdAt)
        // 仅编码受控的 Codable 基础类型，encode 不会抛错。
        let data = try! canonicalEncoder().encode(payload)
        return SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }

    private static func canonicalEncoder() -> JSONEncoder {
        let e = JSONEncoder()
        e.dateEncodingStrategy = .millisecondsSince1970
        e.outputFormatting = [.sortedKeys]
        return e
    }

    private static func jsonEncoder() -> JSONEncoder {
        let e = JSONEncoder()
        e.dateEncodingStrategy = .millisecondsSince1970
        e.outputFormatting = [.sortedKeys]
        return e
    }

    private static func jsonDecoder() -> JSONDecoder {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .millisecondsSince1970
        return d
    }

    // MARK: - zlib（Compression framework）

    static func zlibCompress(_ data: Data) -> Data? {
        guard !data.isEmpty else {
            // 空输入的标准 zlib 流（header + 空 stored block + Adler32）。
            return Data([0x78, 0x9C, 0x03, 0x00, 0x00, 0x00, 0x00, 0x01])
        }
        let src = [UInt8](data)
        let dstCapacity = src.count + src.count / 2 + 64
        var dst = [UInt8](repeating: 0, count: dstCapacity)
        let written = src.withUnsafeBufferPointer { srcPtr -> Int in
            dst.withUnsafeMutableBufferPointer { dstPtr -> Int in
                compression_encode_buffer(dstPtr.baseAddress!, dstPtr.count, srcPtr.baseAddress!, srcPtr.count, nil, COMPRESSION_ZLIB)
            }
        }
        guard written > 0 else { return nil }
        return Data(dst.prefix(written))
    }

    static func zlibDecompress(_ data: Data) -> Data? {
        guard !data.isEmpty else { return nil }
        let src = [UInt8](data)
        var dst = [UInt8](repeating: 0, count: max(1024, src.count * 4))
        while true {
            let written = src.withUnsafeBufferPointer { srcPtr -> Int in
                dst.withUnsafeMutableBufferPointer { dstPtr -> Int in
                    compression_decode_buffer(dstPtr.baseAddress!, dstPtr.count, srcPtr.baseAddress!, srcPtr.count, nil, COMPRESSION_ZLIB)
                }
            }
            if written == 0 { return nil }
            if written < dst.count { return Data(dst.prefix(written)) }
            dst.append(contentsOf: [UInt8](repeating: 0, count: dst.count))
        }
    }
}

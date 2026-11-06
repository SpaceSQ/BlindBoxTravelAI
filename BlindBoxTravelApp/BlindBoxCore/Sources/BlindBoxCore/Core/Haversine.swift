import Foundation

/// Haversine 球面距离计算（交底书 §3.2）。
public enum Haversine {
    public static let earthRadiusKm = 6371.0

    /// 返回两点间的大圆距离（公里）。输入均为角度制（度）。
    public static func distanceKm(lat1: Double, lng1: Double, lat2: Double, lng2: Double) -> Double {
        let dLat = (lat2 - lat1) * .pi / 180.0
        let dLng = (lng2 - lng1) * .pi / 180.0
        let rLat1 = lat1 * .pi / 180.0
        let rLat2 = lat2 * .pi / 180.0
        let a = sin(dLat / 2) * sin(dLat / 2)
            + cos(rLat1) * cos(rLat2) * sin(dLng / 2) * sin(dLng / 2)
        let c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return earthRadiusKm * c
    }

    /// 从两个 [SpotLocation] 计算距离。
    public static func distanceKm(_ p1: SpotLocation, _ p2: SpotLocation) -> Double {
        distanceKm(lat1: p1.lat, lng1: p1.lng, lat2: p2.lat, lng2: p2.lng)
    }
}

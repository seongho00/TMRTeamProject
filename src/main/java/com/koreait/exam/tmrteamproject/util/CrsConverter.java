package com.koreait.exam.tmrteamproject.util;

import org.locationtech.proj4j.*;

public class CrsConverter {
    private static final CRSFactory CRS_FACTORY = new CRSFactory();
    private static final CoordinateTransformFactory CT_FACTORY = new CoordinateTransformFactory();

    // proj4j-epsg 의존성이 있어야 이름(EPSG:xxxx)으로 로드됩니다
    private static final CoordinateReferenceSystem WGS84 =
            CRS_FACTORY.createFromName("EPSG:4326");
    private static final CoordinateReferenceSystem EPSG5179 =
            CRS_FACTORY.createFromName("EPSG:5179");

    private static final CoordinateTransform TO_5179 =
            CT_FACTORY.createTransform(WGS84, EPSG5179);

    // lon, lat (경도, 위도) 순서 주의!
    public static ProjCoordinate toEPSG5179(double lon, double lat) {
        ProjCoordinate src = new ProjCoordinate(lon, lat);
        ProjCoordinate dst = new ProjCoordinate();
        TO_5179.transform(src, dst);
        return dst; // dst.x=Easting(m), dst.y=Northing(m)
    }
}

var mapContainer = document.getElementById('map');
var mapOption = {
    center: new kakao.maps.LatLng(37.566826, 126.9786567),
    level: 7
};
var map = new kakao.maps.Map(mapContainer, mapOption);

const infowindow = new kakao.maps.InfoWindow();

const path = "/js/seoul_area.geojson";

// GeoJSON 파일 로드
$.getJSON(path, function (geojson) {
    const features = geojson.features;

    features.forEach(feature => {
        const coords = feature.geometry.coordinates;
        const type = feature.geometry.type;
        const fillColor = feature.properties.color;
        const properties = feature.properties;

        if (type === "Polygon") {
            drawPolygon(coords[0], fillColor, properties);
        } else if (type === "MultiPolygon") {
            coords.forEach(polygon => {
                drawPolygon(polygon[0], fillColor, properties);
            });
        }
    });
});

function drawPolygon(coordArray, fillColor, properties) {
    const path = coordArray.map(coord => new kakao.maps.LatLng(coord[1], coord[0]));

    const polygon = new kakao.maps.Polygon({
        map: map,
        path: path,
        strokeWeight: 1,
        strokeColor: '#004c80',
        strokeOpacity: 0.8,
        fillColor: fillColor,
        fillOpacity: 0.6
    });

    // 클릭 시 정보창
    kakao.maps.event.addListener(polygon, 'click', function () {
        const content = `
            <div style="padding: 2px;">
                <b>행정동:</b> ${properties.ADSTRD_NM}<br>
                <b>매출 등급:</b> ${properties.매출_등급}<br>
                <b>총 유동인구:</b> ${Number(properties.총_유동인구_수).toLocaleString()}명<br>
                <b>당월 매출액:</b> ${Number(properties.당월_매출_금액).toLocaleString()}원
            </div>
        `;

        // 새로 열기
        infowindow.setContent(content);
        infowindow.setPosition(path[0]);
        infowindow.open(map);
    });
}

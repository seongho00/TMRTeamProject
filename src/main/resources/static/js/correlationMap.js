var mapContainer = document.getElementById('map');
var mapOption = {
    center: new kakao.maps.LatLng(37.566826, 126.9786567),
    level: 7
};
var map = new kakao.maps.Map(mapContainer, mapOption);

const infowindow = new kakao.maps.InfoWindow();

const path = "/js/seoul_area_level.geojson";

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
                <b>위험등급:</b> ${properties.위험등급}<br>
                <b>상관계수:</b> ${Number(properties.상관계수).toLocaleString()}<br>
                <b>상관_위험도점수:</b> ${Number(properties.상관_위험도점수).toLocaleString()}
            </div>
        `;

        // 새로 열기
        infowindow.setContent(content);
        infowindow.setPosition(path[0]);
        infowindow.open(map);
    });
}

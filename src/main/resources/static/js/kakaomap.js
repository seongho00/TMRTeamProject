var mapContainer = document.getElementById('map'),
    mapOption = {
        center: new kakao.maps.LatLng(37.566826, 126.9786567),
        level: 7
    };

var map = new kakao.maps.Map(mapContainer, mapOption);

// 등급별 색상
const colorMap = {
    1: '#ffffb2',
    2: '#fecc5c',
    3: '#fd8d3c',
    4: '#f03b20',
    5: '#bd0026'
};

$.getJSON(path, function (geojson) {
    geojson.features.forEach()
    if (geojson.type === "GeometryCollection" && Array.isArray(geojson.geometries)) {
        geojson.geometries.forEach((geometry) => {
            if (geometry.type === "Polygon") {
                drawPolygon(geometry.coordinates[0]);
            } else if (geometry.type === "MultiPolygon") {
                geometry.coordinates.forEach(polygon => {
                    drawPolygon(polygon[0]);
                });
            }
        });
    } else {
        console.error("GeometryCollection 형식이 아닙니다.");
    }
});

function drawPolygon(coords, name) {
    const path = coords.map(coord => new kakao.maps.LatLng(coord[1], coord[0]));

    const polygon = new kakao.maps.Polygon({
        map: map,
        path: path,
        strokeWeight: 1,
        strokeColor: '#004c80',
        strokeOpacity: 0.8,
        strokeStyle: 'solid',
        fillColor: '#fff',
        fillOpacity: 0
    });

    kakao.maps.event.addListener(polygon, 'click', function () {
        const content = `<div style="padding:8px;"><b>${name}</b></div>`;
        const infowindow = new kakao.maps.InfoWindow({
            content: content,
            position: path[0]
        });
        infowindow.open(map);
    });
}

var mapContainer = document.getElementById('map');
var mapOption = {
    center: new kakao.maps.LatLng(37.566826, 126.9786567),
    level: 7
};
var map = new kakao.maps.Map(mapContainer, mapOption);

const infoWindow = new kakao.maps.InfoWindow();

// 매출 데이터 불러오기 (CSV → JS Object)
const salesData = {};

fetch('/map_result.csv')
    .then(response => response.text())
    .then(data => {
        const lines = data.trim().split('\n');
        const headers = lines[0].split(',');
        lines.slice(1).forEach(line => {
            const values = line.split(',');
            const row = {};
            headers.forEach((h, i) => {
                row[h] = values[i];
            });
            salesData[row['행정동_코드'].toString()] = row;
        });
    });

// GeoJSON 로드
fetch('/Seoul_emds.geojson')
    .then(res => res.json())
    .then(geojson => {
        geojson.features.forEach(feature => {
            const coords = feature.geometry.coordinates;
            const code = feature.properties.EMD_CD;
            const name = feature.properties.EMD_KOR_NM;

            let path = [];

            if (feature.geometry.type === "Polygon") {
                path = coords[0].map(c => new kakao.maps.LatLng(c[1], c[0]));
                drawPolygon(path, code, name);
            } else if (feature.geometry.type === "MultiPolygon") {
                coords.forEach(polygon => {
                    const subPath = polygon[0].map(c => new kakao.maps.LatLng(c[1], c[0]));
                    drawPolygon(subPath, code, name);
                });
            }
        });
    });

function drawPolygon(path, code, name) {
    const polygon = new kakao.maps.Polygon({
        path: path,
        strokeWeight: 0.5,
        strokeColor: '#222',
        strokeOpacity: 1,
        fillColor: '#fff',
        fillOpacity: 0,
        map: map
    });

    // 클릭 감지용 투명 레이어 (보이지 않지만 클릭됨)
    const eventPolygon = new kakao.maps.Polygon({
        path: path,
        strokeWeight: 0,
        strokeColor: '#000',
        strokeOpacity: 0,
        fillColor: '#000',
        fillOpacity: 0.01, // 이게 핵심. 클릭만 감지
        map: map
    });

    kakao.maps.event.addListener(eventPolygon, 'click', function(mouseEvent) {
        const data = salesData[code];
        let content = `<div style="padding:10px;"><b>${name}</b><br>`;

        if (data) {
            content += `예측 매출: ${Number(data['예측_매출']).toLocaleString()}<br>`;
            content += `실제 매출: ${Number(data['실제_매출']).toLocaleString()}</div>`;
        } else {
            content += `데이터 없음</div>`;
        }

        // 클릭 시 색상 채우기
        polygon.setOptions({
            fillColor: '#FFA07A',
            fillOpacity: 0.6
        });

        infoWindow.setContent(content);
        infoWindow.setPosition(mouseEvent.latLng);
        infoWindow.open(map);
    });
}

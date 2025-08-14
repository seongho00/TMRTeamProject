// ===============================
// 카카오맵 + GeoJSON 다각형 + 업종명 검색
// - GeoJSON의 '서비스_업종_코드_명'으로 검색
// - 결과에 위험도 점수/예측 위험도와 함께 표시
// - 결과 클릭 시 해당 폴리곤으로 이동 + 인포윈도우 오픈
// ===============================

// 맵 생성
var mapContainer = document.getElementById('map');
var mapOption = {
    center: new kakao.maps.LatLng(37.566826, 126.9786567),
    level: 7
};
var map = new kakao.maps.Map(mapContainer, mapOption);

// 인포윈도우
const infowindow = new kakao.maps.InfoWindow();

// GeoJSON 경로
const path = "/Seoul_risk.geojson";

// 전역 보관: 피처, 폴리곤, 바운즈
let geoFeatures = []; // 원본 feature 배열
let featurePolygons = []; // { feature, polygon, bounds, firstLatLng }

// GeoJSON 로드
$.getJSON(path, function (geojson) {
    geoFeatures = geojson.features || [];

    // 폴리곤 그리기
    geoFeatures.forEach((feature) => {
        const coords = feature.geometry.coordinates;
        const type = feature.geometry.type;
        const fillColor = feature.properties.color;

        if (type === "Polygon") {
            drawPolygonAndKeep(feature, coords[0], fillColor);
        } else if (type === "MultiPolygon") {
            coords.forEach(polygon => {
                drawPolygonAndKeep(feature, polygon[0], fillColor);
            });
        }
    });
});

// 폴리곤 생성 + 클릭 이벤트 + 참조 보관
function drawPolygonAndKeep(feature, coordArray, fillColor) {
    // 경도,위도 -> LatLng
    const latlngPath = coordArray.map(coord => new kakao.maps.LatLng(coord[1], coord[0]));

    // 폴리곤 생성
    const polygon = new kakao.maps.Polygon({
        map: map,
        path: latlngPath,
        strokeWeight: 1,
        strokeColor: '#004c80',
        strokeOpacity: 0.8,
        fillColor: fillColor,
        fillOpacity: 0.6
    });

    // 바운즈 계산
    const bounds = latlngPath.reduce((b, latlng) => {
        b.extend(latlng);
        return b;
    }, new kakao.maps.LatLngBounds());

    // 클릭 시 정보창
    kakao.maps.event.addListener(polygon, 'click', function () {
        openInfoForFeature(feature, latlngPath[0]);
    });

    // 보관
    featurePolygons.push({
        feature,
        polygon,
        bounds,
        firstLatLng: latlngPath[0]
    });
}

// 특정 feature의 정보창 오픈
function openInfoForFeature(feature, positionLatLng) {
    const p = feature.properties || {};
    const content = `
        <div style="padding: 2px;">
            <b>행정동:</b> ${p.ADSTRD_NM ?? "-"}<br>
            <b>서비스 업종 명:</b> ${p.서비스_업종_코드_명 ?? "-"}<br>
            <b>위험도 단계:</b> ${p.위험도7 ?? "-"}<br>
            <b>위험도 점수:</b> ${safeNumber(p.위험도_점수)}<br>
            <b>예측 위험도:</b> ${safeNumber(p.예측_위험도)}
        </div>
    `;
    infowindow.setContent(content);
    infowindow.setPosition(positionLatLng);
    infowindow.open(map);
}

// 숫자 안전 포맷
function safeNumber(v) {
    const n = Number(v);
    return isNaN(n) ? "-" : n.toLocaleString();
}

// ===============================
// 업종명 검색 UI (간단 컨트롤 생성)
// ===============================

// 맵 상단에 검색창/결과 컨테이너 추가
(function mountSearchUI() {
    // 컨테이너
    const wrap = document.createElement('div');
    wrap.style.cssText = [
        'position:absolute','top:10px','left:10px','z-index:9999',
        'background:#fff','padding:8px','border:1px solid #ddd','border-radius:8px',
        'box-shadow:0 2px 8px rgba(0,0,0,0.15)','min-width:320px','max-width:420px'
    ].join(';');

    // 입력창
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = '업종명을 입력하세요 (예: 한식, 편의점 등)';
    input.id = 'industrySearch';
    input.style.cssText = 'width:70%;padding:6px;border:1px solid #ccc;border-radius:6px;margin-right:6px;';

    // 버튼
    const btn = document.createElement('button');
    btn.textContent = '검색';
    btn.id = 'searchBtn';
    btn.style.cssText = 'padding:6px 10px;border:1px solid #0ea5e9;background:#0ea5e9;color:#fff;border-radius:6px;cursor:pointer;';

    // 결과 영역
    const result = document.createElement('div');
    result.id = 'searchResults';
    result.style.cssText = 'margin-top:8px;max-height:200px;overflow:auto;font-size:13px;line-height:1.4;';

    wrap.appendChild(input);
    wrap.appendChild(btn);
    wrap.appendChild(result);

    // mapContainer 부모에 붙이기
    mapContainer.style.position = 'relative';
    mapContainer.appendChild(wrap);

    // 이벤트
    btn.addEventListener('click', () => {
        const q = input.value.trim();
        doIndustrySearch(q);
    });
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const q = input.value.trim();
            doIndustrySearch(q);
        }
    });
})();

// 업종명으로 검색 실행
function doIndustrySearch(query) {
    const resultsBox = document.getElementById('searchResults');
    resultsBox.innerHTML = '';

    if (!query) {
        resultsBox.innerHTML = '<div>검색어를 입력해줘.</div>';
        return;
    }

    const q = query.toLowerCase();

    // 업종명 포함 검색 (부분일치)
    const matched = featurePolygons.filter(({ feature }) => {
        const name = (feature.properties?.['서비스_업종_코드_명'] || '').toLowerCase();
        return name.includes(q);
    });

    if (matched.length === 0) {
        resultsBox.innerHTML = `<div>검색 결과가 없어. (검색어: ${escapeHtml(query)})</div>`;
        return;
    }

    // 결과 렌더링
    const frag = document.createDocumentFragment();

    // 간단 집계: 같은 업종명이 여러 동에 있으면 평균 위험도도 같이 보여줄게
    const byName = {};
    matched.forEach(({ feature }) => {
        const p = feature.properties || {};
        const name = p['서비스_업종_코드_명'] || '(미정)';
        const risk = Number(p['위험도_점수']);
        const pred = Number(p['예측_위험도']);

        if (!byName[name]) {
            byName[name] = { cnt: 0, riskSum: 0, predSum: 0 };
        }
        if (!isNaN(risk)) byName[name].riskSum += risk;
        if (!isNaN(pred)) byName[name].predSum += pred;
        byName[name].cnt += 1;
    });

    Object.entries(byName).forEach(([name, agg]) => {
        const avgRisk = agg.cnt ? (agg.riskSum / agg.cnt) : NaN;
        const avgPred = agg.cnt ? (agg.predSum / agg.cnt) : NaN;

        const header = document.createElement('div');
        header.style.cssText = 'margin:6px 0;padding:6px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:6px;';
        header.innerHTML = `
            <div style="font-weight:700">${escapeHtml(name)} (건수: ${agg.cnt.toLocaleString()})</div>
            <div>평균 위험도 점수: ${isNaN(avgRisk) ? '-' : Math.round(avgRisk).toLocaleString()}</div>
            <div>평균 예측 위험도: ${isNaN(avgPred) ? '-' : Math.round(avgPred).toLocaleString()}</div>
        `;
        frag.appendChild(header);
    });

    // 상세 리스트
    matched.forEach(({ feature, bounds, firstLatLng }) => {
        const p = feature.properties || {};

        const item = document.createElement('div');
        item.style.cssText = 'padding:6px;border-bottom:1px dashed #e5e7eb;cursor:pointer;';
        item.innerHTML = `
            <div><b>행정동:</b> ${escapeHtml(p.ADSTRD_NM ?? '-')}</div>
            <div><b>업종명:</b> ${escapeHtml(p['서비스_업종_코드_명'] ?? '-')}</div>
            <div><b>위험도 점수:</b> ${safeNumber(p['위험도_점수'])}</div>
            <div><b>예측 위험도:</b> ${safeNumber(p['예측_위험도'])}</div>
        `;

        // 클릭 시 해당 영역으로 이동 + 인포윈도우
        item.addEventListener('click', () => {
            map.setBounds(bounds);
            openInfoForFeature(feature, firstLatLng);
        });

        frag.appendChild(item);
    });

    resultsBox.appendChild(frag);
}

// XSS 방지용 단순 이스케이프
function escapeHtml(str) {
    if (typeof str !== 'string') return str;
    return str.replace(/[&<>"'`=\/]/g, function (s) {
        return ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
            '/': '&#x2F;',
            '`': '&#x60;',
            '=': '&#x3D;'
        })[s];
    });
}

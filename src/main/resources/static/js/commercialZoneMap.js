let map;
let currentPolygon = null;
let emdPolygons = [], emdOverlayList = [];
let sggPolygons = [], sggOverlayList = [];
let currentLevel = 6;
let isProgrammatic = false;

// GeoJSON 키 호환
function getEmdCode(p){ return p?.ADSTRD_CD || p?.행정동_코드 || p?.adm_cd || null; }
function getEmdName(p){ return p?.ADSTRD_NM || p?.행정동_명 || p?.adm_nm || null; }
function getSggName(p){ return p?.SIGUNGU_NM || p?.시군구_명 || p?.sgg_nm || null; }

// 초기화
document.addEventListener("DOMContentLoaded", () => {
    // 맵 초기화
    kakao.maps.load(() => {
        map = new kakao.maps.Map(document.getElementById('map'), {
            center: new kakao.maps.LatLng(37.5665, 126.9780),
            level: 6
        });

        Promise.all([
            loadPolygons("/Seoul_emds.geojson", emdPolygons, emdOverlayList, "#004C80", "ADSTRD_NM"),
            loadPolygons("/Seoul_sggs.geojson", sggPolygons, sggOverlayList, "#007580", "SIGUNGU_NM")
        ]).then(updatePolygonsByZoom);

        kakao.maps.event.addListener(map, 'zoom_changed', () => {
            currentLevel = map.getLevel();
            updatePolygonsByZoom();
        });

        kakao.maps.event.addListener(map, 'click', evt => handleMapClick(evt.latLng));
    });

    // 지역 셀렉트 바인딩
    $(document).on('change', '#sggSelect', onSggChange);
    $(document).on('change', '#emdSelect', onEmdChange);

    // 업종 소스/피커 초기화
    initUpjongSource();
});

/* ================= 지도/도형 로딩 ================= */
function loadPolygons(url, container, overlayList, color, nameKey){
    return fetch(url).then(res => res.json()).then(geojson => {
        geojson.features.forEach(feature => {
            const g = feature.geometry;
            const p = feature.properties;

            const multi = (g.type === "Polygon") ? [g.coordinates] : g.coordinates;
            multi.forEach(poly => {
                const coords = poly[0];
                const path = coords.map(c => new kakao.maps.LatLng(c[1], c[0]));
                const guide = new kakao.maps.Polygon({
                    path, strokeWeight:2, strokeColor:color, strokeOpacity:0.5, strokeStyle:"dash", fillOpacity:0
                });

                // 라벨용 중앙 좌표
                const center = (()=> {
                    const lat = path.reduce((s,pt)=>s+pt.getLat(),0)/path.length;
                    const lng = path.reduce((s,pt)=>s+pt.getLng(),0)/path.length;
                    return new kakao.maps.LatLng(lat,lng);
                })();

                const overlayContent = document.createElement('div');
                overlayContent.innerText = p[nameKey] || getEmdName(p) || getSggName(p) || '';
                overlayContent.style.cssText = "background:#fff;border:1px solid #444;padding:3px 6px;font-size:13px;";
                const overlay = new kakao.maps.CustomOverlay({content:overlayContent, position:center, yAnchor:1, zIndex:3});

                container.push({
                    path,
                    properties:p,
                    guide,
                    overlay,
                    emdCd: getEmdCode(p),
                    emdNM: getEmdName(p),
                    sggName: getSggName(p)
                });
                overlayList.push(overlay);
            });
        });
    });
}

function updatePolygonsByZoom(){
    const isSGG = currentLevel >= 7;
    const show = isSGG ? sggPolygons : emdPolygons;
    const hide = isSGG ? emdPolygons : sggPolygons;
    const showOv = isSGG ? sggOverlayList : emdOverlayList;
    const hideOv = isSGG ? emdOverlayList : sggOverlayList;

    if (currentPolygon){ currentPolygon.setMap(null); currentPolygon=null; }
    hide.forEach(p => p.guide.setMap(null));
    show.forEach(p => p.guide.setMap(map));
    hideOv.forEach(o => o.setMap(null));
    showOv.forEach(o => o.setMap(map));
}

/* ================= 폴리곤 헬퍼 ================= */
function isPointInPolygon(latLng, path){
    let x=latLng.getLng(), y=latLng.getLat(), inside=false;
    for (let i=0,j=path.length-1;i<path.length;j=i++){
        let xi=path[i].getLng(), yi=path[i].getLat();
        let xj=path[j].getLng(), yj=path[j].getLat();
        let intersect=((yi>y)!==(yj>y)) && (x < (xj-xi)*(y-yi)/((yj-yi)||1e-10)+xi);
        if (intersect) inside=!inside;
    }
    return inside;
}
function isSamePath(path1, path2){
    if (!path1||!path2||path1.length!==path2.length) return false;
    for (let i=0;i<path1.length;i++){
        if (path1[i].getLat().toFixed(6)!==path2[i].getLat().toFixed(6) ||
            path1[i].getLng().toFixed(6)!==path2[i].getLng().toFixed(6)) return false;
    }
    return true;
}
function centerOf(path){
    const lat = path.reduce((s,p)=>s+p.getLat(),0)/path.length;
    const lng = path.reduce((s,p)=>s+p.getLng(),0)/path.length;
    return new kakao.maps.LatLng(lat,lng);
}

/* ================= 지도 클릭 -> select 동기화 ================= */
function handleMapClick(latLng){
    const targets = currentLevel >= 7 ? sggPolygons : emdPolygons;
    for (let i=0;i<targets.length;i++){
        const {path, properties} = targets[i];
        if (!isPointInPolygon(latLng, path)) continue;

        const sggNm = getSggName(properties);
        const emdNm = getEmdName(properties);
        let matchedSggNm = null;

        // 시군구 select 설정
        if (sggNm){
            isProgrammatic = true;
            $('#sggSelect').val(sggNm).trigger('change');
            isProgrammatic = false;
        }

        // 행정동 클릭이면, 포함 시군구 찾아서 emd 자동선택
        if (emdNm){
            for (let j=0;j<sggPolygons.length;j++){
                const sgg = sggPolygons[j];
                if (isPointInPolygon(latLng, sgg.path)){
                    matchedSggNm = getSggName(sgg.properties);
                    break;
                }
            }
            if (matchedSggNm){
                window.autoSelectedEmdNm = emdNm; // 이름 저장
                isProgrammatic = true;
                $('#sggSelect').val(matchedSggNm).trigger('change');
                isProgrammatic = false;
            }
        }

        // 하이라이트 토글
        if (currentPolygon && isSamePath(currentPolygon.getPath(), path)){
            currentPolygon.setMap(null); currentPolygon=null; return;
        }
        if (currentPolygon) currentPolygon.setMap(null);
        currentPolygon = new kakao.maps.Polygon({
            map, path, strokeWeight:2, strokeColor:'#004c80', strokeOpacity:0.8, fillColor:'#00a0e9', fillOpacity:0.3
        });
        break;
    }
}

/* ================= 확인 버튼 ================= */
function searchInfoByRegionAndUpjong(){
    // 지역 값
    const sgg = document.getElementById('sggSelect')?.value || '';
    const emd = document.getElementById('emdSelect')?.value || '';

    // 업종 값: 버튼 클릭 선택 > 검색창 입력(엔터/포커스아웃)
    const inputVal = (document.getElementById('upjongSearch')?.value || '').trim();
    const upjongNm = (window.selectedUpjongName || inputVal || null);

    if (!sgg || !emd){ alert('지역을 선택해줘.'); return; }
    if (!upjongNm){ alert('업종 이름을 입력하거나 선택해줘.'); return; }

    // 지도 색칠 + 패널 표시
    colorOnlySelectedEmdByUpjong(emd, upjongNm);
    renderRiskPanel(emd, upjongNm);
}

/* ================= 지역 셀렉트 핸들러 ================= */
function onSggChange(){
    const sggNm = $('#sggSelect').val();
    $('#emdSelect').empty().append('<option value="">행정동</option>');

    // 지도 이동/하이라이트
    if (!isProgrammatic && sggNm){
        for (let i=0;i<sggPolygons.length;i++){
            const {properties, path} = sggPolygons[i];
            if (getSggName(properties) === sggNm){
                const center = centerOf(path);
                map.setLevel(7); map.panTo(center);
                if (currentPolygon){ currentPolygon.setMap(null); currentPolygon=null; }
                currentPolygon = new kakao.maps.Polygon({
                    map, path, strokeWeight:2, strokeColor:'#004c80', strokeOpacity:0.8, fillColor:'#00a0e9', fillOpacity:0.3
                });
                break;
            }
        }
    }

    // 행정동 리스트는 서버에서 받아오거나(권장) 클라이언트에서 필터링
    if (sggNm){
        // 서버 사용시:
        $.ajax({
            url: 'getEmdsBySggNm', // 서버에 맞춰 조정
            method:'GET',
            data:{ sgg: sggNm },
            success: function(rows){
                // rows: [{ emdNm }, ...]
                rows.forEach(d => $('#emdSelect').append($('<option>', { value: d.emdNm, text: d.emdNm })));
                // 지도 클릭으로 넘어온 자동 선택
                if (window.autoSelectedEmdNm){
                    const hit = window.autoSelectedEmdNm;
                    isProgrammatic = true;
                    $('#emdSelect').val(hit).trigger('change');
                    isProgrammatic = false;
                    window.autoSelectedEmdNm = null;
                }
            },
            error: function(){ console.warn('행정동 목록 조회 실패. 필요하면 클라이언트 필터로 대체해줘.'); }
        });
    }
}

function onEmdChange(){
    const emdNm = $('#emdSelect').val();
    if (!emdNm) return;

    for (let i=0; i < emdPolygons.length; i++){
        const {properties, path, emdCd} = emdPolygons[i];
        if (getEmdName(properties) === emdNm){
            if (!isProgrammatic){
                const center = centerOf(path);
                map.setLevel(5); map.panTo(center);
                if (currentPolygon){ currentPolygon.setMap(null); }
                currentPolygon = new kakao.maps.Polygon({
                    map,
                    path,
                    strokeWeight:2,
                    strokeColor:'#004c80',
                    strokeOpacity:0.8,
                    fillColor:'#00a0e9',
                    fillOpacity:0.3
                });
            }

            if (emdCd) {
                fetchEmdInfo(emdCd);
            }

            break;
        }
    }
}

// 주석: /emd/info 호출부 URL 절대경로로 수정
function fetchEmdInfo(adminDongCode) {
    if (!adminDongCode) return;
    $.ajax({
        url: '/usr/dataset/emd/info',
        method: 'GET',
        data: { adminDongCode },
        success: function (rows) {
            if (!rows || rows.length === 0) { updatePanel(null); return; }
            updatePanel(rows[0]);
        },
        error: function (xhr) {
            console.error('emd/info 호출 실패', xhr.status, xhr.responseText);
            updatePanel(null);
        }
    });
}

// 패널 업데이트
function updatePanel(row) {
    if (!row) {
        $('#panel-updated-at').text('기준분기: -');
        $('#emdName').text('행정동을 선택해 주세요');
        $('#floatingPopulation').text('-');
        $('#sales-per-capita-fp').text('-');
        $('#recent-period-fp').text('-');
        return;
    }

    // 기준분기
    $('#panel-updated-at').text('기준분기: ' + (row.baseYearQuarterCode || '-'));
    // 행정동 이름
    $('#emdName').text(row.adminDongName || '-');
    // 유동인구
    $('#floatingPopulation').text(formatPeople(row.floatingPopulation));
    // 당월 매출 추정
    $('#sales-per-capita-fp').text(formatKrw(row.totalSalesAmount));
    // 최근 분기
    $('#recent-period-fp').text(row.baseYearQuarterCode || '-');
}

// 숫자 포맷
function formatPeople(v) {
    const n = Number(v);
    if (!Number.isFinite(n) || n <= 0) return "–";
    if (n >= 100_000_000) {                // 1억명 이상 → 억명
        return (n / 100_000_000).toFixed(1).replace(/\.0$/, "") + "억명";
    }
    if (n >= 10_000) {                     // 1만명 이상 → 만명
        return (n / 10_000).toFixed(1).replace(/\.0$/, "") + "만명";
    }
    return n.toLocaleString() + "명";
}

function formatKrw(v) {
    const n = Number(v);
    if (!Number.isFinite(n) || n <= 0) return "–";
    if (n >= 100_000_000) {                // 1억원 이상 → 억원
        return (n / 100_000_000).toFixed(1).replace(/\.0$/, "") + "억원";
    }
    if (n >= 10_000) {                     // 1만원 이상 → 만원(정수)
        return Math.round(n / 10_000).toLocaleString() + "만원";
    }
    return n.toLocaleString() + "원";
}

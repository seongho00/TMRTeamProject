let map;
let currentPolygon = null;
let emdPolygons = [], emdOverlayList = [];
let sggPolygons = [], sggOverlayList = [];
let currentLevel = 6;
let isProgrammatic = false;

// 낮음 → 높음 (아주 연한 노랑 → 진한 주황)
const PALETTE_5 = {
    0: "#FFF7BC",  // 매우 낮음
    1: "#FEE391",  // 낮음
    2: "#FEC44F",  // 보통
    3: "#FE9929",  // 높음
    4: "#D95F0E"   // 매우 높음
};
const COLOR_DEFAULT = "#D3D3D3";

window.selectedUpjongName = null;
window.autoSelectedEmd = null;

// ===== 공용 유틸 =====
const fmtNum = v => (v == null || isNaN(v)) ? "-" : Number(v).toLocaleString();
const fmtPct = v => (v == null || isNaN(v)) ? "-" : (Number(v)*100).toFixed(1)+"%";
const norm = s => (s||"").toString().trim().replace(/\s+/g,"");

// ===== 초기화 =====
document.addEventListener("DOMContentLoaded", () => {
    kakao.maps.load(() => {
        map = new kakao.maps.Map(document.getElementById('map'), {
            center: new kakao.maps.LatLng(37.5665, 126.9780),
            level: 6
        });

        Promise.all([
            // ★ 위험도 병합본 GeoJSON 사용
            loadPolygons("/Seoul_risk.geojson", emdPolygons, emdOverlayList, "#e45c2f", "ADSTRD_NM"),
            loadPolygons("/Seoul_sggs.geojson", sggPolygons, sggOverlayList, "#e45c2f", "SIGUNGU_NM")
        ]).then(updatePolygonsByZoom);

        kakao.maps.event.addListener(map, 'zoom_changed', () => {
            currentLevel = map.getLevel();
            updatePolygonsByZoom();
        });

        kakao.maps.event.addListener(map, 'click', evt => handleMapClick(evt.latLng));
    });

    // 시군구 선택 → 행정동 로드 + 지도 이동
    $('#sggSelect').on('change', onSggChange);

    // 행정동 선택 → 지도 이동 + 강조
    $('#emdSelect').on('change', onEmdChange);

    // 대분류 클릭 → 중분류 목록
    $(document).on("click", ".major-item", onMajorClick);

    // 중분류 클릭 → 소분류 목록
    $(document).on("click", ".middle-item", onMiddleClick);

    // 소분류 클릭 → 입력 채우기 + 즉시 색칠/패널
    $(document).on("click", ".minor-item", onMinorClick);

    // 업종 입력 자동검색 (원하면 보여주기)
    $('.upjongInput').on('compositionend', () => handleSearch($('.upjongInput').val().trim()))
        .on('keydown', e => {
            if (e.keyCode===8 || e.keyCode===46) {
                setTimeout(()=>handleSearch($('.upjongInput').val().trim()), 10);
            }
        });
});

// ===== 지도/도형 =====
function loadPolygons(url, container, overlayList, color, nameKey){
    return fetch(url).then(res => res.json()).then(geojson => {
        geojson.features.forEach(feature => {
            const g = feature.geometry;
            const p = feature.properties;

            const multi = (g.type === "Polygon") ? [g.coordinates] : g.coordinates;
            multi.forEach(poly => {
                const coords = poly[0];
                const path = coords.map(c => new kakao.maps.LatLng(c[1], c[0]));

                const guide = new kakao.maps.Polygon({ path, strokeWeight:2, strokeColor:color, strokeOpacity:0.5, strokeStyle:"dash", fillOpacity:0 });

                const center = (()=>{
                    const lat = path.reduce((s,pt)=>s+pt.getLat(),0)/path.length;
                    const lng = path.reduce((s,pt)=>s+pt.getLng(),0)/path.length;
                    return new kakao.maps.LatLng(lat,lng);
                })();

                const displayName = p[nameKey] || p['행정동_명'] || p['ADSTRD_NM'] || p['SIGUNGU_NM'] || '';
                const overlayContent = document.createElement('div');
                overlayContent.innerText = displayName;
                overlayContent.style.cssText = "background:#fff;border:1px solid #444;padding:3px 6px;font-size:13px;";
                const overlay = new kakao.maps.CustomOverlay({content:overlayContent, position:center, yAnchor:1, zIndex:3});

                container.push({path, properties:p, guide, overlay});
                overlayList.push(overlay);
            });
        });
    });
}

// 이름 추출(여러 키를 안전하게 커버)
function getEmdName(props){
    return props?.ADSTRD_NM || props?.행정동_명 || props?.adm_nm || null;
}
function getSggName(props){
    return props?.SIGUNGU_NM || props?.시군구명 || props?.sgg_nm || null;
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

function handleMapClick(latLng){
    const targets = currentLevel >= 7 ? sggPolygons : emdPolygons;
    for (let i=0;i<targets.length;i++){
        const {path, properties} = targets[i];
        if (!isPointInPolygon(latLng, path)) continue;

        const sggName = getSggName(properties);     // 변경
        const emdName = getEmdName(properties);     // 변경

        if (sggName){
            isProgrammatic = true;
            $('#sggSelect').val(sggName).trigger('change');
            isProgrammatic = false;
        }

        if (emdName){
            // 클릭 지점이 포함된 시군구를 찾아 이름 얻기 (fallback)
            let matchedSggName = null;
            for (let j=0;j<sggPolygons.length;j++){
                const sgg = sggPolygons[j];
                if (isPointInPolygon(latLng, sgg.path)){
                    matchedSggName = getSggName(sgg.properties); // 변경
                    break;
                }
            }
            if (matchedSggName){
                window.autoSelectedEmd = emdName;
                isProgrammatic = true;
                $('#sggSelect').val(matchedSggName).trigger('change');
                isProgrammatic = false;
            }
        }

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

// ===== 업종별 위험도 검색/표시 =====
function getRiskRecordForUpjong(props, upjongKeyword){
    const items = Array.isArray(props?.업종별_위험도) ? props.업종별_위험도 : [];
    if (!upjongKeyword) return null;
    const key = norm(upjongKeyword);
    return items.find(it => norm(it["서비스_업종_코드_명"]) === key)
        || items.find(it => norm(it["서비스_업종_코드_명"]).includes(key))
        || null;
}

function renderRiskPanel(emdName, upjongName){
    const $panel = document.getElementById("riskResult");
    if (!$panel) return;

    const target = emdPolygons.find(({properties}) => properties?.ADSTRD_NM === emdName);
    if (!target){ $panel.innerHTML = "<div>선택한 행정동을 찾을 수 없어요.</div>"; return; }

    const rec = getRiskRecordForUpjong(target.properties, upjongName);
    if (!rec){
        $panel.innerHTML = `
      <div><b>행정동:</b> ${emdName}</div>
      <div><b>업종:</b> ${upjongName||"-"}</div>
      <div style="color:#666;margin-top:6px;">해당 업종의 위험도 정보가 없어요.</div>`;
        return;
    }

    const color = PALETTE_5[Number(rec["예측_위험도"])] || COLOR_DEFAULT;
    const label = rec["예측_위험도_라벨"] ?? "-";
    const stage = rec["위험도_단계"] ?? "-";
    const score = fmtNum(rec["위험도_점수"]);
    const conf  = fmtPct(rec["예측_신뢰도"]);

    $panel.innerHTML = `
    <div style="line-height:1.5;">
      <div><b>행정동:</b> ${emdName}</div>
      <div><b>업종:</b> ${rec["서비스_업종_코드_명"] ?? upjongName ?? "-"}</div>
      <div><b>위험도:</b>
        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${color};vertical-align:middle;margin-right:6px;"></span>
        ${label} (${stage})
      </div>
      <div><b>위험도 점수:</b> ${score}</div>
      <div><b>예측 신뢰도:</b> ${conf}</div>
    </div>`;
}

// ===== 지역/업종 검색 버튼 =====
function searchInfoByRegionAndUpjong(){
    const sgg = $('#sggSelect').val();
    const emd = $('#emdSelect').val();
    const upjong = $('.upjongInput').val().trim();

    if (!sgg || !emd){ alert('지역을 선택해주세요.'); return; }
    if (!upjong){ alert('업종을 선택해주세요.'); return; }

    // 클릭 할 때만 지도 반영 + 패널 표시
    colorOnlySelectedEmdByUpjong(emd, upjong);
    const box = document.getElementById('riskResult');
    if (box) box.classList.remove('hidden');
    renderRiskPanel(emd, upjong);

    // 필요 시 서버 조회 (선택)
    $.ajax({
        url: 'searchInfoByRegionAndUpjong',
        method: 'GET',
        data: { sgg, emd, upjong },
        success: function(resp){ console.log('서버 응답:', resp); },
        error: function(){ console.error('데이터 로드 실패'); }
    });
}

// ===== 이벤트 핸들러 =====
function onSggChange(){
    const sgg = $(this).val();
    $('#emdSelect').empty().append('<option value="">행정동</option>');

    if (!isProgrammatic){
        for (let i=0;i<sggPolygons.length;i++){
            const {properties, path} = sggPolygons[i];
            if (properties.SIGUNGU_NM === sgg){
                const center = centerOf(path);
                map.setLevel(7); map.panTo(center);
                if (currentPolygon){ currentPolygon.setMap(null); currentPolygon=null; }
                currentPolygon = new kakao.maps.Polygon({ map, path, strokeWeight:2, strokeColor:'#004c80', strokeOpacity:0.8, fillColor:'#00a0e9', fillOpacity:0.3 });
                break;
            }
        }
    }

    if (sgg){
        $.ajax({
            url: 'getEmdsBySggNm',
            method:'GET',
            data:{ sgg },
            success: function(rows){
                rows.forEach(d => $('#emdSelect').append($('<option>', {value:d.emdNm, text:d.emdNm})));

                if (window.autoSelectedEmd){
                    const norm = s => (s||'').toString().trim();
                    let pick = null;
                    $('#emdSelect option').each(function(){
                        if (norm($(this).text()) === norm(window.autoSelectedEmd)){ pick = $(this).val(); return false; }
                    });
                    if (pick){ $('#emdSelect').val(pick).trigger('change'); }
                    else { console.warn('autoSelectedEmd 옵션을 못찾음:', window.autoSelectedEmd); }
                    window.autoSelectedEmd = null;
                    isProgrammatic = false;
                }
            },
            error: function(){ alert('행정동 정보를 가져오는데 실패했습니다.'); }
        });
    }
}

function onEmdChange(){
    const emd = $(this).val();
    if (!emd) return;

    for (let i=0; i < emdPolygons.length; i++){
        const {properties, path} = emdPolygons[i];
        if (getEmdName(properties) === emd){
            if (!isProgrammatic){
                const center = centerOf(path);
                map.setLevel(5); map.panTo(center);
                if (currentPolygon){ currentPolygon.setMap(null); }
                currentPolygon = new kakao.maps.Polygon({ map, path, strokeWeight:2, strokeColor:'#004c80', strokeOpacity:0.8, fillColor:'#00a0e9', fillOpacity:0.3 });
            }
            break;
        }
    }
}

function onMajorClick(){
    const majorCd = $(this).data("majorcd");
    $.ajax({
        url: "getMiddleCategories",
        method: "GET",
        data: { majorCd },
        success: function(rows){
            let liHTML = rows.map(it => `<li class="middle-item h-12 w-full text-xl text-center cursor-pointer hover:bg-gray-100" data-middlecd="${it.middleCd}">${it.middleNm}</li>`).join("");
            $(".middleSelector ul").html(liHTML); $(".middleSelector").removeClass('hidden');
        },
        error: function(){ alert("중분류 데이터를 불러오는데 실패했습니다."); }
    });
}

function onMiddleClick(){
    const middleCd = $(this).data("middlecd");
    $.ajax({
        url: "getMinorCategories",
        method: "GET",
        data: { middleCd },
        success: function(rows){
            let liHTML = rows.map(it => `<li class="minor-item h-12 w-full text-xl text-center cursor-pointer hover:bg-gray-100" data-minorcd="${it.minorCd}">${it.minorNm}</li>`).join("");
            $(".minorSelector ul").html(liHTML); $(".minorSelector").removeClass('hidden');
        },
        error: function(){ alert("소분류 데이터를 불러오는데 실패했습니다."); }
    });
}

function onMinorClick(){
    const minorCd = $(this).data("minorcd");
    $.ajax({
        url: "getUpjongCodeByMinorCd",
        method: "GET",
        data: { minorCd },
        success: function(upjongCode){
            const minorNm = upjongCode.minorNm;
            $('.upjongInput').val(`${upjongCode.majorNm} > ${upjongCode.middleNm} > ${minorNm}`);

            // 색/패널은 '확인' 때만 -> 선택만 저장 후 초기화
            window.selectedUpjongName = minorNm;
            if (typeof clearEmdColors === 'function') clearEmdColors();
            const box = document.getElementById("riskResult");
            if (box) box.classList.add("hidden");

            $('.middleSelector').addClass('hidden');
            $('.minorSelector').addClass('hidden');
        },
        error: function(){ alert("데이터를 불러오는 데 실패했습니다."); }
    });
}

// ===== 기타 =====
function centerOf(path){
    const lat = path.reduce((s,p)=>s+p.getLat(),0)/path.length;
    const lng = path.reduce((s,p)=>s+p.getLng(),0)/path.length;
    return new kakao.maps.LatLng(lat,lng);
}

function handleSearch(keyword){
    if (!keyword){ $('#autocompleteList').empty().addClass('hidden'); return; }
    $.ajax({
        url: 'searchUpjong',
        method: 'GET',
        data: { keyword },
        success: function(list){ console.log('auto:', list); /* 필요시 자동완성 UI 구성 */ },
        error: function(){ console.log('업종 검색 실패'); }
    });
}

// 1) 전체 색 제거
function clearEmdColors() {
    emdPolygons.forEach(({ guide }) => {
        guide.setOptions({ fillOpacity: 0, strokeOpacity: 0.5 });
    });
}

// 2) 선택 동만 업종 위험도 색칠
function colorOnlySelectedEmdByUpjong(emdName, upjongName) {
    clearEmdColors();

    // 대상 동 찾기
    const target = emdPolygons.find(({ properties }) => {
        const name = properties?.ADSTRD_NM || properties?.행정동_명 || properties?.adm_nm;
        return name === emdName;
    });
    if (!target) return;

    // 위험도 레코드
    const rec = getRiskRecordForUpjong(target.properties, upjongName);
    const color = (rec && Number.isFinite(rec["예측_위험도"]))
        ? (PALETTE_5[Number(rec["예측_위험도"])] || COLOR_DEFAULT)
        : COLOR_DEFAULT;

    // 해당 동만 채우기
    target.guide.setOptions({ fillColor: color, fillOpacity: (color===COLOR_DEFAULT?0.2:0.6), strokeOpacity: 0.8 });
}

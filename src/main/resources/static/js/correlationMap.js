/*************************************************
 * [코드 기반으로 전면 전환]
 * - 비교/선택/검색: "코드" 사용 (SIGUNGU_CD, ADSTRD_CD)
 * - UI 표시: "이름" 사용 (SIGUNGU_NM, ADSTRD_NM)
 * - select의 option: value=코드, text=이름
 *************************************************/

let map;
let currentPolygon = null;
let emdPolygons = [], emdOverlayList = [];
let sggPolygons = [], sggOverlayList = [];
let currentLevel = 6;
let isProgrammatic = false;

// 낮음 → 높음
const PALETTE_5 = {
    0: "#FFF7BC",
    1: "#FEE391",
    2: "#FEC44F",
    3: "#FE9929",
    4: "#D95F0E"
};
const COLOR_DEFAULT = "#D3D3D3";

// 업종/자동선택
window.selectedUpjongName = null;
// 자동 선택은 "행정동 코드"로 저장
window.autoSelectedEmdCd = null;

// ===== 공용 유틸 =====
const fmtNum = v => (v == null || isNaN(v)) ? "-" : Number(v).toLocaleString();
const fmtPct = v => (v == null || isNaN(v)) ? "-" : (Number(v)*100).toFixed(1)+"%";
const norm = s => (s||"").toString().trim().replace(/\s+/g,"");

// 코드/이름 추출 유틸 (여러 키 대응)
function getEmdCode(p){ return p?.ADSTRD_CD || p?.행정동_코드 || p?.adm_cd || null; }
function getEmdName(p){ return p?.ADSTRD_NM || p?.행정동_명 || p?.adm_nm || null; }
function getSggCode(p){ return p?.SIGUNGU_CD || p?.시군구코드 || p?.sgg_cd || null; }
function getSggName(p){ return p?.SIGUNGU_NM || p?.시군구명 || p?.sgg_nm || null; }

// ===== 초기화 =====
document.addEventListener("DOMContentLoaded", () => {
    kakao.maps.load(() => {
        map = new kakao.maps.Map(document.getElementById('map'), {
            center: new kakao.maps.LatLng(37.5665, 126.9780),
            level: 6
        });

        Promise.all([
            loadPolygons("/Seoul_risk.geojson", emdPolygons, emdOverlayList, "#e45c2f", "ADSTRD_NM"),
            loadPolygons("/Seoul_sggs.geojson", sggPolygons, sggOverlayList, "#e45c2f", "SIGUNGU_NM")
        ]).then(updatePolygonsByZoom);

        kakao.maps.event.addListener(map, 'zoom_changed', () => {
            currentLevel = map.getLevel();
            updatePolygonsByZoom();
        });

        kakao.maps.event.addListener(map, 'click', evt => handleMapClick(evt.latLng));
    });

    // select는 value=코드, text=이름
    $('#sggSelect').on('change', onSggChange);
    $('#emdSelect').on('change', onEmdChange);

    // 카테고리 이벤트
    $(document).on("click", ".major-item", onMajorClick);
    $(document).on("click", ".middle-item", onMiddleClick);
    $(document).on("click", ".minor-item", onMinorClick);

    // 업종 자동검색
    $('.upjongInput')
        .on('compositionend', () => handleSearch($('.upjongInput').val().trim()))
        .on('keydown', e => { if (e.keyCode===8 || e.keyCode===46) setTimeout(()=>handleSearch($('.upjongInput').val().trim()), 10); });
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

                const guide = new kakao.maps.Polygon({
                    path, strokeWeight:2, strokeColor:color, strokeOpacity:0.5, strokeStyle:"dash", fillOpacity:0
                });

                // 라벨은 이름 표시
                const center = (()=> {
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

function centerOf(path){
    const lat = path.reduce((s,p)=>s+p.getLat(),0)/path.length;
    const lng = path.reduce((s,p)=>s+p.getLng(),0)/path.length;
    return new kakao.maps.LatLng(lat,lng);
}

// ===== 지도 클릭: select에 "코드" 주입 =====
function handleMapClick(latLng){
    const targets = currentLevel >= 7 ? sggPolygons : emdPolygons;
    for (let i=0;i<targets.length;i++){
        const {path, properties} = targets[i];
        if (!isPointInPolygon(latLng, path)) continue;

        const sggCd = getSggCode(properties);
        const emdCd = getEmdCode(properties);

        if (sggCd){
            isProgrammatic = true;
            $('#sggSelect').val(sggCd).trigger('change'); // value=코드
            isProgrammatic = false;
        }

        if (emdCd){
            // 클릭 지점이 포함된 시군구 코드 재확인
            let matchedSggCd = null;
            for (let j=0;j<sggPolygons.length;j++){
                const sgg = sggPolygons[j];
                if (isPointInPolygon(latLng, sgg.path)){
                    matchedSggCd = getSggCode(sgg.properties);
                    break;
                }
            }
            if (matchedSggCd){
                window.autoSelectedEmdCd = emdCd; // 자동 선택도 코드로
                isProgrammatic = true;
                $('#sggSelect').val(matchedSggCd).trigger('change');
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

// ===== 업종별 위험도 =====
function getRiskRecordForUpjong(props, upjongKeyword){
    const items = Array.isArray(props?.업종별_위험도) ? props.업종별_위험도 : [];
    if (!upjongKeyword) return null;
    const key = norm(upjongKeyword);
    return items.find(it => norm(it["서비스_업종_코드_명"]) === key)
        || items.find(it => norm(it["서비스_업종_코드_명"]).includes(key))
        || null;
}

// 패널은 코드로 찾고, 표시만 이름으로
function renderRiskPanel(emdCd, upjongName){
    const $panel = document.getElementById("riskResult");
    if (!$panel) return;

    const target = emdPolygons.find(({properties}) => getEmdCode(properties) === emdCd);
    if (!target){ $panel.innerHTML = "<div>선택한 행정동을 찾을 수 없어요.</div>"; return; }

    const emdNm = getEmdName(target.properties);
    const rec = getRiskRecordForUpjong(target.properties, upjongName);
    if (!rec){
        $panel.innerHTML = `
          <div><b>행정동:</b> ${emdNm ?? "-"}</div>
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
      <div><b>행정동:</b> ${emdNm ?? "-"}</div>
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
    const sggCd = $('#sggSelect').val(); // 코드
    const emdCd = $('#emdSelect').val(); // 코드
    const upjong = ($('.upjongInput').val() || '').trim();

    if (!sggCd || !emdCd){ alert('지역을 선택해주세요.'); return; }
    if (!upjong){ alert('업종을 선택해주세요.'); return; }

    // 지도 반영 + 패널
    colorOnlySelectedEmdByUpjong(emdCd, upjong);
    const box = document.getElementById('riskResult');
    if (box) box.classList.remove('hidden');
    renderRiskPanel(emdCd, upjong);

    // 서버도 코드로 전달
    $.ajax({
        url: 'searchInfoByRegionAndUpjong',
        method: 'GET',
        data: { sggCd, emdCd, upjong },
        success: function(resp){ console.log('서버 응답:', resp); },
        error: function(jq){ console.error('데이터 로드 실패', jq?.status, jq?.responseText); }
    });
}

// ===== 이벤트 핸들러 =====
function onSggChange(){
    const sggCd = $('#sggSelect').val(); // 코드
    $('#emdSelect').empty().append('<option value="">행정동</option>');

    // 시군구 폴리곤 하이라이트 (코드 비교)
    if (!isProgrammatic && sggCd){
        for (let i=0;i<sggPolygons.length;i++){
            const {properties, path} = sggPolygons[i];
            if (getSggCode(properties) === sggCd){
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

    // 시군구 코드로 행정동 목록 조회, option value=emdCd, text=emdNm
    if (sggCd){
        $.ajax({
            url: 'getEmdsBySggCd', // 코드 기반 API 권장
            method:'GET',
            data:{ sggCd },
            success: function(rows){
                // rows: [{ emdCd, emdNm }, ...]
                rows.forEach(d => $('#emdSelect').append(
                    $('<option>', { value: d.emdCd, text: d.emdNm })
                ));

                // 지도 클릭에서 넘어온 자동 선택(코드)
                if (window.autoSelectedEmdCd){
                    let hit = null;
                    $('#emdSelect option').each(function(){
                        if ($(this).val() === window.autoSelectedEmdCd){ hit = window.autoSelectedEmdCd; return false; }
                    });
                    if (hit){
                        isProgrammatic = true;
                        $('#emdSelect').val(hit).trigger('change');
                        isProgrammatic = false;
                    } else {
                        console.warn('autoSelectedEmdCd 코드 매칭 실패:', window.autoSelectedEmdCd);
                    }
                    window.autoSelectedEmdCd = null;
                }
            },
            error: function(){ alert('행정동 정보를 가져오는데 실패했습니다.'); }
        });
    }
}

function onEmdChange(){
    const emdCd = $('#emdSelect').val(); // 코드
    if (!emdCd) return;

    for (let i=0; i < emdPolygons.length; i++){
        const {properties, path} = emdPolygons[i];
        if (getEmdCode(properties) === emdCd){
            if (!isProgrammatic){
                const center = centerOf(path);
                map.setLevel(5); map.panTo(center);
                if (currentPolygon){ currentPolygon.setMap(null); }
                currentPolygon = new kakao.maps.Polygon({
                    map, path, strokeWeight:2, strokeColor:'#004c80', strokeOpacity:0.8, fillColor:'#00a0e9', fillOpacity:0.3
                });
            }
            break;
        }
    }
}

// ===== 카테고리 =====
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

            // 선택만 저장 후 초기화
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
function handleSearch(keyword){
    if (!keyword){ $('#autocompleteList').empty().addClass('hidden'); return; }
    $.ajax({
        url: 'searchUpjong',
        method: 'GET',
        data: { keyword },
        success: function(list){ console.log('auto:', list); /* 자동완성 UI 필요 시 구현 */ },
        error: function(){ console.log('업종 검색 실패'); }
    });
}

// 1) 전체 색 제거
function clearEmdColors() {
    emdPolygons.forEach(({ guide }) => {
        guide.setOptions({ fillOpacity: 0, strokeOpacity: 0.5 });
    });
}

// 2) 선택 동만 업종 위험도 색칠 (파라미터=emdCd)
function colorOnlySelectedEmdByUpjong(emdCd, upjongName) {
    clearEmdColors();

    // 대상 동: 코드로 찾기
    const target = emdPolygons.find(({ properties }) => getEmdCode(properties) === emdCd);
    if (!target) return;

    const rec = getRiskRecordForUpjong(target.properties, upjongName);
    const color = (rec && Number.isFinite(rec["예측_위험도"]))
        ? (PALETTE_5[Number(rec["예측_위험도"])] || COLOR_DEFAULT)
        : COLOR_DEFAULT;

    target.guide.setOptions({ fillColor: color, fillOpacity: (color===COLOR_DEFAULT?0.2:0.6), strokeOpacity: 0.8 });
}

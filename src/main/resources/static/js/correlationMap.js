// correlationMap.js
// 업종 UI가 안 뜨는 문제 + 위험도 패널 미표시 문제 해결본
// - UPJONGS 로드 → 업종 리스트/검색 즉시 렌더
// - 업종은 "이름" 기준 검색/선택, 필요시 입력값에서 (코드)도 보조 파싱
// - 행정동은 select 값(이름)으로 찾고, 내부 처리에선 코드/이름 모두 대응
// 참고 원본: 사용자 제공 파일들  :contentReference[oaicite:1]{index=1}  :contentReference[oaicite:2]{index=2}

/* ================= 전역/상태 ================= */
let map;
let currentPolygon = null;
let emdPolygons = [], emdOverlayList = [];
let sggPolygons = [], sggOverlayList = [];
let currentLevel = 6;
let isProgrammatic = false;

// 팔레트
const PALETTE_5 = {0:"#FFF7BC",1:"#FEE391",2:"#FEC44F",3:"#FE9929",4:"#D95F0E"};
const COLOR_DEFAULT = "#D3D3D3";

// 업종 선택 상태
window.selectedUpjongName = null; // 이름 우선
window.selectedUpjongCd   = null; // 코드 보조
window.autoSelectedEmdCd  = null; // 지도 클릭으로 자동 지정

/* ================= 유틸 ================= */
// 숫자/퍼센트 포맷
const fmtNum = v => (v == null || isNaN(v)) ? "-" : Number(v).toLocaleString();
const fmtPct = v => (v == null || isNaN(v)) ? "-" : (Number(v)*100).toFixed(1)+"%";

// 공백 제거 후 소문자
const norm = s => (s||"").toString().trim().replace(/\s+/g,"").toLowerCase();

// 입력에서 "(코드)" 추출
function parseUpjongCdFromInput(inputValue){
    const m = /\(([^)]+)\)\s*$/.exec(inputValue || "");
    return m ? m[1].trim() : null;
}

// GeoJSON 키 호환
function getEmdCode(p){ return p?.ADSTRD_CD || p?.행정동_코드 || p?.adm_cd || null; }
function getEmdName(p){ return p?.ADSTRD_NM || p?.행정동_명 || p?.adm_nm || null; }
function getSggCode(p){ return p?.SIGUNGU_CD || p?.시군구_코드 || p?.sgg_cd || null; }
function getSggName(p){ return p?.SIGUNGU_NM || p?.시군구_명 || p?.sgg_nm || null; }

// 위험도 항목 키 추출
function pickCodeField(obj){
    return obj?.["서비스_업종_코드"] ?? obj?.["업종_코드"] ?? obj?.["코드"] ?? obj?.["upjongCd"] ?? null;
}
function pickNameField(obj){
    return obj?.["서비스_업종_코드_명"] ?? obj?.["업종명"] ?? obj?.["이름"] ?? obj?.["upjongNm"] ?? null;
}

/* ================= 초기화 ================= */
document.addEventListener("DOMContentLoaded", () => {
    // 1) 맵 초기화
    kakao.maps.load(() => {
        map = new kakao.maps.Map(document.getElementById('map'), {
            center: new kakao.maps.LatLng(37.5665, 126.9780),
            level: 6
        });

        Promise.all([
            loadPolygons("/Seoul_risk.geojson", emdPolygons, emdOverlayList, "#004C80", "ADSTRD_NM"),
            loadPolygons("/Seoul_sggs.geojson", sggPolygons, sggOverlayList, "#007580", "SIGUNGU_NM")
        ]).then(updatePolygonsByZoom);

        kakao.maps.event.addListener(map, 'zoom_changed', () => {
            currentLevel = map.getLevel();
            updatePolygonsByZoom();
        });

        kakao.maps.event.addListener(map, 'click', evt => handleMapClick(evt.latLng));
    });

    // 2) 지역 셀렉트 바인딩
    $(document).on('change', '#sggSelect', onSggChange);
    $(document).on('change', '#emdSelect', onEmdChange);

    // 3) 업종 소스/피커 초기화 (이게 안되면 리스트/자동완성이 안 뜸)
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

/* ================= 지도 클릭 → select 동기화 ================= */
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

/* ================= 업종 위험도 (이름 기준) ================= */
// 업종 이름으로 레코드 찾기
function getRiskRecordForUpjongByName(props, upjongName){
    const items = Array.isArray(props?.업종별_위험도) ? props.업종별_위험도 : [];
    if (!items.length || !upjongName) return null;
    const key = norm(upjongName);
    return items.find(it => norm(pickNameField(it)||"") === key)
        || items.find(it => norm(pickNameField(it)||"").includes(key))
        || null;
}

// emd 값(코드 또는 이름)으로 polygon 찾기
function findEmdByValue(v){
    return emdPolygons.find(({properties}) =>
        getEmdCode(properties) === v || getEmdName(properties) === v
    );
}

/* ================= 결과 패널 ================= */
function renderRiskPanel(emdValue, upjongName){
    const $panel = document.getElementById("riskResult");
    if (!$panel) return;

    const target = findEmdByValue(emdValue);
    if (!target){
        $panel.classList.remove('hidden');
        $panel.textContent = "선택한 행정동을 찾을 수 없어요.";
        return;
    }

    const emdNm = getEmdName(target.properties);
    const rec   = getRiskRecordForUpjongByName(target.properties, upjongName);

    if (!rec){
        $panel.classList.remove('hidden');
        $panel.innerHTML = `
      <div><b>행정동:</b> ${emdNm ?? "-"}</div>
      <div><b>업종:</b> ${upjongName || "-"}</div>
      <div style="color:#666;margin-top:6px;">해당 업종의 위험도 정보가 없어요.</div>`;
        return;
    }

    const color = PALETTE_5[Number(rec["예측_위험도"])] || COLOR_DEFAULT;
    const label = rec["예측_위험도_라벨"] ?? "-";
    const stage = rec["위험도_단계"] ?? "-";
    const score = fmtNum(rec["위험도_점수"]);
    const conf  = fmtPct(rec["예측_신뢰도"]);

    $panel.classList.remove('hidden');
    $panel.innerHTML = `
    <div style="line-height:1.5;">
      <div><b>행정동:</b> ${emdNm ?? "-"}</div>
      <div><b>업종:</b> ${upjongName ?? "-"}</div>
      <div><b>위험도:</b>
        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${color};vertical-align:middle;margin-right:6px;"></span>
        ${label} (${stage})
      </div>
      <div><b>위험도 점수:</b> ${score}</div>
      <div><b>예측 신뢰도:</b> ${conf}</div>
    </div>`;
}

/* ================= 확인 버튼 ================= */
function searchInfoByRegionAndUpjong(){
    const sgg = document.getElementById('sggSelect')?.value || '';
    const emd = document.getElementById('emdSelect')?.value || '';
    const inputVal = (document.getElementById('upjongSearch')?.value || '').trim();

    // 업종 이름 우선 결정
    const upjongNm = window.selectedUpjongName || inputVal || null;

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
        const {properties, path} = emdPolygons[i];
        if (getEmdName(properties) === emdNm){
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

/* ================= 색칠(이름 기반) ================= */
function clearEmdColors() {
    emdPolygons.forEach(({ guide }) => {
        guide.setOptions({ fillOpacity: 0, strokeOpacity: 0.5 });
    });
}
function colorOnlySelectedEmdByUpjong(emdValue, upjongName) {
    clearEmdColors();
    const target = findEmdByValue(emdValue);
    if (!target) return;

    const rec = getRiskRecordForUpjongByName(target.properties, upjongName);
    const color = (rec && Number.isFinite(rec?.["예측_위험도"]))
        ? (PALETTE_5[Number(rec["예측_위험도"])] || COLOR_DEFAULT)
        : COLOR_DEFAULT;

    target.guide.setOptions({
        fillColor: color,
        fillOpacity: (color===COLOR_DEFAULT?0.2:0.6),
        strokeOpacity: 0.8
    });
}

/* ================= 업종 소스/피커 ================= */
async function initUpjongSource(){
    try {
        // 백엔드가 제공: [{upjongCd, upjongNm}, ...]
        const res = await fetch('/usr/map/api/upjong');
        const json = await res.json();
        window.UPJONGS = Array.isArray(json) ? json : [];
    } catch(e) {
        // 폴백 데이터
        window.UPJONGS = [
            {upjongCd:'CS100001', upjongNm:'한식음식점'},
            {upjongCd:'CS100010', upjongNm:'커피-음료'},
            {upjongCd:'CS100007', upjongNm:'치킨전문점'},
            {upjongCd:'CS200028', upjongNm:'미용실'},
            {upjongCd:'CS300002', upjongNm:'편의점'},
        ];
    }
    initUpjongPicker();
}

function initUpjongPicker(){
    const $groups = document.getElementById('upjongGroups');
    const $list   = document.getElementById('upjongList');
    const $search = document.getElementById('upjongSearch');
    const $drop   = document.getElementById('upjongSearchDrop');

    // 최초 렌더
    renderList('all','');

    // 탭 클릭
    $groups?.addEventListener('click', (e)=>{
        const btn = e.target.closest('button[data-group]');
        if(!btn) return;
        [...$groups.querySelectorAll('.chip')].forEach(b=>b.classList.remove('active'));
        btn.classList.add('active');
        renderList(btn.dataset.group, $search?.value?.trim() || '');
    });

    // 검색 자동완성
    let tId = null;
    $search?.addEventListener('input', (e)=>{
        clearTimeout(tId);
        tId = setTimeout(()=>{
            const q = e.target.value.trim();
            if(!q){
                $drop?.classList.add('hidden');
                const active = document.querySelector('#upjongGroups .active')?.dataset.group || 'all';
                renderList(active, '');
                return;
            }
            const hits = filterBy('all', q).slice(0,20);
            if ($drop){
                $drop.innerHTML = hits.map(it => `
          <button type="button" class="w-full text-left px-3 py-2 hover:bg-gray-50"
                  data-cd="${it.upjongCd}" data-nm="${it.upjongNm}">
            <span class="text-gray-500 mr-2">${hl(it.upjongCd, q)}</span>${hl(it.upjongNm, q)}
          </button>
        `).join('');
                $drop.classList.toggle('hidden', hits.length===0);
            }
        }, 120);
    });

    // 자동완성 선택
    $drop?.addEventListener('click', (e)=>{
        const b = e.target.closest('button[data-cd]');
        if(!b) return;
        pick({upjongCd:b.dataset.cd, upjongNm:b.dataset.nm});
        $drop.classList.add('hidden');
    });

    // 리스트 선택
    $list?.addEventListener('click', (e)=>{
        const b = e.target.closest('button[data-cd]');
        if(!b) return;
        pick({upjongCd:b.dataset.cd, upjongNm:b.dataset.nm});
    });

    // 선택 공용
    function pick(item){
        const ui = document.querySelector('.upjongInput:not(.hidden)') || document.querySelector('.upjongInput');
        if (ui) ui.value = `${item.upjongNm} (${item.upjongCd})`; // 입력창에 이름(코드) 표시
        window.selectedUpjongName = item.upjongNm;
        window.selectedUpjongCd   = item.upjongCd;

        const box = document.getElementById('riskResult');
        if (box) box.classList.add('hidden');
        if (typeof clearEmdColors === 'function') clearEmdColors();
    }

    // 리스트 렌더
    function renderList(group, query){
        const data = filterBy(group, query);
        if ($list){
            $list.innerHTML = data.map(it => `
        <button type="button" class="upjong-btn" data-cd="${it.upjongCd}" data-nm="${it.upjongNm}">
          <div class="text-xs text-gray-500">${it.upjongCd}</div>
          <div>${hl(it.upjongNm, query)}</div>
        </button>
      `).join('') || `<div class="text-gray-500 col-span-2">결과가 없습니다.</div>`;
        }
    }

    // 필터(이름 우선)
    function filterBy(group, query){
        const q = norm(query);
        const src = Array.isArray(window.UPJONGS) ? window.UPJONGS : [];
        return src.filter(it=>{
            const cd = String(it.upjongCd||'');
            const nm = String(it.upjongNm||'');
            const inGroup = group==='all' ? true : cd.startsWith(group);
            if(!inGroup) return false;
            if(!q) return true;
            return norm(nm).includes(q) || cd.toLowerCase().includes(q.toLowerCase());
        });
    }
}

/* ================= 하이라이트 유틸 ================= */
function hl(text, q){
    if(!q) return text;
    const t = text.toString();
    const i = t.toLowerCase().indexOf(q.toLowerCase());
    if(i<0) return t;
    return t.substring(0,i) + `<span class="hit">${t.substring(i, i+q.length)}</span>` + t.substring(i+q.length);
}

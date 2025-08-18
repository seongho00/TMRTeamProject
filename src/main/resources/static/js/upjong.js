window.UPJONGS = window.UPJONGS || [];

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const res = await fetch('/usr/map/api/upjong'); // 엔드포인트 맞춰주세요
        window.UPJONGS = await res.json();
    } catch(e) {
        // 실패시 최소 동작을 위한 예시 데이터
        window.UPJONGS = [
            {upjongCd:'CS100001', upjongNm:'한식음식점'},
            {upjongCd:'CS100002', upjongNm:'중식음식점'},
            {upjongCd:'CS100003', upjongNm:'일식음식점'},
            {upjongCd:'CS100004', upjongNm:'양식음식점'},
            {upjongCd:'CS100005', upjongNm:'제과점'},
            {upjongCd:'CS100006', upjongNm:'패스트푸드점'},
            {upjongCd:'CS100007', upjongNm:'치킨전문점'},
            {upjongCd:'CS100008', upjongNm:'분식전문점'},
            {upjongCd:'CS100009', upjongNm:'호프-간이주점'},
            {upjongCd:'CS100010', upjongNm:'커피-음료'},
            {upjongCd:'CS200001', upjongNm:'일반교습학원'},
            {upjongCd:'CS200002', upjongNm:'외국어학원'},
            {upjongCd:'CS200003', upjongNm:'예술학원'},
            {upjongCd:'CS200005', upjongNm:'스포츠 강습'},
            {upjongCd:'CS200006', upjongNm:'일반의원'},
            {upjongCd:'CS200007', upjongNm:'치과의원'},
            {upjongCd:'CS200008', upjongNm:'한의원'},
            {upjongCd:'CS200016', upjongNm:'당구장'},
            {upjongCd:'CS200017', upjongNm:'골프연습장'},
            {upjongCd:'CS200019', upjongNm:'PC방'},
            {upjongCd:'CS200024', upjongNm:'스포츠클럽'},
            {upjongCd:'CS200025', upjongNm:'자동차수리'},
            {upjongCd:'CS200026', upjongNm:'자동차미용'},
            {upjongCd:'CS200028', upjongNm:'미용실'},
            {upjongCd:'CS200029', upjongNm:'네일숍'},
            {upjongCd:'CS200030', upjongNm:'피부관리실'},
            {upjongCd:'CS200031', upjongNm:'세탁소'},
            {upjongCd:'CS200032', upjongNm:'가전제품수리'},
            {upjongCd:'CS200033', upjongNm:'부동산중개업'},
            {upjongCd:'CS200034', upjongNm:'여관'},
            {upjongCd:'CS200036', upjongNm:'고시원'},
            {upjongCd:'CS200037', upjongNm:'노래방'},
            {upjongCd:'CS300001', upjongNm:'슈퍼마켓'},
            {upjongCd:'CS300002', upjongNm:'편의점'},
            {upjongCd:'CS300003', upjongNm:'컴퓨터및주변장치판매'},
            {upjongCd:'CS300004', upjongNm:'핸드폰'},
            {upjongCd:'CS300006', upjongNm:'미곡판매'},
            {upjongCd:'CS300007', upjongNm:'육류판매'},
            {upjongCd:'CS300008', upjongNm:'수산물판매'},
            {upjongCd:'CS300009', upjongNm:'청과상'},
            {upjongCd:'CS300010', upjongNm:'반찬가게'},
            {upjongCd:'CS300011', upjongNm:'일반의류'},
            {upjongCd:'CS300014', upjongNm:'신발'},
            {upjongCd:'CS300015', upjongNm:'가방'},
            {upjongCd:'CS300016', upjongNm:'안경'},
            {upjongCd:'CS300017', upjongNm:'시계및귀금속'},
            {upjongCd:'CS300018', upjongNm:'의약품'},
            {upjongCd:'CS300019', upjongNm:'의료기기'},
            {upjongCd:'CS300020', upjongNm:'서적'},
            {upjongCd:'CS300021', upjongNm:'문구'},
            {upjongCd:'CS300022', upjongNm:'화장품'},
            {upjongCd:'CS300024', upjongNm:'운동/경기용품'},
            {upjongCd:'CS300025', upjongNm:'자전거 및 기타운송장비'},
            {upjongCd:'CS300026', upjongNm:'완구'},
            {upjongCd:'CS300027', upjongNm:'섬유제품'},
            {upjongCd:'CS300028', upjongNm:'화초'},
            {upjongCd:'CS300029', upjongNm:'애완동물'},
            {upjongCd:'CS300031', upjongNm:'가구'},
            {upjongCd:'CS300032', upjongNm:'가전제품'},
            {upjongCd:'CS300033', upjongNm:'철물점'},
            {upjongCd:'CS300035', upjongNm:'인테리어'},
            {upjongCd:'CS300036', upjongNm:'조명용품'},
            {upjongCd:'CS300043', upjongNm:'전자상거래업'}
        ];
    }
    initUpjongPicker();
});

function initUpjongPicker(){
    const $groups = document.getElementById('upjongGroups');
    const $list   = document.getElementById('upjongList');
    const $search = document.getElementById('upjongSearch');
    const $drop   = document.getElementById('upjongSearchDrop');

    // 기본 렌더
    renderList('all','');

    // 그룹 탭 클릭
    $groups.addEventListener('click', (e)=>{
        const btn = e.target.closest('button[data-group]');
        if(!btn) return;
        [...$groups.querySelectorAll('.chip')].forEach(b=>b.classList.remove('active'));
        btn.classList.add('active');
        renderList(btn.dataset.group, $search.value.trim());
    });

    // 검색 드롭다운
    let tId = null;
    $search.addEventListener('input', (e)=>{
        clearTimeout(tId);
        tId = setTimeout(()=>{
            const q = e.target.value.trim();
            if(!q){
                $drop.classList.add('hidden');
                // 현재 선택된 탭 기준 다시 렌더
                const active = document.querySelector('#upjongGroups .active')?.dataset.group || 'all';
                renderList(active, '');
                return;
            }
            // 상위 20개 제안
            const hits = filterBy('all', q).slice(0,20);
            $drop.innerHTML = hits.map(it => `
        <button type="button" class="w-full text-left px-3 py-2 hover:bg-gray-50"
                data-cd="${it.upjongCd}" data-nm="${it.upjongNm}">
          <span class="text-gray-500 mr-2">${hl(it.upjongCd, q)}</span>${hl(it.upjongNm, q)}
        </button>
      `).join('');
            $drop.classList.toggle('hidden', hits.length===0);
        }, 120);
    });

    // 드롭다운 항목 선택
    $drop.addEventListener('click', (e)=>{
        const b = e.target.closest('button[data-cd]');
        if(!b) return;
        pick({upjongCd:b.dataset.cd, upjongNm:b.dataset.nm});
        $drop.classList.add('hidden');
    });

    // 리스트 클릭
    $list.addEventListener('click', (e)=>{
        const b = e.target.closest('button[data-cd]');
        if(!b) return;
        pick({upjongCd:b.dataset.cd, upjongNm:b.dataset.nm});
    });

    function pick(item){
        // 화면의 표시용 input 채우기
        const ui = document.querySelector('.upjongInput:not(.hidden)') || document.querySelector('.upjongInput');
        if (ui) ui.value = `${item.upjongNm} (${item.upjongCd})`;

        // 선택만 저장
        window.selectedUpjongName = item.upjongNm;

        // 패널은 감춰둠
        const box = document.getElementById('riskResult');
        if (box) box.classList.add('hidden');

        // 지도를 초기 상태로 (색 제거)
        if (typeof clearEmdColors === 'function') clearEmdColors();
    }

    function renderList(group, query){
        const data = filterBy(group, query);
        $list.innerHTML = data.map(it => `
      <button type="button" class="upjong-btn" data-cd="${it.upjongCd}" data-nm="${it.upjongNm}">
        <div class="text-xs text-gray-500">${it.upjongCd}</div>
        <div>${hl(it.upjongNm, query)}</div>
      </button>
    `).join('') || `<div class="text-gray-500 col-span-2">결과가 없습니다.</div>`;
    }

    function filterBy(group, query){
        const q = norm(query);
        return UPJONGS.filter(it=>{
            const inGroup =
                group==='all' ? true :
                    it.upjongCd.startsWith(group); // CS100/CS200/CS300
            if(!inGroup) return false;
            if(!q) return true;
            return norm(it.upjongNm).includes(q) || it.upjongCd.toLowerCase().includes(q.toLowerCase());
        });
    }
}

// helper
function norm(s){ return (s||'').toString().replace(/\s+/g,'').toLowerCase(); }
function hl(text, q){
    if(!q) return text;
    const t = text.toString();
    const i = t.toLowerCase().indexOf(q.toLowerCase());
    if(i<0) return t;
    return t.substring(0,i) + `<span class="hit">${t.substring(i, i+q.length)}</span>` + t.substring(i+q.length);
}

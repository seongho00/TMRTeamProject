let map;
let currentPolygon = null;
let emdPolygons = [], emdOverlayList = [];
let sggPolygons = [], sggOverlayList = [];
let currentLevel = 6;
let isProgrammatic = false;
let selectedSgg = null;
let selectedEmd = null;

// GeoJSON 키 호환
function getEmdCode(p) {
    return p?.ADSTRD_CD || p?.행정동_코드 || p?.adm_cd || null;
}

function getEmdName(p) {
    return p?.ADSTRD_NM || p?.행정동_명 || p?.adm_nm || null;
}

function getSggName(p) {
    return p?.SIGUNGU_NM || p?.시군구_명 || p?.sgg_nm || null;
}

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
function loadPolygons(url, container, overlayList, color, nameKey) {
    return fetch(url).then(res => res.json()).then(geojson => {
        geojson.features.forEach(feature => {
            const g = feature.geometry;
            const p = feature.properties;

            const multi = (g.type === "Polygon") ? [g.coordinates] : g.coordinates;
            multi.forEach(poly => {
                const coords = poly[0];
                const path = coords.map(c => new kakao.maps.LatLng(c[1], c[0]));
                const guide = new kakao.maps.Polygon({
                    path, strokeWeight: 2, strokeColor: color, strokeOpacity: 0.5, strokeStyle: "dash", fillOpacity: 0
                });

                // 라벨용 중앙 좌표
                const center = (() => {
                    const lat = path.reduce((s, pt) => s + pt.getLat(), 0) / path.length;
                    const lng = path.reduce((s, pt) => s + pt.getLng(), 0) / path.length;
                    return new kakao.maps.LatLng(lat, lng);
                })();

                const overlayContent = document.createElement('div');
                overlayContent.innerText = p[nameKey] || getEmdName(p) || getSggName(p) || '';
                overlayContent.style.cssText = "background:#fff;border:1px solid #444;padding:3px 6px;font-size:13px;";
                const overlay = new kakao.maps.CustomOverlay({
                    content: overlayContent,
                    position: center,
                    yAnchor: 1,
                    zIndex: 3
                });

                container.push({
                    path,
                    properties: p,
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

function updatePolygonsByZoom() {
    const isSGG = currentLevel >= 7;
    const show = isSGG ? sggPolygons : emdPolygons;
    const hide = isSGG ? emdPolygons : sggPolygons;
    const showOv = isSGG ? sggOverlayList : emdOverlayList;
    const hideOv = isSGG ? emdOverlayList : sggOverlayList;

    if (currentPolygon) {
        currentPolygon.setMap(null);
        currentPolygon = null;
    }
    hide.forEach(p => p.guide.setMap(null));
    show.forEach(p => p.guide.setMap(map));
    hideOv.forEach(o => o.setMap(null));
    showOv.forEach(o => o.setMap(map));
}

/* ================= 폴리곤 헬퍼 ================= */
function isPointInPolygon(latLng, path) {
    let x = latLng.getLng(), y = latLng.getLat(), inside = false;
    for (let i = 0, j = path.length - 1; i < path.length; j = i++) {
        let xi = path[i].getLng(), yi = path[i].getLat();
        let xj = path[j].getLng(), yj = path[j].getLat();
        let intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / ((yj - yi) || 1e-10) + xi);
        if (intersect) inside = !inside;
    }
    return inside;
}

function isSamePath(path1, path2) {
    if (!path1 || !path2 || path1.length !== path2.length) return false;
    for (let i = 0; i < path1.length; i++) {
        if (path1[i].getLat().toFixed(6) !== path2[i].getLat().toFixed(6) ||
            path1[i].getLng().toFixed(6) !== path2[i].getLng().toFixed(6)) return false;
    }
    return true;
}

function centerOf(path) {
    const lat = path.reduce((s, p) => s + p.getLat(), 0) / path.length;
    const lng = path.reduce((s, p) => s + p.getLng(), 0) / path.length;
    return new kakao.maps.LatLng(lat, lng);
}

/* ================= 지도 클릭 -> select 동기화 ================= */
function handleMapClick(latLng) {
    const targets = currentLevel >= 7 ? sggPolygons : emdPolygons;
    for (let i = 0; i < targets.length; i++) {
        const {path, properties} = targets[i];
        if (!isPointInPolygon(latLng, path)) continue;

        const sggNm = getSggName(properties);
        const emdNm = getEmdName(properties);
        if (sggNm) selectedSgg = sggNm;
        if (emdNm) selectedEmd = emdNm;

        let matchedSggNm = null;

        // 시군구 select 설정
        if (sggNm) {
            isProgrammatic = true;
            $('#sggSelect').val(sggNm).trigger('change');
            isProgrammatic = false;
        }

        // 행정동 클릭이면, 포함 시군구 찾아서 emd 자동선택
        if (emdNm) {
            for (let j = 0; j < sggPolygons.length; j++) {
                const sgg = sggPolygons[j];
                if (isPointInPolygon(latLng, sgg.path)) {
                    matchedSggNm = getSggName(sgg.properties);
                    break;
                }
            }
            if (matchedSggNm) {
                window.autoSelectedEmdNm = emdNm; // 이름 저장
                isProgrammatic = true;
                $('#sggSelect').val(matchedSggNm).trigger('change');
                isProgrammatic = false;
            }
        }

        // 하이라이트 토글
        if (currentPolygon && isSamePath(currentPolygon.getPath(), path)) {
            currentPolygon.setMap(null);
            currentPolygon = null;
            return;
        }
        if (currentPolygon) currentPolygon.setMap(null);
        currentPolygon = new kakao.maps.Polygon({
            map,
            path,
            strokeWeight: 2,
            strokeColor: '#004c80',
            strokeOpacity: 0.8,
            fillColor: '#00a0e9',
            fillOpacity: 0.3
        });
        break;
    }
}

/* ================= 확인 버튼 ================= */
function searchInfoByRegionAndUpjong() {
    // 지역 값
    const sgg = document.getElementById('sggSelect')?.value || '';
    const emd = document.getElementById('emdSelect')?.value || '';

    // 업종 값: 버튼 클릭 선택 > 검색창 입력(엔터/포커스아웃)
    const inputVal = (document.getElementById('upjongSearch')?.value || '').trim();
    const upjongNm = (window.selectedUpjongName || inputVal || null);

    if (!sgg || !emd) {
        alert('지역을 선택해줘.');
        return;
    }
    if (!upjongNm) {
        alert('업종 이름을 입력하거나 선택해줘.');
        return;
    }

    // 지도 색칠 + 패널 표시
    colorOnlySelectedEmdByUpjong(emd, upjongNm);
    renderRiskPanel(emd, upjongNm);
}

/* ================= 지역 셀렉트 핸들러 ================= */
function onSggChange() {
    const sggNm = $('#sggSelect').val();
    selectedSgg = sggNm; // 🔥 선택된 시군구 저장
    $('#emdSelect').empty().append('<option value="">행정동</option>');

    // 지도 이동/하이라이트
    if (!isProgrammatic && sggNm) {
        for (let i = 0; i < sggPolygons.length; i++) {
            const {properties, path} = sggPolygons[i];
            if (getSggName(properties) === sggNm) {
                const center = centerOf(path);
                map.setLevel(7);
                map.panTo(center);
                if (currentPolygon) {
                    currentPolygon.setMap(null);
                    currentPolygon = null;
                }
                currentPolygon = new kakao.maps.Polygon({
                    map,
                    path,
                    strokeWeight: 2,
                    strokeColor: '#004c80',
                    strokeOpacity: 0.8,
                    fillColor: '#00a0e9',
                    fillOpacity: 0.3
                });
                break;
            }
        }
    }

    // 행정동 리스트는 서버에서 받아오거나(권장) 클라이언트에서 필터링
    if (sggNm) {
        // 서버 사용시:
        $.ajax({
            url: 'getEmdsBySggNm', // 서버에 맞춰 조정
            method: 'GET',
            data: {sgg: sggNm},
            success: function (rows) {
                // rows: [{ emdNm }, ...]
                rows.forEach(d => $('#emdSelect').append($('<option>', {value: d.emdNm, text: d.emdNm})));
                // 지도 클릭으로 넘어온 자동 선택
                if (window.autoSelectedEmdNm) {
                    const hit = window.autoSelectedEmdNm;
                    isProgrammatic = true;
                    $('#emdSelect').val(hit).trigger('change');
                    isProgrammatic = false;
                    window.autoSelectedEmdNm = null;
                }
            },
            error: function () {
                console.warn('행정동 목록 조회 실패. 필요하면 클라이언트 필터로 대체해줘.');
            }
        });
    }
}

function onEmdChange() {
    const emdNm = $('#emdSelect').val();
    if (!emdNm) return;
    selectedEmd = emdNm; // 🔥 선택된 행정동 저장

    for (let i = 0; i < emdPolygons.length; i++) {
        const {properties, path, emdCd} = emdPolygons[i];
        if (getEmdName(properties) === emdNm) {
            if (!isProgrammatic) {
                const center = centerOf(path);
                map.setLevel(5);
                map.panTo(center);
                if (currentPolygon) {
                    currentPolygon.setMap(null);
                }
                currentPolygon = new kakao.maps.Polygon({
                    map,
                    path,
                    strokeWeight: 2,
                    strokeColor: '#004c80',
                    strokeOpacity: 0.8,
                    fillColor: '#00a0e9',
                    fillOpacity: 0.3
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
        data: {adminDongCode},
        success: function (rows) {
            if (!rows || rows.length === 0) {
                updatePanel(null);
                return;
            }
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


function openReport() {
    const $report = $(".report");
    // 데이터 가져오기
    if (selectedSgg && selectedEmd) {
        $.ajax({
            url: "../dataset/getDataSetByAdminDong",
            method: "POST",
            data: {
                sgg: selectedSgg,
                emd: selectedEmd
            },
            success: function (data) {
                const currentData = data[data.length - 1];

                console.log(currentData);

                // 예: 특정 값 화면에 표시
                if (data) {


                    // 성별 데이터
                    const male = currentData.maleFloatingPopulation || 0;
                    const female = currentData.femaleFloatingPopulation || 0;
                    const genderTotal = male + female;

                    if (window.genderFloatingChart instanceof Chart) {
                        window.genderFloatingChart.destroy();
                    }

                    const genderCtx = document.getElementById("genderFloatingChart").getContext("2d");
                    window.genderFloatingChart = new Chart(genderCtx, {
                        type: "doughnut", // 또는 "pie"
                        data: {
                            labels: ["남성", "여성"],
                            datasets: [{
                                label: "성별 유동인구",
                                data: [male, female],
                                backgroundColor: [
                                    "rgba(59, 130, 246, 0.7)",   // 파랑: 남성
                                    "rgba(236, 72, 153, 0.7)"    // 분홍: 여성
                                ],
                                borderColor: [
                                    "rgba(59, 130, 246, 1)",
                                    "rgba(236, 72, 153, 1)"
                                ],
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: false,   // 자동 리사이즈 끔
                            maintainAspectRatio: false, // 가로세로 비율 고정 해제
                            plugins: {
                                title: {
                                    display: false,
                                },
                                tooltip: {
                                    callbacks: {
                                        label: (genderCtx) => {
                                            const total = male + female;
                                            const val = genderCtx.raw || 0;
                                            const percent = total ? ((val / total) * 100).toFixed(1) : 0;
                                            return `${genderCtx.label}: ${val.toLocaleString()}명 (${percent}%)`;
                                        }
                                    }
                                },
                                legend: {
                                    position: "bottom"
                                }
                            }
                        }
                    });


                    // ✅ 해석 div 채우기
                    const genderAnalysis = document.getElementById("genderPopulationAnalysis");
                    const malePercent = ((male / genderTotal) * 100).toFixed(1);
                    const femalePercent = ((female / genderTotal) * 100).toFixed(1);

                    const dominant = male > female ? "남성" : "여성";
                    const dominantPercent = male > female ? malePercent : femalePercent;

                    genderAnalysis.innerHTML = `
                       <div class="flex absolute -top-[20px] left-2 font-bold bg-red-500 text-white rounded-lg px-3 py-2">
                            <i class="fa-solid fa-chart-line"></i>
                            &nbsp;
                            <span>분석결과 해석</span>
                        </div>
                        <p>성별 유동인구는 
                           <span class="font-bold text-blue-500">남성 ${malePercent}%</span>, 
                           <span class="font-bold text-pink-500">여성 ${femalePercent}%</span>로 
                           <span class="font-bold text-red-500">${dominant} 유동인구가 더 많습니다.</span>
                        </p>
                        <p><span class="font-bold text-red-500">${dominant}</span> 소비층을 주요 타깃으로 한 업종·마케팅 전략에 유리합니다.</p>
                    `;


                    // 시간대별 그래프
                    const timeLabels = [
                        "00~06시", "06~11시", "11~14시",
                        "14~17시", "17~21시", "21~24시"
                    ];

                    const timeValues = [
                        currentData.time00to06FloatingPopulation,
                        currentData.time06to11FloatingPopulation,
                        currentData.time11to14FloatingPopulation,
                        currentData.time14to17FloatingPopulation,
                        currentData.time17to21FloatingPopulation,
                        currentData.time21to24FloatingPopulation
                    ];

                    // ✅ 합계 구하기
                    const timeTotal = timeValues.reduce((a, b) => a + b, 0);

                    // 퍼센트 변환
                    const timePercentValues = timeValues.map(v => timeTotal > 0 ? (v / timeTotal * 100) : 0);


                    // ✅ 최고값 찾기
                    const timeMaxValue = Math.max(...timePercentValues);
                    const timeMaxIndex = timePercentValues.indexOf(timeMaxValue);
                    const maxTimeLabel = timeLabels[timeMaxIndex];

                    const minTimeValue = Math.min(...timePercentValues);
                    const minTimeIndex = timePercentValues.indexOf(minTimeValue);
                    const minTimeLabel = timeLabels[minTimeIndex];


                    // ✅ 색상 배열 (최고값만 빨강 강조)
                    const timePointColors = timePercentValues.map((v, i) =>
                        i === timeMaxIndex ? "rgba(239, 68, 68, 1)" : "rgba(37, 99, 235, 1)"
                    );
                    const timeBgColors = timePercentValues.map((v, i) =>
                        i === timeMaxIndex ? "rgba(239, 68, 68, 0.6)" : "rgba(37, 99, 235, 0.3)"
                    );

                    // ✅ Y축 최대값 = 최고값 + 2 (최소 100 제한 제거)
                    const timeYMax = Math.ceil(timeMaxValue + 2);

                    // ✅ 기존 차트 있으면 안전하게 제거
                    if (timeSalesChart instanceof Chart) {
                        timeSalesChart.destroy();
                    }

                    // 새 차트 생성
                    const timeCtx = document.getElementById("timeSalesChart").getContext("2d");
                    window.timeSalesChart = new Chart(timeCtx, {
                        type: "line",
                        data: {
                            labels: timeLabels,
                            datasets: [{
                                label: "시간대별 유동인구 비율",
                                data: timePercentValues,
                                borderColor: "rgba(37, 99, 235, 1)",
                                backgroundColor: timeBgColors,
                                tension: 0,
                                fill: false,
                                pointRadius: 6,
                                pointBackgroundColor: timePointColors
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                title: {
                                    display: false,
                                    text: "📊 시간대별 유동인구 비율"
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function (context) {
                                            return context.dataset.label + ": "
                                                + context.raw.toFixed(1) + "%";
                                        }
                                    }
                                },
                                datalabels: {
                                    anchor: "end",
                                    align: "top",
                                    formatter: (value) => value.toFixed(1) + "%",
                                    color: (ctx) => ctx.raw === timeMaxValue ? "#e11d48" : "#000",
                                    font: {
                                        weight: "bold"
                                    }
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: timeYMax,  // 최고값 + 2%
                                    ticks: {
                                        callback: function (value) {
                                            return value + "%";
                                        }
                                    }
                                }
                            }
                        },
                        plugins: [ChartDataLabels]
                    });

                    // 요일별 그래프
                    const dayLabels = ["월", "화", "수", "목", "금", "토", "일"];
                    const dayValues = [
                        currentData.mondayFloatingPopulation,
                        currentData.tuesdayFloatingPopulation,
                        currentData.wednesdayFloatingPopulation,
                        currentData.thursdayFloatingPopulation,
                        currentData.fridayFloatingPopulation,
                        currentData.saturdayFloatingPopulation,
                        currentData.sundayFloatingPopulation
                    ];

                    // 합계 구하기
                    const total = dayValues.reduce((a, b) => a + b, 0);

                    // 퍼센트 값으로 변환
                    const percentValues = dayValues.map(v => total > 0 ? (v / total * 100) : 0);

                    // ✅ Y축 최대값 = 최고값 + 2 (최소 100 제한 제거)
                    const dayYMax = Math.ceil(timeMaxValue + 2);

                    // 기존 차트 제거
                    if (window.weeklyPopulationChart instanceof Chart) {
                        window.weeklyPopulationChart.destroy();
                    }

                    // 가장 큰 값 찾기
                    const maxValue = Math.max(...percentValues);
                    const maxIndex = percentValues.indexOf(maxValue);
                    const maxDay = dayLabels[maxIndex];

                    const minDayValue = Math.min(...percentValues);
                    const minDayIndex = percentValues.indexOf(minDayValue);
                    const minDayLabel = dayLabels[minDayIndex];


                    const backgroundColors = percentValues.map(v =>
                        v === maxValue ? "rgba(239, 68, 68, 0.8)" : "rgba(37, 99, 235, 0.7)"
                    );
                    const borderColors = percentValues.map(v =>
                        v === maxValue ? "rgba(220, 38, 38, 1)" : "rgba(37, 99, 235, 1)"
                    );


                    // Bar 차트 생성
                    const dayCtx = document.getElementById("weeklyPopulationChart").getContext("2d");
                    window.weeklyPopulationChart = new Chart(dayCtx, {
                        type: "bar",
                        data: {
                            labels: dayLabels,
                            datasets: [{
                                label: "요일별 유동인구",
                                data: percentValues,
                                backgroundColor: backgroundColors,  // 배열 적용
                                borderColor: borderColors,          // 배열 적용
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                title: {
                                    display: false,
                                    text: "📊 요일별 유동인구"
                                },
                                tooltip: {
                                    callbacks: {
                                        label: ctx => ctx.dataset.label + ": " + ctx.raw.toFixed(1) + "%"
                                    }
                                },
                                datalabels: {
                                    anchor: "end",
                                    align: "end",
                                    formatter: (value) => value.toFixed(1) + "%",
                                    color: (ctx) => {
                                        // 최고값은 흰 글씨로 표시, 나머지는 검정
                                        return ctx.raw === maxValue ? "#fff" : "#000";
                                    },
                                    font: {
                                        weight: "bold"
                                    }
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: dayYMax,
                                    ticks: {
                                        callback: v => v + "%"
                                    }
                                }
                            }
                        },
                        plugins: [ChartDataLabels]
                    });

                    // 해설 div 업데이트
                    const analysisDiv = document.getElementById("weeklyPopulationAnalysis");
                    analysisDiv.innerHTML = `
                        <div class="flex absolute -top-[20px] left-2 font-bold bg-red-500 text-white rounded-lg px-3 py-2">
                            <i class="fa-solid fa-chart-line"></i>
                            &nbsp;
                            <span>분석결과 해석</span>
                        </div>
                        <p><span class="font-bold text-red-500">${maxDay}요일</span> (${maxValue.toFixed(1)}%)과 
                        <span class="font-bold text-red-500">${maxTimeLabel}</span> (${timeMaxValue.toFixed(1)}%)에 
                        유동인구가 가장 많습니다.</p>
                    
                        <p>반대로 <span class="font-bold text-blue-500">${minDayLabel}요일</span> 
                        (${minDayValue.toFixed(1)}%)과 
                        <span class="font-bold text-blue-500">${minTimeLabel}</span> 
                        (${minTimeValue.toFixed(1)}%)에는 가장 적습니다.</p>
                    `;


                    const rawData = getRawData(currentData);

                    // visible 상태는 그대로 legend에서 관리
                    const visible = {resident: true, workplace: true, floating: true};
                    const newData = calculatePercentages(rawData, visible);

                    function getRawData(currentData) {
                        return {
                            resident: [
                                currentData.age10ResidentPopulation,
                                currentData.age20ResidentPopulation,
                                currentData.age30ResidentPopulation,
                                currentData.age40ResidentPopulation,
                                currentData.age50ResidentPopulation,
                                currentData.age60PlusResidentPopulation
                            ],
                            workplace: [
                                null,
                                currentData.age20WorkplacePopulation,
                                currentData.age30WorkplacePopulation,
                                currentData.age40WorkplacePopulation,
                                currentData.age50WorkplacePopulation,
                                currentData.age60PlusWorkplacePopulation
                            ],
                            floating: [
                                currentData.age10FloatingPopulation,
                                currentData.age20FloatingPopulation,
                                currentData.age30FloatingPopulation,
                                currentData.age40FloatingPopulation,
                                currentData.age50FloatingPopulation,
                                currentData.age60PlusFloatingPopulation
                            ]
                        };
                    }


                    let ageLabels = ["20대", "30대", "40대", "50대", "60대+"]; // 처음엔 10대 제외

                    function calculatePercentages(rawData, visible) {
                        const sum = (arr, skipFirst = false) =>
                            arr.reduce((a, b, i) => a + ((skipFirst && i === 0) ? 0 : (b || 0)), 0);

                        const totalResident = sum(rawData.resident, visible.workplace);
                        const totalWorkplace = sum(rawData.workplace, true);
                        const totalFloating = sum(rawData.floating, visible.workplace);

                        let result = {
                            resident: rawData.resident.map((v, i) =>
                                visible.resident && (visible.workplace && i === 0 ? false : true) && totalResident
                                    ? parseFloat(((v || 0) / totalResident * 100).toFixed(1))
                                    : null
                            ),
                            workplace: rawData.workplace.map((v, i) =>
                                visible.workplace && i > 0 && totalWorkplace
                                    ? parseFloat(((v || 0) / totalWorkplace * 100).toFixed(1))
                                    : null
                            ),
                            floating: rawData.floating.map((v, i) =>
                                visible.floating && (visible.workplace && i === 0 ? false : true) && totalFloating
                                    ? parseFloat(((v || 0) / totalFloating * 100).toFixed(1))
                                    : null
                            )
                        };

                        if (visible.workplace) {
                            result.resident = result.resident.slice(1);
                            result.workplace = result.workplace.slice(1);
                            result.floating = result.floating.slice(1);
                        }

                        return result;
                    }


                    if (window.populationByAgeChart instanceof Chart) {
                        // 재사용 업데이트
                        const c = window.populationByAgeChart;
                        c.data.datasets[0].data = newData.resident;
                        c.data.datasets[1].data = newData.workplace;
                        c.data.datasets[2].data = newData.floating;
                        c.data.labels = visible.workplace
                            ? ["20대", "30대", "40대", "50대", "60대+"]
                            : ["10대", "20대", "30대", "40대", "50대", "60대+"];
                        c.update();
                    } else {
                        const ctx = document.getElementById("populationByAgeChart").getContext("2d");
                        window.populationByAgeChart = new Chart(ctx, {
                            type: "bar",
                            data: {
                                labels: visible.workplace
                                    ? ["20대", "30대", "40대", "50대", "60대+"]
                                    : ["10대", "20대", "30대", "40대", "50대", "60대+"],
                                datasets: [
                                    {label: "상주", data: newData.resident, backgroundColor: "rgba(59,130,246,0.7)"},
                                    {label: "직장", data: newData.workplace, backgroundColor: "rgba(16,185,129,0.7)"},
                                    {label: "유동", data: newData.floating, backgroundColor: "rgba(239,68,68,0.7)"}
                                ]
                            },
                            options: {
                                plugins: {
                                    legend: {
                                        onClick: (e, legendItem, legend) => {
                                            const ci = legend.chart;
                                            const index = legendItem.datasetIndex;

                                            // 기본 토글 동작
                                            const meta = ci.getDatasetMeta(index);
                                            meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;

                                            // 현재 보임 상태 재계산
                                            const vis = {
                                                resident: !ci.getDatasetMeta(0).hidden,
                                                workplace: !ci.getDatasetMeta(1).hidden,
                                                floating: !ci.getDatasetMeta(2).hidden
                                            };

                                            // 라벨
                                            ci.data.labels = vis.workplace
                                                ? ["20대", "30대", "40대", "50대", "60대+"]
                                                : ["10대", "20대", "30대", "40대", "50대", "60대+"];

                                            // 🔧 2) 올바른 인자 전달
                                            const recalced = calculatePercentages(rawData, vis);

                                            ci.data.datasets[0].data = recalced.resident;
                                            ci.data.datasets[1].data = recalced.workplace;
                                            ci.data.datasets[2].data = recalced.floating;

                                            ci.update();
                                        }
                                    },
                                    tooltip: {
                                        callbacks: {
                                            label: (ageCtx) => {
                                                const val = ageCtx.raw;
                                                return val != null ? `${ageCtx.dataset.label}: ${val}%` : `${ageCtx.dataset.label}: 없음`;
                                            }
                                        }
                                    }
                                }
                            }
                        });
                    }


                    const ageLabelsByAnalyze = ["20대", "30대", "40대", "50대", "60대+"];

                    // ✅ 10대 제외한 데이터만 사용
                    const residentData = newData.resident;
                    const workplaceData = newData.workplace;
                    const floatingData = newData.floating;

                    // ✅ 각 그룹에서 최댓값 찾기
                    function getMaxGroup(dataArr, labels) {
                        let maxVal = -1;
                        let maxIndex = -1;
                        dataArr.forEach((v, i) => {
                            if (v != null && v > maxVal) {
                                maxVal = v;
                                maxIndex = i;
                            }
                        });
                        return { label: labels[maxIndex], value: maxVal };
                    }

                    const maxResident = getMaxGroup(residentData, ageLabelsByAnalyze);
                    const maxWorkplace = getMaxGroup(workplaceData, ageLabelsByAnalyze);
                    const maxFloating = getMaxGroup(floatingData, ageLabelsByAnalyze);

                    // ✅ 해설 문구 생성
                    let analysisHtml = `
                        <div class="flex absolute -top-[20px] left-2 font-bold bg-red-500 text-white rounded-lg px-3 py-2">
                            <i class="fa-solid fa-chart-line"></i>
                            &nbsp;
                            <span>분석결과 해석</span>
                        </div>
                        <p>상주인구는 <span class="font-bold text-blue-500">${maxResident.label} (${maxResident.value}%)</span>가 가장 많아 지역 내 안정적 수요를 이끕니다.</p>
                        <p>직장인구는 <span class="font-bold text-green-500">${maxWorkplace.label} (${maxWorkplace.value}%)</span>가 우세해 평일 소비 주도층으로 작용합니다.</p>
                        <p>유동인구는 <span class="font-bold text-red-500">${maxFloating.label} (${maxFloating.value}%)</span>가 두드러져 외부 방문 수요가 활발합니다.</p>
                        <p>따라서 <span class="font-bold text-red-600">${maxFloating.label}</span> 방문 수요, 
                           <span class="font-bold text-green-600">${maxWorkplace.label}</span> 직장 수요, 
                           <span class="font-bold text-blue-600">${maxResident.label}</span> 거주 수요가 공존하는 지역으로 평가됩니다.</p>
                    `;

                    document.getElementById("populationAnalysis").innerHTML = analysisHtml;


                    // DOM 업데이트
                    $report.removeClass("hidden"); // DOM에 표시
                    setTimeout(() => {
                        $report.removeClass("opacity-0 -translate-x-4");
                    }, 10); // 애니메이션 적용
                } else {
                    alert("데이터가 없습니다.");
                }
            },
            error: function (xhr, status, err) {
                console.error("❌ 서버 오류:", status, err);
                alert("데이터 조회 실패");
            }
        });
    }

}

function closeReport() {

    // 설명창 열기
    const $report = $(".report");
    $report.addClass("opacity-0 -translate-x-4"); // 살짝 오른쪽 이동 + 투명도 0
    setTimeout(() => {
        $report.addClass("hidden"); // 애니메이션 끝나고 완전히 숨김
    }, 300); // duration-300ms와 맞춤
}
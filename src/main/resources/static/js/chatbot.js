function toggleChatBotUI() {
    $(".chatbot").toggleClass('hidden');
}

function sendMessage() {
    let message = $("#chatbotText").val();
    const $chatBox = $("#chat-box");
    $.ajax({
        type: "POST",
        url: "sendMessage",
        data: {message: message},
        success: function (data) {

            // 행정동 필요한 로직인데 없을 때
            if (data.resultCode === "F-2") {
                // 안내 메시지 표시
                $chatBox.append(`<div class="bot-msg"><b>챗봇:</b>${data.msg}</div>`);
            }

            // 여러 개의 시군구가 있을 시
            if (data.resultCode === "F-3") {
                const candidates = data.data1;

                // 기존 표시 영역 비우기
                $("#candidateContainer").empty();

                // 안내 메시지 표시
                $("#candidateContainer").append(
                    `<p>${data.msg || "동 이름이 여러 구에 있어요. 정확한 위치를 선택하세요."}</p>`
                );

                // 후보 버튼 생성
                candidates.forEach(function (c) {
                    const label = [c.sidoNm, c.sggNm, c.emdNm ?? c.emd].filter(Boolean).join(" ");

                    $("<button>")
                        .text(label)
                        .addClass("candidate-btn")
                        .on("click", function () {
                            // 현재 success 스코프의 message는 바깥 변수라 혼동될 수 있으니 새로 구성
                            const newMessage = $("#chatbotText").val() + " " + c.sggNm;

                            // 입력창 업데이트 후 재호출
                            $("#chatbotText").val(newMessage);
                            $("#candidateContainer").empty();   // 후보 UI 정리
                            sendMessage();                      // ✅ 기존 함수 재사용
                        })
                        .appendTo("#candidateContainer");
                });
                return;
            }

            // 업종 선택을 해야할 시
            if (data.resultCode === "F-4") {
                const upjongs = data.data1;
                const message = data.data2;

                $chatBox.append(`<div class="bot-msg"><b>챗봇:</b>아래에서 업종을 선택하면 매출 데이터를 보여드릴게요.</div>`);

                let btnHtml = '<div class="grid grid-cols-2 gap-2 mt-2 max-h-64 overflow-y-auto pr-2">';
                upjongs.forEach(u => {
                    btnHtml += `<button
                          class="p-2 rounded-lg bg-blue-100 hover:bg-blue-200 candidate-upjong"
                          data-upjong="${u.upjongCd}">
                          ${u.upjongNm}
                        </button>`;
                });
                btnHtml += '</div>';

                $chatBox.append(btnHtml);

                // 버튼 클릭 이벤트 등록
                $(".candidate-upjong").on("click", function () {
                    const selectedCd = $(this).data("upjong");
                    const selectedNm = $(this).text();
                    $("#chatbotText").val(message + " " + selectedNm.trim()); // 입력창 갱신
                    sendMessage(); // 다시 서버로 요청
                });

                return;
            }

            const flaskResult = data.data1;
            const sido = flaskResult.sido;
            const sigungu = flaskResult.sigungu;
            const emd = flaskResult.emd;

            const regionText = [sido, sigungu, emd]
                .filter(val => val && val !== "")
                .join(" ");

            // 매출액 대답
            if (data.resultCode === "S-1") {
                const upjongCode = data.data2;
                const dataSets = data.data3;


                // 차트용 배열
                const labels = [];       // 분기 (20241, 20242 ...)
                const salesValues = [];  // 매출액

                dataSets.forEach(data => {
                    labels.push(data.baseYearQuarterCode);   // 또는 item.baseYearQuarterCode 같은 키
                    salesValues.push(data.monthlySalesAmount); // 매출액 컬럼명 맞게 수정
                });

                $chatBox.append(`<div class="bot-msg"><b>챗봇:</b> ${upjongCode.upjongNm}의 매출액 데이터입니다.</div>`);

                if (window.salesChart) {
                    window.salesChart.destroy();
                }
                // 차트 container 초기화 후 다시 추가
                $("#chartContainer").remove();
                $chatBox.append(`
                      <div id="chartContainer">
                          <canvas id="salesChart"></canvas>
                      </div>
                    `);

                // Chart.js (Line 차트 예시)
                const ctx = document.getElementById("salesChart").getContext("2d");

                new Chart(ctx, {
                    type: "bar", // 또는 "bar"
                    data: {
                        labels: labels,
                        datasets: [{
                            label: "분기별 매출액",
                            data: salesValues,
                            borderColor: "rgba(54, 162, 235, 1)",
                            backgroundColor: "rgba(54, 162, 235, 0.2)",
                            fill: true,
                            tension: 0.3
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function (value) {
                                        return (value / 100000000).toLocaleString() + " 억";
                                    }
                                }
                            }
                        }
                    }
                });

            }

            // 유동인구 대답
            if (data.resultCode === "S-2") {
                const dataSet = data.data2;
                const percentile = data.data3
                console.log(dataSet)

                // 성별 관련 설정
                const genderKor = flaskResult.gender === "male" ? "남성" : "여성";
                const genderValue = flaskResult.gender === "male" ? dataSet.maleFloatingPopulation : dataSet.femaleFloatingPopulation;

                // 나이대 관련 설정
                const convertAgeKey = (ageGroup) => {
                    if (!ageGroup) return null;
                    const baseKey = ageGroup.replace("age_", "age"); // age_20 → age20
                    return baseKey + "FloatingPopulation";           // age20 → age20FloatingPopulation
                };

                const ageGroupMap = {
                    "age_10": "10대",
                    "age_20": "20대",
                    "age_30": "30대",
                    "age_40": "40대",
                    "age_50": "50대",
                    "age_60": "60대"
                };

                const rawAgeGroup = flaskResult.ageGroup;         // 예: "age_20"
                const ageKor = ageGroupMap[rawAgeGroup];          // 예: "20대"
                const ageKey = convertAgeKey(rawAgeGroup);        // 예: "age20"
                const ageValue = dataSet?.[ageKey];     // 올바르게 접근


                if (flaskResult.gender === "" && flaskResult.ageGroup === "") {
                    // 성별도 없고, 나이대도 없을 때 → 전체 인구 출력
                    $chatBox.append(`<div class="bot-msg"><b>챗봇:</b> ${regionText}의 전체 유동인구는 ${dataSet.totalFloatingPopulation}명입니다.</div>`);
                    $chatBox.append(`
                          <div class="bot-msg">
                            <b>챗봇:</b> ${regionText}은(는) 서울 전체 지역 중 <b>상위 ${percentile}%</b>에 해당합니다 🚀
                          </div>
                        `);

                } else if (flaskResult.gender !== "" && flaskResult.ageGroup === "") {
                    // 성별만 있을 때
                    $chatBox.append(`<div class="bot-msg"><b>챗봇:</b> ${regionText}의 ${genderKor} 유동인구는 ${genderValue}명입니다.</div>`);
                    $chatBox.append(`
                          <div class="bot-msg">
                            <b>챗봇:</b> ${regionText}의 ${genderKor} 유동인구는 서울 전체 지역 중 <b>상위 ${percentile}%</b>에 해당합니다 🚀
                          </div>
                        `);
                } else if (flaskResult.gender === "" && flaskResult.ageGroup !== "") {
                    // 나이대만 있을 때

                    $chatBox.append(`<div class="bot-msg"><b>챗봇:</b> ${regionText}의 ${ageKor} 유동인구는 ${ageValue}명입니다.</div>`);
                    $chatBox.append(`
                          <div class="bot-msg">
                            <b>챗봇:</b> ${regionText}의 ${ageKor} 유동인구는 서울 전체 지역 중 <b>상위 ${percentile}%</b>에 해당합니다 🚀
                          </div>
                        `);
                } else {
                    // 성별 + 나이대 모두 있을 때 → 조합 데이터는 없으므로 따로 안내

                    $chatBox.append(`<div class="bot-msg"><b>챗봇:</b>"${regionText}의 ${ageKor} ${genderKor}"에 대한 정확한 인구수는 제공되지 않지만,<br>
                    각각의 통계는 다음과 같습니다 😊 <br>
                    👉 ${ageKor} 인구: ${ageValue}명<br>
                    👉 ${genderKor} 인구: ${genderValue}명</div>`);
                }

                // ===== Chart.js 추가 부분 =====
                // 기존 차트 제거
                if (window.populationChart) {
                    window.populationChart.destroy();
                }
                if (window.genderChart) {
                    window.genderChart.destroy();
                }

                // 차트 나올 container 설정

                $("#chartContainer").remove();
                $chatBox.append(`
                          <div id="chartContainer">
                              <canvas id="genderChart"></canvas>
                              <canvas id="populationChart"></canvas>
                          </div>
                        `);

                // ===== 1. 성별 원형 차트 =====
                const genderCtx = document.getElementById("genderChart").getContext("2d");
                window.genderChart = new Chart(genderCtx, {
                    type: "doughnut",   // pie 로도 가능
                    data: {
                        labels: ["남성", "여성"],
                        datasets: [{
                            label: regionText + " 성별 유동인구",
                            data: [
                                dataSet.maleFloatingPopulation,
                                dataSet.femaleFloatingPopulation
                            ],
                            backgroundColor: ["#36A2EB", "#FF6384"]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            title: {display: true, text: regionText + " 성별 유동인구"}
                        }
                    }
                });

                // ===== 2. 연령대 막대 차트 =====
                const ageCtx = document.getElementById("populationChart").getContext("2d");
                window.populationChart = new Chart(ageCtx, {
                    type: "bar",
                    data: {
                        labels: ["10대", "20대", "30대", "40대", "50대", "60대"],
                        datasets: [{
                            label: regionText + " 연령대별 유동인구",
                            data: [
                                dataSet.age10FloatingPopulation,
                                dataSet.age20FloatingPopulation,
                                dataSet.age30FloatingPopulation,
                                dataSet.age40FloatingPopulation,
                                dataSet.age50FloatingPopulation,
                                dataSet.age60PlusFloatingPopulation
                            ],
                            backgroundColor: "#4CAF50"
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {display: false},
                            title: {display: true, text: regionText + " 연령대별 유동인구"}
                        }
                    }
                });

            }


            // 위험도 데이터 출력 로직
            if (data.resultCode === "S-3") {
                const riskData = data.data2[0];
                // 위험도 단계 (1~5)
                const riskLevel = parseInt(riskData.riskLevel.replace("단계", ""), 10);
                const predictedRiskLabel = riskData.predictedRiskLabel;

                // 단계별 색상 정의
                function getRiskBadge(level) {
                    switch (level) {
                        case 1:
                            return `<span class="badge text-green-500">1단계 (안전)</span>`;
                        case 2:
                            return `<span class="badge text-yellow-400">2단계 (주의)</span>`;
                        case 3:
                            return `<span class="badge text-orange-500">3단계 (경계)</span>`;
                        case 4:
                            return `<span class="badge text-red-500">4단계 (위험)</span>`;
                        case 5:
                            return `<span class="badge text-red-800 font-bold animate-pulse">5단계 (매우 위험)</span>`;
                        default:
                            return `<span class="badge">정보 없음</span>`;
                    }
                }

                $chatBox.append(`<div class="bot-msg"><b>챗봇:</b>"${regionText}"의 윟머도 점수는 다음과 같습니다.<br>
                        👉 전체 업종 위험도 : ${riskData.risk100All}점<br>
                        👉 해당 업종 위험도 : ${riskData.risk100ByBiz}점<br>
                        👉 업종 위험도 단계 : ${getRiskBadge(riskLevel)}<br>
                        👉 예상 위험도 단계 : ${getRiskBadge(predictedRiskLabel)}</div>`);

            }

            // 청약 데이터 출력 로직
            if (data.resultCode === "S-4") {
                const lhSupplyInfos = data.data2;

                console.log(lhSupplyInfos);

                let tableHtml = `
                        <div class="bot-msg">
                            <b>챗봇:</b> 현재 모집 중인 청약 데이터 리스트입니다.<br><br>
                            <div class="overflow-x-auto">
                                <table class="table table-zebra table-bordered w-full border border-gray-300">
                                    <thead>
                                        <tr>
                                            <th>공고 이름</th>
                                            <th>지역</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                    `;

                lhSupplyInfos.forEach(lh => {
                    tableHtml += `
                            <tr>
                                <td class="border border-gray-300">
                                    <a href="/lh/${lh.id}" target="_blank" class="text-blue-600 hover:underline">
                                        ${lh.title}
                                    </a>
                                </td>
                                <td class="border border-gray-300">${lh.address.replace(/(특별시|광역시|특별자치시|특별자치도|도)/g, "") || "정보 없음"}</td>
                            </tr>
                        `;
                });

                tableHtml += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    `;

                $chatBox.append(tableHtml);
            }


            $("#chatbotText").val("");  // 입력창 비우기
            $chatBox.scrollTop($chatBox[0].scrollHeight); // 스크롤 하단으로
        }
        ,
        error: function () {
            $chatBox.append(`<div class="bot-msg"><b>챗봇:</b> 오류가 발생했습니다.</div>`);
        }
    });
}

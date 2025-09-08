import React, {useEffect, useState} from "react";
import {Bar, Line, Radar} from "react-chartjs-2";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from "chart.js";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

import {
    RadialLinearScale,
    PointElement,
    LineElement,
    Filler,
} from "chart.js";
import {X} from "lucide-react";

ChartJS.register(
    RadialLinearScale,
    PointElement,
    LineElement,
    Filler
);

const colorList = [
    "#4e79a7", // 파랑
    "#f28e2b", // 주황
    "#e15759", // 빨강
    "#76b7b2", // 청록
    "#59a14f", // 초록
    "#edc949", // 노랑
    "#af7aa1", // 보라
    "#ff9da7", // 핑크
];

const CompareChartPanel = ({infos, onClose}) => {
    const [fetchedData, setFetchedData] = useState([]);

    useEffect(() => {
        if (!infos || infos.length === 0) return;

        const fetchData = async () => {
            const results = await Promise.all(
                infos.map((info) =>
                    fetch(`http://localhost:8080/usr/commercialData/findByEmdCode?emdCode=${info.address}`)
                        .then((res) => res.json())
                        .then((data) => ({
                            name: info.name,
                            totalFloating: data.total,
                            totalWorkers: data.workingTotal,
                            dominantAge: Object.entries({
                                "10대": data.age10,
                                "20대": data.age20,
                                "30대": data.age30,
                                "40대": data.age40,
                                "50대": data.age50,
                                "60대 이상": data.age60plus,
                            }).sort((a, b) => b[1] - a[1])[0][0],

                            // ✅ 연령대별 유동인구
                            age10: data.age10,
                            age20: data.age20,
                            age30: data.age30,
                            age40: data.age40,
                            age50: data.age50,
                            age60plus: data.age60plus,

                            totalAge:
                                data.age10 +
                                data.age20 +
                                data.age30 +
                                data.age40 +
                                data.age50 +
                                data.age60plus,

                            // ✅ 요일별 유동인구
                            mondayFloatingPopulation: data.mondayFloatingPopulation,
                            tuesdayFloatingPopulation: data.tuesdayFloatingPopulation,
                            wednesdayFloatingPopulation: data.wednesdayFloatingPopulation,
                            thursdayFloatingPopulation: data.thursdayFloatingPopulation,
                            fridayFloatingPopulation: data.fridayFloatingPopulation,
                            saturdayFloatingPopulation: data.saturdayFloatingPopulation,
                            sundayFloatingPopulation: data.sundayFloatingPopulation,

                            // ✅ 시간대별 유동인구
                            floating00to06: data.floating00to06,
                            floating06to11: data.floating06to11,
                            floating11to14: data.floating11to14,
                            floating14to17: data.floating14to17,
                            floating17to21: data.floating17to21,
                            floating21to24: data.floating21to24,

                        }))
                        .catch((err) => {
                            console.error("❌ 데이터 로딩 실패:", info.address, err);
                            return null;
                        })
                )
            );

            // null 필터링
            setFetchedData(results.filter(Boolean));

        };

        fetchData();
    }, [infos]);

    if (!fetchedData || fetchedData.length === 0) return null;


    /* 연령대별 유동인구 */
    const ageLabels = ["10대", "20대", "30대", "40대", "50대", "60대 이상"];

    const ageChartData = {
        labels: ageLabels,
        datasets: fetchedData.map((data, idx) => {
            const total =
                data.age10 +
                data.age20 +
                data.age30 +
                data.age40 +
                data.age50 +
                data.age60plus;

            return {
                label: data.name,
                data: [
                    ((data.age10 / total) * 100).toFixed(2),
                    ((data.age20 / total) * 100).toFixed(2),
                    ((data.age30 / total) * 100).toFixed(2),
                    ((data.age40 / total) * 100).toFixed(2),
                    ((data.age50 / total) * 100).toFixed(2),
                    ((data.age60plus / total) * 100).toFixed(2),
                ],
                backgroundColor: colorList[idx % colorList.length],
            };
        }),
    };

    const ageChartOptions = {
        responsive: true,
        plugins: {
            title: {display: true, text: "연령대별 유동인구 비교"},
            legend: {position: "top"},
            tooltip: {
                callbacks: {
                    label: (ctx) => `${ctx.dataset.label}: ${ctx.formattedValue}%`,
                },
            },
        },
        scales: {
            y: {beginAtZero: true},
            x: {stacked: false},
        },
    };



    const ageRadarChartOptions = {
        responsive: true,
        plugins: {
            title: {display: true, text: "연령대별 유동인구 비율 비교 (Radar)"},
            legend: {position: "top"},
            tooltip: {
                callbacks: {
                    label: (ctx) => `${ctx.dataset.label}: ${ctx.formattedValue}%`,
                },
            },
        },
        scales: {
            r: {
                suggestedMin: 0,
                suggestedMax: 40,
                ticks: {
                    callback: (val) => `${val}%`,
                },
            },
        },
    };

    /* 연령대별 유동인구 - Stacked Bar Chart 코드 */
    const ageStackedBarLabels = infos.map((info) => info.name); // 지역 이름 목록

    const ageStackedBarData = {
        labels: ageStackedBarLabels,
        datasets: [
            {
                label: "10대",
                data: fetchedData.map((d) => ((d.age10 / d.totalAge) * 100).toFixed(2)),
                backgroundColor: "#FF6384",
            },
            {
                label: "20대",
                data: fetchedData.map((d) => ((d.age20 / d.totalAge) * 100).toFixed(2)),
                backgroundColor: "#36A2EB",
            },
            {
                label: "30대",
                data: fetchedData.map((d) => ((d.age30 / d.totalAge) * 100).toFixed(2)),
                backgroundColor: "#FFCE56",
            },
            {
                label: "40대",
                data: fetchedData.map((d) => ((d.age40 / d.totalAge) * 100).toFixed(2)),
                backgroundColor: "#4BC0C0",
            },
            {
                label: "50대",
                data: fetchedData.map((d) => ((d.age50 / d.totalAge) * 100).toFixed(2)),
                backgroundColor: "#9966FF",
            },
            {
                label: "60대 이상",
                data: fetchedData.map((d) => ((d.age60plus / d.totalAge) * 100).toFixed(2)),
                backgroundColor: "#FF9F40",
            },
        ],
    };

    const ageStackedBarOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            title: {
                display: true,
                text: "연령대별 유동인구 비율 (Stacked Bar)",
            },
            tooltip: {
                callbacks: {
                    label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y}%`,
                },
            },
        },
        scales: {
            x: {
                stacked: true,
            },
            y: {
                stacked: true,
                beginAtZero: true,
                max: 100,
                ticks: {
                    callback: (value) => `${value}%`,
                },
            },
        },
    };


    /* 요일별 유동인구 */
    const dayLabels = ["월", "화", "수", "목", "금", "토", "일"];

    const dayChartData = {
        labels: dayLabels,
        datasets: fetchedData.map((data, idx) => ({
            label: data.name,
            data: [
                data.mondayFloatingPopulation,
                data.tuesdayFloatingPopulation,
                data.wednesdayFloatingPopulation,
                data.thursdayFloatingPopulation,
                data.fridayFloatingPopulation,
                data.saturdayFloatingPopulation,
                data.sundayFloatingPopulation,
            ],
            backgroundColor: colorList[idx % colorList.length],
        })),
    };

    const dayChartOptions = {
        responsive: true,
        plugins: {
            legend: {position: "top"},
            title: {
                display: true,
                text: "지역 간 유동 인구 비교",
            },
        },
        scales: {
            y: {beginAtZero: true},
        },
    };

    /* 시간별 유동인구 */
    const timeLabels = ["00~06시", "06~11시", "11~14시", "14~17시", "17~21시", "21~24시"];

    const timeChartData = {
        labels: timeLabels,
        datasets: fetchedData.map((data, idx) => ({
            label: data.name,
            data: [
                data.floating00to06,
                data.floating06to11,
                data.floating11to14,
                data.floating14to17,
                data.floating17to21,
                data.floating21to24,
            ],
            borderColor: colorList[idx % colorList.length],
            tension: 0.3,
            fill: false,
        })),
    };

    const timeChartOptions = {
        responsive: true,
        plugins: {
            legend: {position: "top"},
            title: {
                display: true,
                text: "시간대별 유동인구 비교",
            },
        },
        scales: {
            y: {beginAtZero: true},
        },
    };

    return (
        <div className="tw-w-full tw-max-w-4xl tw-mx-auto tw-mt-12">
            <button
                onClick={onClose}
                className="tw-absolute tw-top-3 tw-right-3 tw-w-8 tw-h-8 tw-rounded-full tw-bg-gray-200 hover:tw-bg-gray-300 tw-text-gray-700 hover:tw-text-black tw-flex tw-items-center tw-justify-center tw-transition"
                aria-label="닫기"
            >
                <X className="tw-w-4 tw-h-4"/>
            </button>

            <h2 className="tw-text-xl tw-font-bold tw-mb-4 tw-text-center">📊 다중 지역 비교</h2>
            <Bar data={dayChartData} options={dayChartOptions}/>

            <div className="tw-mt-12">
                <h2 className="tw-text-xl tw-font-bold tw-mb-4 tw-text-center">⏰ 시간대별 유동인구</h2>
                <Line data={timeChartData} options={timeChartOptions}/>
            </div>
            <div className="tw-mt-12 tw-h-[500px]">
                <h2 className="tw-text-xl tw-font-bold tw-mb-4 tw-text-center ">📈 연령대별 유동인구 비율 (Radar)</h2>
                <Bar data={ageStackedBarData} options={ageStackedBarOptions} />

            </div>
        </div>
    );
};

export default CompareChartPanel;

import React, {useEffect, useState} from "react";
import { Bar } from "react-chartjs-2";
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

const CompareChartPanel = ({ infos }) => {
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

                            mondayFloatingPopulation: data.mondayFloatingPopulation,
                            tuesdayFloatingPopulation: data.tuesdayFloatingPopulation,
                            wednesdayFloatingPopulation: data.wednesdayFloatingPopulation,
                            thursdayFloatingPopulation: data.thursdayFloatingPopulation,
                            fridayFloatingPopulation: data.fridayFloatingPopulation,
                            saturdayFloatingPopulation: data.saturdayFloatingPopulation,
                            sundayFloatingPopulation: data.sundayFloatingPopulation,

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

    const labels = fetchedData.map((item) => item.name);
    const totalFloating = fetchedData.map((item) => item.totalFloating);
    const totalWorkers = fetchedData.map((item) => item.totalWorkers);
    const dominantAges = fetchedData.map((item) => item.dominantAge);

    const dayLabels = ["월", "화", "수", "목", "금", "토", "일"];

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

    const chartData = {
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

    const options = {
        responsive: true,
        plugins: {
            legend: { position: "top" },
            title: {
                display: true,
                text: "지역 간 유동 인구 비교",
            },
            tooltip: {
                callbacks: {
                    afterBody: (tooltipItems) => {
                        const index = tooltipItems[0].dataIndex;
                        return `🎯 주 연령대: ${dominantAges[index]}`;
                    },
                },
            },
        },
        scales: {
            y: { beginAtZero: true },
        },
    };

    return (
        <div className="tw-absolute tw-top-0 tw-right-0 tw-w-full tw-max-w-4xl tw-mx-auto tw-mt-12">
            <h2 className="tw-text-xl tw-font-bold tw-mb-4 tw-text-center">📊 다중 지역 비교</h2>
            <Bar data={chartData} options={options} />
        </div>
    );
};

export default CompareChartPanel;

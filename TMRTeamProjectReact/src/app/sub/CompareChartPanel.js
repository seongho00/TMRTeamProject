import React from "react";
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

const CompareChartPanel = ({ data }) => {
    if (!data || data.length === 0) return null;

    const labels = data.map((item) => item.name);

    const totalFloating = data.map((item) => item.totalFloating);
    const totalWorkers = data.map((item) => item.totalWorkers);
    const dominantAges = data.map((item) => item.dominantAge);

    const chartData = {
        labels,
        datasets: [
            {
                label: "유동인구",
                data: totalFloating,
                backgroundColor: "#4e79a7",
            },
            {
                label: "직장인구",
                data: totalWorkers,
                backgroundColor: "#f28e2b",
            },
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            legend: { position: "top" },
            title: {
                display: true,
                text: "선택된 지역 간 인구 비교",
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

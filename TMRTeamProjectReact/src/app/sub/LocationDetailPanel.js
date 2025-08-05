import React, {useEffect, useState} from 'react';
import {X} from "lucide-react";
import {Pie} from 'react-chartjs-2';
import {Bar, Line} from "react-chartjs-2";
import {motion, AnimatePresence} from "framer-motion";

import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend, ArcElement
} from "chart.js";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

ChartJS.register(ArcElement, Tooltip, Legend);

const LocationDetailPanel = ({info, onClose}) => {
    if (!info) return null;

    const [data, setData] = useState(null);

    useEffect(() => {
        fetch(`http://localhost:8080/usr/commercialData/findByEmdCode?emdCode=${info.address}`)  // Spring Boot API 경로
            .then(res => res.json())
            .then(setData)
            .catch(console.error);
    }, []);

    if (!data) return <p className="tw-p-4">📡 데이터 로딩 중...</p>;

    const ageLabels = ['10대', '20대', '30대', '40대', '50대', '60대 이상'];
    const ageValues = [data.age10, data.age20, data.age30, data.age40, data.age50, data.age60plus];
    const workingValues = [data.workingAge10, data.workingAge20, data.workingAge30, data.workingAge40, data.workingAge50, data.workingAge60Plus];

    const commonColors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];

    const makeChartData = values => ({
        labels: ageLabels,
        datasets: [{data: values, backgroundColor: commonColors}]
    });

    const pieOptions = (values) => ({
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1.3,
        plugins: {
            legend: {position: 'bottom'},
            tooltip: {
                callbacks: {
                    label: context => {
                        const value = context.parsed;
                        const total = values.reduce((a, b) => a + b, 0);
                        const percent = ((value / total) * 100).toFixed(1);
                        return `${context.label}: ${value.toLocaleString()}명 (${percent}%)`;
                    }
                }
            }
        }
    });

    // ✅ 요일별 라벨
    const dayLabels = ["월", "화", "수", "목", "금", "토", "일"];
    const dayData = [data.mondayFloatingPopulation, data.tuesdayFloatingPopulation, data.wednesdayFloatingPopulation, data.thursdayFloatingPopulation, data.fridayFloatingPopulation, data.saturdayFloatingPopulation, data.sundayFloatingPopulation];

    const dayChartData = {
        labels: dayLabels,
        datasets: [
            {
                label: "요일별 유동인구 수",
                data: dayData,
                backgroundColor: "#4e79a7",
            },
        ],
    };

    const dayChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {display: false},
            title: {
                display: true,
                text: "요일별 유동인구",
            },
        },
        scales: {
            y: {beginAtZero: true},
        },
    };


    // ✅ 시간대별 유동인구 데이터
    const timeLabels = ["00~06시", "06~11시", "11~14시", "14~17시", "17~21시", "21~24시"];
    const timeData = [data.floating00to06, data.floating06to11, data.floating11to14, data.floating14to17, data.floating17to21, data.floating21to24];

    const timeChartData = {
        labels: timeLabels,
        datasets: [
            {
                label: "시간대별 유동인구 수",
                data: timeData,
                borderColor: "#f28e2b",
                backgroundColor: "#f28e2b66",
                tension: 0.3,
                fill: true,
            },
        ],
    };

    const timeChartOptions = {
        responsive: true,
        plugins: {
            legend: {position: "top"},
            title: {
                display: true,
                text: "시간대별 유동인구",
            },
        },
        scales: {
            y: {beginAtZero: true},
        },
    };
    return (
        <AnimatePresence>
            <motion.div
                key={info.address}
                initial={{x: "100%"}}
                animate={{x: 0}}
                exit={{x: "100%"}}
                transition={{type: "tween", duration: 0.5}}
                className="tw-fixed tw-top-0 tw-right-0 tw-h-full tw-w-[500px] tw-bg-white tw-shadow-lg tw-z-50 tw-border tw-border-black tw-overflow-auto"
            >

                <button
                    onClick={onClose}
                    className="tw-absolute tw-top-3 tw-right-3 tw-w-8 tw-h-8 tw-rounded-full tw-bg-gray-200 hover:tw-bg-gray-300 tw-text-gray-700 hover:tw-text-black tw-flex tw-items-center tw-justify-center tw-transition"
                    aria-label="닫기"
                >
                    <X className="tw-w-4 tw-h-4"/>
                </button>

                <h2 className="text-xl font-bold mb-2">{data.emdName}</h2>

                {/* 연령대 차트 */}
                <div className="tw-w-full tw-flex tw-flex-col tw-gap-8 tw-items-center">
                    <div className="tw-w-[280px]">
                        <h3 className="tw-text-center tw-font-semibold tw-text-base tw-mb-2">연령대별 유동인구</h3>
                        <Pie data={makeChartData(ageValues)} options={pieOptions(ageValues)}/>
                    </div>
                    <div className="tw-w-[280px]">
                        <h3 className="tw-text-center tw-font-semibold tw-text-base tw-mb-2">연령대별 직장인구</h3>
                        <Pie data={makeChartData(workingValues)} options={pieOptions(workingValues)}/>
                    </div>
                </div>

                {/* 요일, 시간별 유동인구 차트 */}
                <div className="tw-p-6 tw-space-y-12">
                    <div className="tw-w-full tw-h-[200px] tw-mx-auto">
                        <Bar data={dayChartData} options={dayChartOptions}/>
                    </div>
                    <div className="tw-w-full tw-h-[200px] tw-mx-auto">
                        <Line data={timeChartData} options={timeChartOptions}/>
                    </div>

                </div>
            </motion.div>
        </AnimatePresence>
    );
};

export default LocationDetailPanel;

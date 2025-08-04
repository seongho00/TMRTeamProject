import React, {useEffect, useState} from 'react';
import {X} from "lucide-react";
import {Pie} from 'react-chartjs-2';
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend,
} from 'chart.js';

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
        datasets: [{ data: values, backgroundColor: commonColors }]
    });

    const options = (values) => ({
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1.3,
        plugins: {
            legend: { position: 'bottom' },
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

    return (
        <div
            className="tw-fixed tw-right-0 tw-top-0 tw-h-full tw-w-[300px] tw-bg-white tw-shadow-lg tw-p-4 tw-z-50 tw-border tw-border-black">
            <button
                onClick={onClose}
                className="tw-absolute tw-top-3 tw-right-3 tw-w-8 tw-h-8 tw-rounded-full tw-bg-gray-200 hover:tw-bg-gray-300 tw-text-gray-700 hover:tw-text-black tw-flex tw-items-center tw-justify-center tw-transition"
                aria-label="닫기"
            >
                <X className="tw-w-4 tw-h-4"/>
            </button>

            <h2 className="text-xl font-bold mb-2">{info.address}</h2>

            {/* 연령대 차트 */}
            <div className="tw-w-full tw-flex tw-flex-col tw-gap-8 tw-items-center">
                <div className="tw-w-[280px]">
                    <h3 className="tw-text-center tw-font-semibold tw-text-base tw-mb-2">연령대별 유동인구</h3>
                    <Pie data={makeChartData(ageValues)} options={options(ageValues)} />
                </div>
                <div className="tw-w-[280px]">
                    <h3 className="tw-text-center tw-font-semibold tw-text-base tw-mb-2">연령대별 직장인구</h3>
                    <Pie data={makeChartData(workingValues)} options={options(workingValues)} />
                </div>
            </div>
            {/* 추가로 차트, 링크, 등등도 삽입 가능 */}
        </div>
    );
};

export default LocationDetailPanel;

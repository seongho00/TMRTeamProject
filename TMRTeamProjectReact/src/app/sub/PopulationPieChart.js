import { useEffect, useState } from 'react';
import { Pie } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend,
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const PopulationPieChart = () => {
    const [data, setData] = useState(null);

    useEffect(() => {
        fetch('http://localhost:8080/usr/commercialData/getPopulation')  // Spring Boot API 경로
            .then(res => res.json())
            .then(setData)
            .catch(console.error);
    }, []);

    if (!data) return <p>📡 데이터 로딩 중...</p>;

    const ageLabels = ['10대', '20대', '30대', '40대', '50대', '60대 이상'];
    const ageValues = [
        data.age10,
        data.age20,
        data.age30,
        data.age40,
        data.age50,
        data.age60plus
    ];

    const chartData = {
        labels: ageLabels,
        datasets: [
            {
                data: ageValues,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56',
                    '#4BC0C0', '#9966FF', '#FF9F40'
                ]
            }
        ]
    };

    const options = {
        responsive: true,
        plugins: {
            legend: { position: 'bottom' },
            tooltip: {
                callbacks: {
                    label: context => {
                        const value = context.parsed;
                        const total = ageValues.reduce((a, b) => a + b, 0);
                        const percent = ((value / total) * 100).toFixed(1);
                        return `${context.label}: ${value.toLocaleString()}명 (${percent}%)`;
                    }
                }
            }
        }
    };

    return (
        <div className="w-[400px] mx-auto">
            <h3 className="text-center font-bold text-lg mb-4">연령대별 유동인구 비율</h3>
            <Pie data={chartData} options={options} />
        </div>
    );
};

export default PopulationPieChart;

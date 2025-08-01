"use client";

import { useState } from "react";

const MonthlySimulationPage = ({ character, business, location, initialCost, onFinish }) => {
    const [month, setMonth] = useState(1);
    const [balance, setBalance] = useState(initialCost);
    const [logs, setLogs] = useState([]);
    const [history, setHistory] = useState([]);



    const runSimulation = () => {
        // 👉 매출 / 비용 계산 예시 (임의 값 사용)
        const revenue = getEstimatedRevenue();
        const cost = getEstimatedCost();
        const profit = revenue - cost;


        const newBalance = balance + profit;
        setBalance(newBalance);

        setLogs((prev) => [
            `🗓 ${month}월차 | 매출: ${revenue.toLocaleString()}원, 비용: ${cost.toLocaleString()}원, 순이익: ${profit.toLocaleString()}원, 잔고: ${newBalance.toLocaleString()}원`,
            ...prev
        ]);

        setHistory((prev) => [...prev, { month, revenue, cost, profit, balance: newBalance }]);

        if (month >= 12 || newBalance <= 0) {
            onFinish(history.concat({ month, revenue, cost, profit, balance: newBalance }));
        } else {
            setMonth(month + 1);
        }
    };

    const getEstimatedRevenue = () => {
        // 실제로는 업종/지역 기반 평균 매출 활용
        const base = 5000000;
        const variation = Math.floor(Math.random() * 1000000) - 500000;
        let revenue = base + variation;

        // 🎯 여름철(6~8월) + 한식 업종 매출 감소 이벤트
        const isSummer = month >= 6 && month <= 8;
        const isHansik = business.upjongCd === "CS100001" || business.name === "한식음식점";

        if (isSummer && isHansik) {
            const originalRevenue = revenue;
            revenue = Math.floor(revenue * 0.8); // 20% 감소

            setLogs((prev) => [
                `🔥 폭염으로 한식 매출 20% 감소 (${originalRevenue.toLocaleString()} → ${revenue.toLocaleString()})`,
                ...prev
            ]);
        }

        return revenue;
    };

    const getEstimatedCost = () => {
        // 임시 고정비용 + 랜덤 이벤트성 지출
        const baseCost = 3000000;
        const randomCost = Math.floor(Math.random() * 500000);
        return baseCost + randomCost;
    };

    return (
        <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen tw-px-4">
            <h1 className="tw-text-3xl tw-font-bold tw-mb-4">📊 {month}월차 시뮬레이션</h1>
            <p className="tw-mb-2 tw-text-lg">현재 잔고: {balance.toLocaleString()}원</p>

            <button
                onClick={runSimulation}
                className="tw-mb-6 tw-bg-blue-500 tw-text-white tw-px-6 tw-py-2 tw-rounded-xl hover:tw-bg-blue-600"
            >
                다음 달 진행 →
            </button>

            <div className="tw-w-full tw-max-w-2xl tw-h-[300px] tw-overflow-y-auto tw-bg-gray-100 tw-p-4 tw-rounded-lg">
                {logs.map((log, idx) => (
                    <div key={idx} className="tw-text-sm tw-mb-1">{log}</div>
                ))}
            </div>
        </div>
    );
};

export default MonthlySimulationPage;

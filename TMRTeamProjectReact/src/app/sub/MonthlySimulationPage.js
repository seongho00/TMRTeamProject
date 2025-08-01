"use client";

import {useState, useEffect} from "react";

const MonthlySimulationPage = ({character, business, location, initialCost, onFinish}) => {
    const [month, setMonth] = useState(1);
    const [balance, setBalance] = useState(initialCost);
    const [logs, setLogs] = useState([]);
    const [history, setHistory] = useState([]);
    const [events, setEvents] = useState([]);
    const [pendingEvent, setPendingEvent] = useState(null); // 선택형 이벤트 발생 시 저장
    const [isWaitingChoice, setIsWaitingChoice] = useState(false);
    const [remainingEvents, setRemainingEvents] = useState([]); // ✅ 이벤트 큐

    // 이벤트 JSON 가져오기
    useEffect(() => {
        fetch("/events.json")
            .then(res => res.json())
            .then(data => {
                setEvents(data);
            })
            .catch(err => console.error("이벤트 불러오기 실패:", err));
    }, []);

    const runSimulation = () => {
        const applicableEvents = events.filter(event =>
            event.type === "decision" &&
            matchCondition(event.condition, month, business) &&
            (event.probability === undefined || Math.random() < event.probability)
        );

        if (applicableEvents.length > 0) {
            setPendingEvent(applicableEvents[0]);
            setRemainingEvents(applicableEvents.slice(1)); // 다음 이벤트는 차례로 대기
            setIsWaitingChoice(true);
            return;
        }

        runMainSimulation();

    };

    const runMainSimulation = () => {
        const revenue = getEstimatedRevenue();
        const cost = getEstimatedCost();
        const profit = revenue - cost;
        const newBalance = balance + profit;

        setBalance(newBalance);
        setLogs(prev => [
            `🗓 ${month}월차 | 매출: ${revenue.toLocaleString()}원, 비용: ${cost.toLocaleString()}원, 순이익: ${profit.toLocaleString()}원, 잔고: ${newBalance.toLocaleString()}원`,
            ...prev
        ]);
        setHistory(prev => [...prev, { month, revenue, cost, profit, balance: newBalance }]);

        if (month >= 12 || newBalance <= 0) {
            onFinish(history.concat({ month, revenue, cost, profit, balance: newBalance }));
        } else {
            setMonth(month + 1);
        }
    };



    const applyDecision = (choice) => {
        let revenue = getEstimatedRevenue();
        let cost = getEstimatedCost();

        if (choice.effect.multiplier) {
            revenue = Math.floor(revenue * choice.effect.multiplier);
        }
        if (choice.effect.additionalCost) {
            cost += choice.effect.additionalCost;
        }

        const profit = revenue - cost;
        const newBalance = balance + profit;

        setBalance(newBalance);
        setLogs(prev => [
            `🗳 ${choice.log}`,
            `🗓 ${month}월차 | 매출: ${revenue.toLocaleString()}원, 비용: ${cost.toLocaleString()}원, 순이익: ${profit.toLocaleString()}원, 잔고: ${newBalance.toLocaleString()}원`,
            ...prev
        ]);
        setHistory(prev => [...prev, { month, revenue, cost, profit, balance: newBalance }]);

        // 다음 이벤트 처리 or 본체 실행
        if (remainingEvents.length > 0) {
            const [next, ...rest] = remainingEvents;
            setPendingEvent(next);
            setRemainingEvents(rest);
        } else {
            setPendingEvent(null);
            setIsWaitingChoice(false);
            runMainSimulation(); // ✅ 다음 단계로
        }
    };

    function matchCondition(condition, month, business) {
        // 월 범위 검사 (예: [6, 8])
        if (condition.monthRange) {
            const [start, end] = condition.monthRange;
            if (month < start || month > end) return false;
        }

        // 특정 월 검사 (예: { month: 12 })
        if (condition.month !== undefined) {
            if (month !== condition.month) return false;
        }

        // 업종 코드 검사 (예: ["CS100001"])
        if (condition.businessCodes) {
            if (!condition.businessCodes.includes(business.upjongCd)) return false;
        }

        // 여기에 캐릭터나 지역 조건도 확장 가능
        return true; // 모두 통과한 경우
    }

    const applyCostEvents = (baseCost) => {
        let updatedCost = baseCost;
        events.forEach((event) => {
            const { condition, type, effect, description } = event;
            if (type !== "cost") return;

            const matches = condition.month === month;
            if (matches) {
                if (effect.additionalCost) updatedCost += effect.additionalCost;
                setLogs(prev => [`${description} (추가 비용: ${effect.additionalCost.toLocaleString()}원)`, ...prev]);
            }
        });
        return updatedCost;
    };

    const getEstimatedRevenue = () => {
        return 5000000 + Math.floor(Math.random() * 1000000) - 500000;
    };

    const getEstimatedCost = () => {
        const base = 3000000 + Math.floor(Math.random() * 500000);
        return applyCostEvents(base);
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
            {isWaitingChoice && pendingEvent && (
                <div className="tw-p-4 tw-bg-yellow-100 tw-rounded-lg tw-mb-4 tw-w-full tw-max-w-2xl">
                    <p className="tw-font-bold tw-mb-2">{pendingEvent.description}</p>
                    {pendingEvent.choices.map((choice, idx) => (
                        <button
                            key={idx}
                            onClick={() => applyDecision(choice)}
                            className="tw-block tw-bg-blue-500 tw-text-white tw-px-4 tw-py-2 tw-rounded-xl tw-mb-2 hover:tw-bg-blue-600 tw-w-full"
                        >
                            {choice.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

export default MonthlySimulationPage;

"use client";

import {useState, useEffect} from "react";
import WeeklyCalendar from "./WeeklyCalendar";


const WeeklySimulationPage = ({character, business, location, initialCost, onFinish}) => {
    const [month, setMonth] = useState(1);
    const [weekInMonth, setWeekInMonth] = useState(1); // ✅ 추가: 1~4
    const [year, setYear] = useState(2025); // 기본 시작 연도
    const [balance, setBalance] = useState(initialCost);
    const [logs, setLogs] = useState([]);
    const [history, setHistory] = useState([]);
    const [events, setEvents] = useState([]);
    const [pendingEvent, setPendingEvent] = useState(null); // 선택형 이벤트 발생 시 저장
    const [isWaitingChoice, setIsWaitingChoice] = useState(false);
    const [remainingEvents, setRemainingEvents] = useState([]); // ✅ 이벤트 큐
    const [status, setStatus] = useState({
        fatigue: false,
        popularity: 0,
        trust: 0
    });

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
            `🗓 ${month}월 ${weekInMonth}주차 | 매출: ${revenue.toLocaleString()}원, 비용: ${cost.toLocaleString()}원, 순이익: ${profit.toLocaleString()}원, 잔고: ${newBalance.toLocaleString()}원`,
            ...prev
        ]);
        setHistory(prev => [...prev, {month, revenue, cost, profit, balance: newBalance}]);

        const lastWeek = getLastWeekOfMonth(year, month);

        // 날짜 계산 로직
        if ((month === 12 && weekInMonth === lastWeek) || newBalance <= 0) {
            onFinish(history.concat({year, month, weekInMonth, revenue, cost, profit, balance: newBalance}));
        } else {
            if (weekInMonth === lastWeek) {
                if (month === 12) {
                    setYear(prev => prev + 1);
                    setMonth(1);
                } else {
                    setMonth(prev => prev + 1);
                }
                setWeekInMonth(1);
            } else {
                setWeekInMonth(prev => prev + 1);
            }
        }

    };
    
    // 해당되는 연도의 달월이 몇주차까지 있는지 계산
    function getLastWeekOfMonth(year, month) {
        const firstDay = new Date(year, month - 1, 1); // JS: month 0-indexed
        const lastDay = new Date(year, month, 0); // 0일 = 전 달의 마지막 날 = 해당 월의 말일
        const firstWeekday = firstDay.getDay(); // 일(0)~토(6)
        const totalDays = lastDay.getDate();

        return Math.ceil((totalDays + firstWeekday) / 7);
    }


    const applyDecision = (choice) => {
        let revenue = getEstimatedRevenue();
        let cost = getEstimatedCost();
        let appliedLog = null;
        let updatedStatus = {...status};

        if (choice.effect.multiplier) {
            revenue = Math.floor(revenue * choice.effect.multiplier);
        }
        if (choice.effect.additionalCost) {
            cost += choice.effect.additionalCost;
        }

        // ✅ 확률 기반 결과 처리 (randomOutcome)
        if (choice.effect.randomOutcome) {
            const rand = Math.random();
            let acc = 0;
            for (const outcome of choice.effect.randomOutcome) {
                acc += outcome.probability;
                if (rand < acc) {
                    if (outcome.multiplier) {
                        revenue = Math.floor(revenue * outcome.multiplier);
                    }
                    if (outcome.additionalCost) {
                        cost += outcome.additionalCost;
                    }
                    if (outcome.penalty === "fatigue") {
                        updatedStatus.fatigue = true;
                    }
                    if (outcome.penalty === "popularityDown") {
                        updatedStatus.popularity = Math.max(0, updatedStatus.popularity - 1);
                    }
                    if (outcome.penalty === "trustDown") {
                        updatedStatus.trust = Math.max(0, updatedStatus.trust - 1);
                    }
                    appliedLog = outcome.log;
                    break;
                }
            }
        }

        const profit = revenue - cost;
        const newBalance = balance + profit;

        setBalance(newBalance);
        setLogs(prev => [
            `🗳 ${choice.log}`,
            `🗓 ${month}월차 | 매출: ${revenue.toLocaleString()}원, 비용: ${cost.toLocaleString()}원, 순이익: ${profit.toLocaleString()}원, 잔고: ${newBalance.toLocaleString()}원`,
            ...prev
        ]);
        setHistory(prev => [...prev, {month, revenue, cost, profit, balance: newBalance}]);

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
        if (condition.monthRange) {
            const [start, end] = condition.monthRange;
            if (month < start || month > end) return false;
        }

        if (condition.month !== undefined && month !== condition.month) return false;
        if (condition.week !== undefined && condition.week !== weekInMonth) return false;

        if (condition.businessCodes) {
            if (!condition.businessCodes.includes(business.upjongCd)) return false;
        }

        return true;
    }

    const applyCostEvents = (baseCost) => {
        let updatedCost = baseCost;
        events.forEach((event) => {
            const {condition, type, effect, description} = event;
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
            <h1 className="tw-text-3xl tw-font-bold tw-mb-4">📊 {month}월 {weekInMonth}주차 시뮬레이션</h1>
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

            <WeeklyCalendar year={year} month={month} weekInMonth={weekInMonth} />
        </div>
    );
};

export default WeeklySimulationPage;

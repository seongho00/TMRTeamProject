"use client";

import {useState, useEffect} from "react";
import WeeklyCalendar from "./WeeklyCalendar";


const WeeklySimulationPage = ({character, business, location, initialCost, goLoan, rent, setShowResult}) => {
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
    const [loanAmount, setLoanAmount] = useState(goLoan);
    const [interestRate] = useState(5); // 연이율 5%, 필요시 props로 받아오기
    const [loanMonths] = useState(36); // 상환 개월 수
    const [loanLogs, setLoanLogs] = useState([]);
    const [isFinished, setIsFinished] = useState(false);
    const [monthlySalesAmount, setMonthlySalesAmount] = useState(null);

    const lastWeek = getLastWeekOfMonth(year, month);


    if (month === 12 && weekInMonth === lastWeek) {
        setIsFinished(true); // ✅ 종료 상태로 전환
    }

    const [status, setStatus] = useState({
        fatigue: false,
        popularity: 0,
        trust: 0
    });

    // 행정동코드, 업종코드를 통해 매출액가져오기

    useEffect(() => {
        if (!location?.emdCode || !business?.upjongCd) return;

        fetch(`http://localhost:8080/usr/dataset/getDataSet?emdCode=${location.emdCode}&upjongCd=${business.upjongCd}`)
            .then(res => {
                if (!res.ok) throw new Error("매출 데이터를 불러올 수 없습니다");
                return res.json();
            })
            .then(data => {
                console.log("평균 매출 데이터:", data);
                const sales = (data.monthlySalesAmount / data.storeCount) * 0.6 // 0.6 : 소규모 창업을 위한 보정수치
                setMonthlySalesAmount(sales);

            })
            .catch(err => console.error(err));
    }, [location, business]);

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
        let profit = revenue - cost;
        let newBalance = balance + profit;


        // ✅ 대출 상환 처리
        if (loanAmount > 0 && weekInMonth === 1) {
            const monthlyPayment = calculateMonthlyPayment(loanAmount, interestRate, loanMonths);
            // 이자/원금 분리
            const monthlyRate = interestRate / 100 / 12;
            const interestPortion = Math.round(loanAmount * monthlyRate);
            const principalPortion = monthlyPayment - interestPortion;

            // 원금 줄이기
            const newLoanAmount = Math.max(0, loanAmount - principalPortion);
            setLoanAmount(newLoanAmount);

            // 잔고에서 상환금 빼기
            newBalance -= monthlyPayment;

            setLoanLogs(prev => [
                `💸 대출 상환: 원금 ${formatKoreanMoney(principalPortion)}, 이자 ${formatKoreanMoney(interestPortion)})`,
                ...prev
            ]);
        }

        setBalance(newBalance);
        setLogs(prev => [
            `🗓 ${month}월 ${weekInMonth}주차 | 매출: ${revenue.toLocaleString()}원, 비용: ${cost.toLocaleString()}원, 순이익: ${profit.toLocaleString()}원, 잔고: ${newBalance.toLocaleString()}원`,
            ...prev
        ]);
        setHistory(prev => [...prev, {month, revenue, cost, profit, balance: newBalance}]);

        const lastWeek = getLastWeekOfMonth(year, month);

        // 날짜 계산 로직
        if ((month === 12 && weekInMonth === lastWeek) || newBalance <= 0) {
            setIsFinished(true);
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
        if (!monthlySalesAmount) return 0;
        const base = monthlySalesAmount * 0.6;   // 보정치 60% 적용
        const variation = base * 0.1;            // ±10% 변동
        return Math.floor(base + (Math.random() * variation * 2 - variation));
    };

    const getEstimatedCost = () => {
        // 인건비 (2명 기준 예: 300만 원)
        const labor = 3000000;

        // 식자재비 (매출의 30% 정도 가정 → getEstimatedRevenue() 참조)
        const food = Math.floor(getEstimatedRevenue() * 0.3);

        // 기본 운영비 (랜덤)
        const etc = 500000 + Math.floor(Math.random() * 200000);

        // 총합
        const baseCost = rent + labor + food + etc;

        return applyCostEvents(baseCost);
    };

    function formatKoreanMoney(value) {
        if (value === null || value === undefined || isNaN(value)) return "0원";

        const num = Number(value);
        const isNegative = num < 0;
        const absNum = Math.abs(num);

        const eok = Math.floor(absNum / 100000000);     // 억 단위
        const man = Math.floor((absNum % 100000000) / 10000); // 만 단위
        const won = absNum % 10000;                     // 원 단위

        let result;

        if (eok > 0) {
            result = `${eok}억`;
            if (man > 0) result += ` ${man.toLocaleString()}만`;
            if (won > 0) result += ` ${won.toLocaleString()}원`;
            else result += "원";
        } else if (man > 0) {
            result = `${man.toLocaleString()}만`;
            if (won > 0) result += ` ${won.toLocaleString()}원`;
            else result += "원";
        } else {
            result = `${won.toLocaleString()}원`;
        }

        return (isNegative ? "-" : "") + result;
    }

    function calculateMonthlyPayment(loanAmount, annualRate, months = 36) {
        const monthlyRate = annualRate / 100 / 12;
        if (monthlyRate === 0) return loanAmount / months;

        const monthlyPayment =
            loanAmount *
            (monthlyRate * Math.pow(1 + monthlyRate, months)) /
            (Math.pow(1 + monthlyRate, months) - 1);

        return Math.round(monthlyPayment);
    }

    return (
        <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen tw-px-4">
            <h1 className="tw-text-3xl tw-font-bold tw-mb-4">📊 {month}월 {weekInMonth}주차 시뮬레이션</h1>
            <p className="tw-mb-2 tw-text-lg">현재 잔고: {formatKoreanMoney(balance)}</p>

            <button
                onClick={isFinished ? () => setShowResult(true) : runSimulation}
                className="tw-mb-6 tw-bg-blue-500 tw-text-white tw-px-6 tw-py-2 tw-rounded-xl hover:tw-bg-blue-600"
            >
                {isFinished ? "시뮬레이션 종료" : "다음 주 진행 →"}
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
            <div className="tw-absolute tw-top-1/2 tw-left-10 tw-transform tw--translate-y-1/2">
                <WeeklyCalendar year={year} month={month} weekInMonth={weekInMonth}/>
            </div>

            <div className="tw-absolute tw-top-1/2 tw-right-6 tw-transform tw--translate-y-1/2">
                <div>남은 대출금 : {formatKoreanMoney(loanAmount)}</div>
                <div className="tw-mt-2 tw-h-48 tw-overflow-y-auto tw-bg-gray-100 tw-p-2 tw-rounded">
                    {loanLogs.map((log, idx) => (
                        <div key={idx} className="tw-text-xs tw-mb-1">{log}</div>
                    ))}
                </div>
            </div>

        </div>
    );
};

export default WeeklySimulationPage;

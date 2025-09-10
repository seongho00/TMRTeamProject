import React, {useState, useRef, useEffect} from "react";
import DesignChoice from "./DesignChoice";
import {motion, AnimatePresence} from "framer-motion";
import InfoTooltip from "./InfoTooltip";

const CostSettingPage = ({onSubmit, onBack}) => {
    const [initialCost, setInitialCost] = useState("5000000");
    const inputRef = useRef(null);
    const cursorOffset = useRef(0);
    const [showLoanModal, setShowLoanModal] = useState(false);
    const [showLoanForm, setShowLoanForm] = useState(false);
    const [showInitialCostModal, setShowInitialCostModal] = useState(false);
    const [amount, setAmount] = useState(0);
    const [interestRate, setInterestRate] = useState(5); // 연이율 % (기본 5%)
    const [selectedDesign, setSelectedDesign] = useState(null);
    const [selectedMethod, setSelectedMethod] = useState("");
    const [result, setResult] = useState(0);
    const emdCd = location.emdCode;

    // 초기비용 팝업 내부
    const deposit = 10000 * 10000; // 예: 1000만원 보증금
    const rent = 1000 * 10000;     // 예: 200만원 월세
    const labor = 300 * 10000;    // 2명 인건비 (300만원)
    const food = 300 * 10000;     // 식자재비 (300만원)
    const premium = 2000 * 10000; // 권리금
    const maintenance = 200 * 10000; // 관리비

    // 디자인 선택에 따라 변하는 비용
    const designCost = selectedDesign ? selectedDesign.cost : 0;

    useEffect(() => {
        const totalUsed = deposit + rent + labor + food + designCost + premium + maintenance
            + (selectedMethod === "lawyer_check" ? 500000 : 0);

        setResult(initialCost - totalUsed);
    }, [initialCost, deposit, rent, labor, food, designCost, premium, maintenance, selectedMethod]);

    const money = result + amount;

    // 부동산 사기 확률
    const scamRiskMap = {
        no_action: 0.7,
        self_check: 0.3,
        expert_verification: 0.05,
    };

    const items = [
        {
            label: "중개보수", value: (deposit + rent * 100) * 0.009, tooltip: "부동산이 계약을 중개해준 대가로 내는 수수료. \n" +
                "보증금 + (월세 × 100) 금액을 기준으로 0.3~0.9% 계산."
        },
        {label: "관리비", value: maintenance, tooltip: "매달 납부하는 건물 관리비 (공용 전기, 청소비 등)"},
        {
            label: "권리금", value: premium, tooltip: "기존 가게의 단골·시설·위치를 \n" +
                "그대로 이어받는 대가로 기존 주인에게 주는 비용"
        },
        {label: "보증금", value: deposit},
        {label: "월세", value: rent},
        {label: "인건비(2명)", value: labor},
        {label: "식자재", value: food},
    ];


    const handleStart = () => {
        setShowInitialCostModal(true);
    };

    // result 음수 여부만 체크하는 함수
    const handleCheckResult = () => {
        if (!selectedDesign) {
            alert("디자인을 선택해주세요!");
            return; // 선택 안 했으면 진행 막기
        }

        if (!selectedMethod) {
            alert("부동산 거래 방식을 선택해주세요!");
            return;
        }
        // 부동산 사기 계산
        const riskRate = scamRiskMap[selectedMethod];
        const isScammed = Math.random() < riskRate;

        if (isScammed) {
            alert(`⚠️ 부동산 사기를 당했습니다! 보증금 ${formatMoneyKRW(deposit)}을 잃었습니다.`);
            setResult(prev => prev - deposit); // 보증금만큼 차감
        }


        if (result < 0) {
            setShowInitialCostModal(false);
            setShowLoanModal(true);   // 대출 여부 묻는 모달 열기
        } else {
            // 자본이 충분할 때는 바로 onSubmit 호출
            onSubmit({
                initialCost: money,
                goLoan: false,
                loanAmount: 0,
                rent: rent,
            });
            setShowLoanForm(false);
        }
    };

    const handleConfirm = () => {
        const minLoanAmount = Math.abs(result); // 최소 대출 금액

        if (amount < minLoanAmount) {
            alert(`최소 ${formatMoneyKRW(minLoanAmount)} 이상 대출해야 합니다.`);
            return; // ❌ 진행 막기
        }

        console.log("대출 확정:", amount);
        setShowLoanForm(false);

        onSubmit({
            initialCost: money,
            goLoan: true,
            loanAmount: amount,
            deposit: deposit,
            rent: rent,
        });
    };

    function formatNumber(value) {
        if (!value) return "";
        return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    const unformatNumber = (value) => {
        return value.replace(/[^0-9]/g, "");
    };

    const handleChange = (e) => {
        const rawValue = e.target.value;
        const unformatted = unformatNumber(rawValue);

        // 커서 위치 계산
        const selectionStart = e.target.selectionStart;
        const rawBeforeCursor = unformatNumber(rawValue.slice(0, selectionStart));
        cursorOffset.current = rawBeforeCursor.length;

        setInitialCost(unformatted);
    };

    useEffect(() => {
        if (inputRef.current) {
            const formatted = formatNumber(initialCost);
            let cursorPos = 0;
            let rawIndex = 0;
            for (let i = 0; i < formatted.length && rawIndex < cursorOffset.current; i++) {
                if (formatted[i] !== ",") {
                    rawIndex++;
                }
                cursorPos++;
            }
            inputRef.current.setSelectionRange(cursorPos, cursorPos);
        }
    }, [initialCost]);

    function parseNumber(value) {
        if (!value) return 0;
        return Number(value.replace(/,/g, ""));
    }

    function formatMoneyKRW(value) {
        if (value === null || value === undefined || isNaN(value)) return "0원";

        const num = Number(value);
        const isNegative = num < 0;
        const absNum = Math.abs(num);

        // 만원 미만
        if (absNum < 10000) {
            return (isNegative ? "-" : "") + `${absNum.toLocaleString()}원`;
        }

        const eok = Math.floor(absNum / 100000000);          // 억 단위
        const man = Math.floor((absNum % 100000000) / 10000); // 만원 단위

        let result = "";
        if (eok > 0 && man > 0) {
            result = `${eok}억 ${man.toLocaleString()}만원`;
        } else if (eok > 0) {
            result = `${eok}억`;
        } else {
            result = `${man.toLocaleString()}만원`;
        }

        return (isNegative ? "-" : "") + result;
    }


    return (
        <>
            <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen tw-px-4">
                <h1 className="tw-text-3xl tw-font-bold tw-mb-8">💰 초기자금을 입력해주세요</h1>

                <div className="tw-bg-white tw-p-6 tw-rounded-xl tw-shadow-md tw-w-full tw-max-w-xl">
                    <div className="tw-mb-4">
                        <label className="tw-block tw-font-semibold tw-mb-1">초기자금 (원)</label>
                        <input
                            ref={inputRef}
                            type="text"
                            className="tw-w-full tw-border tw-rounded tw-p-2"
                            value={formatNumber(initialCost)}
                            onChange={handleChange}
                        />
                    </div>
                    {/* 입력값을 억/만원 단위로 변환해서 표시 */}
                    <p className="tw-my-2 tw-text-gray-600">
                        {formatMoneyKRW(initialCost)}
                    </p>

                    <button
                        onClick={handleStart}
                        className="tw-w-full tw-bg-blue-500 tw-text-white tw-py-2 tw-rounded-lg hover:tw-bg-blue-600 tw-transition"
                    >
                        시뮬레이션 시작 →
                    </button>


                    <button
                        onClick={onBack}
                        className="tw-absolute tw-top-6 tw-left-6 tw-bg-gray-200 tw-text-gray-800 tw-px-4 tw-py-2 tw-rounded-md hover:tw-bg-gray-300 tw-transition"
                    >
                        ← 이전 단계
                    </button>
                </div>
            </div>

            {/* 0단계 : 초기 비용 계산 팝업창 */}

            <AnimatePresence mode="wait">
                {showInitialCostModal && (
                    <motion.div
                        key="initialCostModal"
                        className="tw-fixed tw-inset-0 tw-flex tw-items-center tw-justify-center tw-bg-black tw-bg-opacity-40"
                        initial={{opacity: 0}}
                        animate={{opacity: 1}}
                    >
                        <motion.div
                            className="tw-bg-white tw-p-6 tw-rounded-2xl tw-w-[400px] tw-shadow-lg tw-font-mono"
                            initial={{scale: 0.9, opacity: 0}}
                            animate={{scale: [0.8, 1.05, 1], opacity: 1}}
                            transition={{duration: 0.25, ease: "easeOut"}}
                        >
                            <h2 className="tw-text-center tw-font-bold tw-mb-4">초기 비용 계산</h2>

                            {/* 초기 자금 */}
                            <div className="tw-border-b tw-border-gray-400 tw-border-dashed tw-pb-2 tw-mb-2">
                                <p>
                                    초기자금:{" "}
                                    <span className="tw-font-semibold">
            {formatMoneyKRW(initialCost)}
          </span>
                                </p>
                            </div>

                            {/* 항목별 차감 */}
                            <div className="tw-space-y-1">
                                {items.map((item, idx) => (
                                    <motion.div
                                        key={idx}
                                        className="tw-flex tw-justify-between"
                                        initial={{x: -30, opacity: 0}}
                                        animate={{x: 0, opacity: 1}}
                                        transition={{delay: idx * 0.3, duration: 0.5}}
                                    >
                                        <div className="tw-flex tw-items-center tw-gap-1">
                                            <span>{item.label}</span>
                                            {item.tooltip && <InfoTooltip text={item.tooltip}/>}
                                        </div>
                                        <span className="tw-font-semibold tw-text-red-500">
              - {formatMoneyKRW(item.value)}
            </span>
                                    </motion.div>
                                ))}

                                {/* 디자인 비용 */}
                                <motion.div
                                    className="tw-flex tw-justify-between"
                                    initial={{x: -40, opacity: 0}}
                                    animate={{x: 0, opacity: 1}}
                                    transition={{delay: items.length * 0.3, duration: 0.5, ease: "easeOut"}}
                                >
                                    <DesignChoice onSelect={setSelectedDesign}/>
                                </motion.div>

                                {/* 부동산 거래 방식 */}
                                <motion.div
                                    className="tw-flex tw-justify-between tw-items-center"
                                    initial={{x: -40, opacity: 0}}
                                    animate={{x: 0, opacity: 1}}
                                    transition={{delay: (items.length + 1) * 0.3, duration: 0.5, ease: "easeOut"}}
                                >
                                    <div className="tw-flex tw-items-center tw-gap-1">
                                        <span>부동산 계약</span>
                                        <InfoTooltip
                                            text="부동산 계약을 어떻게 진행할지 선택하세요. 선택한 방식에 따라 사기 위험도, 체력 소모, 비용이 달라집니다."/>
                                    </div>
                                    <select
                                        value={selectedMethod}
                                        onChange={(e) => setSelectedMethod(e.target.value)}
                                        className="tw-border tw-rounded-lg tw-px-2 tw-py-1">
                                        <option value="">-- 선택 --</option>
                                        <option value="no_action" title="편하지만 사기 위험이 큽니다.">
                                            아무 행동 하지 않기
                                        </option>
                                        <option value="self_check" title="체력이 소모되지만 사기 위험을 줄일 수 있습니다.">
                                            직접 조사하기 (체력 -10)
                                        </option>
                                        <option value="lawyer_check" title="비용은 들지만 사기를 당할 확률이 가장 낮습니다.">
                                            외부 결제 (비용 50만원)
                                        </option>
                                    </select>
                                </motion.div>

                            </div>


                            {/* 합계 */}
                            <div className="tw-border-t tw-border-gray-400 tw-border-dashed tw-mt-3 tw-pt-2">
                                <div className="tw-flex tw-justify-between tw-font-bold">
                                    <span>잔여 금액</span>
                                    <motion.span
                                        initial={{scale: 1.3, color: "#16a34a", opacity: 0}}
                                        animate={{scale: 1, color: "#000", opacity: 1}}
                                        transition={{
                                            delay: items.length * 0.3 + 0.6, // 항목 개수 × delay 만큼 기다렸다가 시작
                                            duration: 0.6,
                                            ease: "easeOut",
                                        }}
                                        className={result < 0 ? "tw-text-red-600" : "tw-text-green-600"}
                                    >
                                        {formatMoneyKRW(result)}
                                    </motion.span>
                                </div>
                            </div>

                            {/* 버튼 */}
                            <div className="tw-flex tw-justify-end tw-gap-3 tw-mt-4">
                                <button
                                    onClick={() => setShowInitialCostModal(false)}
                                    className="tw-px-4 tw-py-2 tw-rounded-lg tw-border tw-border-gray-300 hover:tw-bg-gray-100"
                                >
                                    닫기
                                </button>
                                <button
                                    onClick={handleCheckResult}
                                    className="tw-px-4 tw-py-2 tw-rounded-lg tw-bg-blue-600 tw-text-white hover:tw-bg-blue-700"
                                >
                                    다음
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}


                {/* 1단계: 대출 여부 묻는 팝업 */}
                {showLoanModal && (
                    <motion.div
                        key="loanModal"
                        className="tw-fixed tw-inset-0 tw-flex tw-items-center tw-justify-center tw-bg-black tw-bg-opacity-40"
                        initial={{opacity: 0}}
                        animate={{opacity: 1}}
                        transition={{duration: 0.1}}
                    >
                        <motion.div
                            className="tw-bg-white tw-p-6 tw-rounded-lg tw-w-96"
                            initial={{scale: 0.8, opacity: 0}}
                            animate={{scale: [0.8, 1.05, 1], opacity: 1}}
                            transition={{duration: 0.25, ease: "easeOut"}}
                        >
                            <h2 className="tw-text-xl tw-font-bold tw-mb-4">자본이 부족합니다</h2>
                            <p className="tw-mb-4">대출을 진행하시겠습니까?</p>
                            <div className="tw-flex tw-justify-end tw-space-x-2">
                                <button
                                    onClick={() => {
                                        setShowLoanModal(false);
                                    }}
                                    className="tw-bg-gray-400 tw-text-white tw-px-4 tw-py-2 tw-rounded"
                                >
                                    아니오
                                </button>
                                <button
                                    onClick={() => {
                                        setShowLoanModal(false);   // 첫 모달 닫기
                                        setShowLoanForm(true);     // LoanPage 모달 열기
                                    }}
                                    className="tw-bg-blue-500 tw-text-white tw-px-4 tw-py-2 tw-rounded hover:tw-bg-blue-600"
                                >
                                    대출하기
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}

                {/* 2단계: LoanPage(대출 입력 폼) 팝업 */}
                {showLoanForm && (
                    <motion.div
                        key="loanForm"
                        className="tw-fixed tw-inset-0 tw-flex tw-items-center tw-justify-center tw-bg-black tw-bg-opacity-40"
                        initial={{opacity: 0}}
                        animate={{opacity: 1}}
                        transition={{duration: 0.1}}
                    >
                        <motion.div
                            className="tw-bg-white tw-p-6 tw-rounded-lg tw-w-96"
                            initial={{scale: 0.8, opacity: 0}}
                            animate={{scale: [0.8, 1.05, 1], opacity: 1}}
                            transition={{duration: 0.25, ease: "easeOut"}}
                        >
                            <h1 className="tw-text-xl tw-font-bold tw-mb-4">대출 받기</h1>
                            <input
                                type="text"
                                value={formatNumber(amount)}
                                onChange={(e) => {
                                    const rawValue = e.target.value;
                                    const numericValue = parseNumber(rawValue); // 콤마 제거 후 숫자 변환
                                    setAmount(numericValue);
                                }}
                                placeholder="대출 금액"
                                className="tw-border tw-w-full tw-p-2 tw-rounded tw-mb-4"
                            />

                            {/* 입력값을 억/만원 단위로 변환해서 표시 */}
                            <p className="tw-my-2 tw-text-gray-600">
                                {formatMoneyKRW(amount)}
                            </p>

                            {/* 월 이자 계산 결과 표시 */}
                            {amount > 0 && (
                                <p className="tw-mb-4 tw-text-gray-700">
                                    예상 월 이자(연 5%):{" "}
                                    <span className="tw-font-semibold tw-text-red-600">
            {Math.floor(amount * 0.05 / 12).toLocaleString()} 원
          </span>
                                </p>
                            )}

                            <div className="tw-flex tw-justify-end tw-space-x-2">
                                <button
                                    onClick={() => setShowLoanForm(false)}
                                    className="tw-bg-gray-400 tw-text-white tw-px-4 tw-py-2 tw-rounded"
                                >
                                    취소
                                </button>
                                <button
                                    onClick={handleConfirm}
                                    className="tw-bg-blue-500 tw-text-white tw-px-4 tw-py-2 tw-rounded hover:tw-bg-blue-600"
                                >
                                    확정
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}

            </AnimatePresence>

        </>
    );
};

export default CostSettingPage;

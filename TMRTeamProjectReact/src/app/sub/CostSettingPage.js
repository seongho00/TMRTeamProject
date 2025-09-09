import React, {useState, useRef, useEffect} from "react";
import DesignChoice from "./DesignChoice";


const CostSettingPage = ({onSubmit, onBack}) => {
    const [initialCost, setInitialCost] = useState("5000000");
    const inputRef = useRef(null);
    const cursorOffset = useRef(0);
    const [showLoanModal, setShowLoanModal] = useState(false);
    const [showLoanForm, setShowLoanForm] = useState(false);
    const [showInitialCostModal, setShowInitialCostModal] = useState(false);
    const [loanAmount, setLoanAmount] = useState(0);
    const [amount, setAmount] = useState(0);
    const [interestRate, setInterestRate] = useState(5); // 연이율 % (기본 5%)
    const [selectedDesign, setSelectedDesign] = useState(null);


    // 초기비용 팝업 내부
    const deposit = 1000 * 10000; // 예: 1000만원
    const rent = 200 * 10000;     // 예: 200만원
    const labor = 300 * 10000;    // 2명 인건비 (300만원)
    const food = 300 * 10000;     // 식자재비 (300만원)

// 디자인 선택에 따라 변하는 비용
    const designCost = selectedDesign ? selectedDesign.cost : 0;

// 결과 계산
    const totalUsed = deposit + rent + labor + food + designCost;
    const result = initialCost - totalUsed;

    const handleStart = () => {
        setShowInitialCostModal(true);
    };

    // result 음수 여부만 체크하는 함수
    const handleCheckResult = () => {
        if (result < 0) {
            setShowInitialCostModal(false);
            setShowLoanModal(true);   // 대출 여부 묻는 모달 열기
        } else {
            // 자본이 충분할 때는 바로 onSubmit 호출
            onSubmit(Number(initialCost), {
                goLoan: false,
                loanAmount: 0,
            });
            setShowLoanForm(false);
        }
    };

    const handleConfirm = () => {
        console.log("대출 확정:", amount);
        setShowLoanForm(false);

        onSubmit(Number(initialCost), {
            goLoan: true,
            loanAmount: amount,
        });
    };

    const formatNumber = (value) => {
        if (!value) return "";
        return value.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };

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

    function formatMoneyKRW(value) {
        if (value >= 100000000) { // 1억 이상
            const eok = Math.floor(value / 100000000); // 억 단위
            const man = Math.floor((value % 100000000) / 10000); // 남은 만원 단위
            if (man > 0) {
                return `${eok}억 ${man.toLocaleString()}만원`;
            } else {
                return `${eok}억`;
            }
        } else {
            return `${(value / 10000).toLocaleString()}만원`;
        }
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
            {showInitialCostModal && (
                <div
                    className="tw-fixed tw-inset-0 tw-flex tw-items-center tw-justify-center tw-bg-black tw-bg-opacity-40">
                    <div className="tw-bg-white tw-p-6 tw-rounded-2xl tw-w-[500px] tw-shadow-lg">
                        <h2 className="tw-text-xl tw-font-bold tw-mb-4">초기 비용 계산</h2>
                        <p className="tw-mb-4">
                            입력한 초기자금 :{" "}
                            <span className="tw-font-semibold">
                                {formatMoneyKRW(initialCost)}
                             </span>
                        </p>

                        <p className="tw-mb-4">
                            평균 보증금 :{" "}
                            <span className="tw-font-semibold">
                                {formatMoneyKRW(deposit)}
                            </span>
                        </p>

                        <p className="tw-mb-4">
                            평균 월세 :{" "}
                            <span className="tw-font-semibold">
                                {formatMoneyKRW(rent)}
                            </span>
                        </p>

                        <p className="tw-mb-4">
                            인건비(2명) :{" "}
                            <span className="tw-font-semibold">
                                {formatMoneyKRW(labor)}
                            </span>
                        </p>

                        <p className="tw-mb-4">
                            식자재 :{" "}
                            <span className="tw-font-semibold">
                                {formatMoneyKRW(food)}
                            </span>
                        </p>


                        {/* 디자인 선택창 */}
                        <DesignChoice onSelect={setSelectedDesign}/>

                        <p className="tw-mb-4">
                            결과 :{" "}
                            <span className="tw-font-semibold">
                                {formatMoneyKRW(result)}
                            </span>
                        </p>

                        {/* 버튼 영역 */}
                        <div className="tw-flex tw-justify-end tw-gap-3">
                            <button
                                onClick={() => setShowLoanForm(false)}
                                className="tw-px-4 tw-py-2 tw-rounded-lg tw-border tw-border-gray-300 hover:tw-bg-gray-100"
                            >
                                취소
                            </button>
                            <button
                                onClick={handleCheckResult}
                                className="tw-px-4 tw-py-2 tw-rounded-lg tw-bg-blue-600 tw-text-white hover:tw-bg-blue-700"
                            >
                                확인
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 1단계: 대출 여부 묻는 팝업 */}
            {showLoanModal && (
                <div
                    className="tw-fixed tw-inset-0 tw-flex tw-items-center tw-justify-center tw-bg-black tw-bg-opacity-40">
                    <div className="tw-bg-white tw-p-6 tw-rounded-lg tw-w-96">
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
                    </div>
                </div>
            )}

            {/* 2단계: LoanPage(대출 입력 폼) 팝업 */}
            {showLoanForm && (
                <div
                    className="tw-fixed tw-inset-0 tw-flex tw-items-center tw-justify-center tw-bg-black tw-bg-opacity-40">
                    <div className="tw-bg-white tw-p-6 tw-rounded-lg tw-w-96">
                        <h1 className="tw-text-xl tw-font-bold tw-mb-4">대출 시스템</h1>
                        <input
                            type="number"
                            value={amount}
                            onChange={(e) => setAmount(Number(e.target.value))}
                            placeholder="대출 금액"
                            className="tw-border tw-w-full tw-p-2 tw-rounded tw-mb-4"
                        />
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
                    </div>
                </div>
            )}


        </>
    );
};

export default CostSettingPage;

import React, { useState, useRef, useEffect } from "react";

const CostSettingPage = ({ onSubmit, onBack }) => {
    const [initialCost, setInitialCost] = useState("5000000");
    const inputRef = useRef(null);
    const cursorOffset = useRef(0);

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

    return (
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
                    onClick={() =>
                        onSubmit({
                            initialCost: Number(initialCost)
                        })
                    }
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
    );
};

export default CostSettingPage;

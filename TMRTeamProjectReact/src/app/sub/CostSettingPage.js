"use client";

import React, { useState } from "react";

const CostSettingPage = ({ character, business, onSubmit, onBack }) => {
    const [rent, setRent] = useState(1000000); // 기본 월세
    const [marketing, setMarketing] = useState(300000); // 기본 마케팅비
    const [initialCost, setInitialCost] = useState(5000000); // 기본 초기비용

    const handleStart = () => {
        if (!rent || !marketing || !initialCost) {
            alert("모든 값을 입력해주세요.");
            return;
        }

        onSubmit({
            rent: Number(rent),
            marketing: Number(marketing),
            initialCost: Number(initialCost),
        });
    };

    const formatNumber = (value) => {
        if (!value) return "";
        return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };

    const unformatNumber = (value) => {
        return value.replace(/,/g, "");
    };


    return (
        <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen tw-px-4">
            <h1 className="tw-text-3xl tw-font-bold tw-mb-8">💰 비용 설정</h1>

            <div className="tw-bg-white tw-p-6 tw-rounded-xl tw-shadow-md tw-w-full tw-max-w-xl">
                <div className="tw-mb-4">
                    <label className="tw-block tw-font-semibold tw-mb-1">월세 (원)</label>
                    <input
                        type="text"
                        className="tw-w-full tw-border tw-rounded tw-p-2"
                        value={formatNumber(rent)}
                        onChange={(e) => {
                            const raw = unformatNumber(e.target.value);
                            if (/^\d*$/.test(raw)) setRent(raw); // 숫자만 허용
                        }}
                    />
                </div>

                <div className="tw-mb-4">
                    <label className="tw-block tw-font-semibold tw-mb-1">마케팅 비용 (원)</label>
                    <input
                        type="text"
                        className="tw-w-full tw-border tw-rounded tw-p-2"
                        value={formatNumber(marketing)}
                        onChange={(e) => {
                            const raw = unformatNumber(e.target.value);
                            if (/^\d*$/.test(raw)) setMarketing(raw); // 숫자만 허용
                        }}
                    />
                </div>

                <div className="tw-mb-4">
                    <label className="tw-block tw-font-semibold tw-mb-1">초기비용 (원)</label>
                    <input
                        type="text"
                        className="tw-w-full tw-border tw-rounded tw-p-2"
                        value={formatNumber(initialCost)}
                        onChange={(e) => {
                            const raw = unformatNumber(e.target.value);
                            if (/^\d*$/.test(raw)) setInitialCost(raw); // 숫자만 허용
                        }}
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
    );
};

export default CostSettingPage;

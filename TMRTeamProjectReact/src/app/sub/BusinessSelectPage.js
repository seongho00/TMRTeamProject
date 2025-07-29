"use client";

import React, { useState } from "react";

const businessTypes = [
    { id: 1, name: "카페", description: "커피, 디저트 중심 매장" },
    { id: 2, name: "편의점", description: "24시간 운영 프랜차이즈 소매점" },
    { id: 3, name: "분식집", description: "떡볶이, 김밥 등 빠른 회전율" },
    { id: 4, name: "헬스장", description: "고정 회원 수 기반 수익" },
    { id: 5, name: "의류 매장", description: "시즌 트렌드에 민감한 판매" },
];

const BusinessSelectPage = ({ onSelect }) => {
    const [selectedId, setSelectedId] = useState(null);

    const handleSelect = (id) => {
        setSelectedId(id);
    };

    const handleNext = () => {
        if (selectedId === null) return alert("업종을 선택해주세요!");
        const selected = businessTypes.find((b) => b.id === selectedId);
        onSelect(selected); // 부모에 전달
    };

    return (
        <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen tw-px-4">
            <h1 className="tw-text-3xl tw-font-bold tw-mb-8">📂 업종을 선택하세요</h1>
            <div className="tw-grid tw-grid-cols-1 sm:tw-grid-cols-2 lg:tw-grid-cols-3 tw-gap-6">
                {businessTypes.map((b) => (
                    <div
                        key={b.id}
                        onClick={() => handleSelect(b.id)}
                        className={`tw-border tw-rounded-xl tw-p-6 tw-cursor-pointer tw-transition tw-shadow-md tw-text-center ${
                            selectedId === b.id
                                ? "tw-border-blue-500 tw-ring-2 tw-ring-blue-300"
                                : "hover:tw-shadow-xl"
                        }`}
                    >
                        <h2 className="tw-text-2xl tw-font-bold">{b.name}</h2>
                        <p className="tw-text-gray-600 tw-mt-2">{b.description}</p>
                    </div>
                ))}
            </div>

            <button
                onClick={handleNext}
                className="tw-bg-blue-500 tw-text-white tw-px-6 tw-py-2 tw-rounded-xl hover:tw-bg-blue-600 tw-transition tw-mt-10"
            >
                다음 단계 →
            </button>
        </div>
    );
};

export default BusinessSelectPage;

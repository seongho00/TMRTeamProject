"use client";

import {useEffect, useState} from "react";
import axios from "axios";

const businessTypes = [
    {name: "카페", description: "커피, 디저트 중심 매장", upjongCd: "CS100010"},
    {name: "편의점", description: "24시간 운영 프랜차이즈 소매점", upjongCd: "CS300002"},
    {name: "분식집", description: "떡볶이, 김밥 등 빠른 회전율", upjongCd: "CS100008"},
    {name: "패스트푸드점", description: "고정 회원 수 기반 수익", upjongCd: "CS100006"},
    {name: "의류 매장", description: "시즌 트렌드에 민감한 판매", upjongCd: "CS300011"},
    {name: "기타", description: "다른 업종 더보기", upjongCd: "etc"}
];

const BusinessSelectPage = ({onSelect , onBack}) => {
    const [selectedCode, setSelectedCode] = useState(null);
    const [customUpjongs, setCustomUpjongs] = useState([]);
    const [selectedCustom, setSelectedCustom] = useState(null);

    useEffect(() => {
        if (selectedCode === "etc") {
            axios.get("http://localhost:8080/usr/upjong/getAllUpjong")
                .then((res) => setCustomUpjongs(res.data))
                .catch((err) => console.error(err));
        }
    }, [selectedCode]);

    const handleSelect = (code) => {
        setSelectedCode(code);
        setSelectedCustom(null); // 기타 다시 선택 시 초기화
    };

    const handleNext = () => {
        if (!selectedCode) return alert("업종을 선택해주세요!");

        if (selectedCode === "etc") {
            if (!selectedCustom) return alert("기타 업종을 선택해주세요!");

            const convertedItem = {
                name: selectedCustom.upjongNm,
                description: "기타 업종", // 또는 필요 시 null
                upjongCd: selectedCustom.upjongCd,
            };

            onSelect(convertedItem);
        } else {
            const selected = businessTypes.find((b) => b.upjongCd === selectedCode);
            onSelect(selected);
        }
    };

    const handleCustomUpjongSelect = (item) => {
        console.log(item);
        setSelectedCustom(item);
    };


    return (
        <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen tw-px-4">
            <h1 className="tw-text-3xl tw-font-bold tw-mb-8">📂 업종을 선택하세요</h1>
            <div className="tw-grid tw-grid-cols-1 sm:tw-grid-cols-2 lg:tw-grid-cols-3 tw-gap-6">
                {businessTypes.map((b) => (
                    <div
                        key={b.upjongCd}
                        onClick={() => handleSelect(b.upjongCd)}
                        className={`tw-border tw-rounded-xl tw-p-6 tw-cursor-pointer tw-transition tw-shadow-md tw-text-center 
                            ${selectedCode === b.upjongCd ? "tw-border-blue-500 tw-ring-2 tw-ring-blue-300 tw-bg-blue-50" : "hover:tw-shadow-xl"}
                        `}
                    >
                        <h2 className="tw-text-2xl tw-font-bold">{b.name}</h2>
                        <p className="tw-text-gray-600 tw-mt-2">{b.description}</p>
                    </div>
                ))}
            </div>

            {selectedCode === "etc" && (
                <div
                    className="tw-mt-6 tw-w-full tw-max-w-2xl tw-h-[200px] tw-overflow-y-auto tw-border tw-rounded-lg tw-p-4">
                    <h2 className="tw-text-xl tw-font-semibold tw-mb-2">기타 업종 선택</h2>
                    <ul className="tw-grid tw-grid-cols-2 tw-gap-3">
                        {customUpjongs.map((item) => (
                            <li
                                key={item.upjongCd}
                                onClick={() => handleCustomUpjongSelect(item)}
                                className={`tw-px-4 tw-py-2 tw-border tw-rounded-xl tw-cursor-pointer
                                    hover:tw-bg-blue-200
                                    ${selectedCustom?.upjongCd === item.upjongCd ? "tw-bg-blue-200" : ""}
                                `}
                            >
                                {item.upjongNm}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <button
                onClick={handleNext}
                className="tw-bg-blue-500 tw-text-white tw-px-6 tw-py-2 tw-rounded-xl hover:tw-bg-blue-600 tw-transition tw-mt-10"
            >
                다음 단계 →
            </button>
            <button
                onClick={onBack}
                className="tw-absolute tw-top-6 tw-left-6 tw-bg-gray-200 tw-text-gray-800 tw-px-4 tw-py-2 tw-rounded-md hover:tw-bg-gray-300 tw-transition"
            >
                ← 이전 단계
            </button>
        </div>
    );
};

export default BusinessSelectPage;

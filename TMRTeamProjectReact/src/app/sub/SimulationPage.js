"use client";

import React from "react";

const SimulationPage = ({ character, business }) => {
    return (
        <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen tw-px-4">
            <h1 className="tw-text-3xl tw-font-bold tw-mb-6">📊 시뮬레이션 시작</h1>

            <div className="tw-bg-white tw-rounded-xl tw-shadow-md tw-p-6 tw-w-full tw-max-w-xl">
                <h2 className="tw-text-xl tw-font-bold tw-mb-2">선택된 캐릭터</h2>
                <p>👤 이름: {character.name}</p>
                <p>📝 설명: {character.description}</p>

                <hr className="tw-my-4" />

                <h2 className="tw-text-xl tw-font-bold tw-mb-2">선택된 업종</h2>
                <p>🏪 업종명: {business.name}</p>
                <p>🏪 업종코드: {business.upjongCd}</p>
                <p>📋 설명: {business.description}</p>

                <h2 className="tw-text-xl tw-font-bold tw-mb-2">선택된 위치</h2>
                <p>선택한 위치: {location?.emdName}</p>
            </div>

            <p className="tw-text-gray-500 tw-mt-8">
                ※ 추후 여기에 시뮬레이션 로직이 들어갈 예정입니다.
            </p>
        </div>
    );
};

export default SimulationPage;

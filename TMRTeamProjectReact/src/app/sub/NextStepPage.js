"use client";

import React from "react";

const NextStepPage = ({ character }) => {
    return (
        <div className="tw-flex tw-flex-col tw-items-center tw-justify-center tw-min-h-screen">
            <h1 className="tw-text-3xl tw-font-bold tw-mb-4">선택된 캐릭터 🎉</h1>
            <img src={character.img} alt={character.name} className="tw-w-40 tw-h-40" />
            <h2 className="tw-text-2xl tw-font-semibold tw-mt-4">{character.name}</h2>
            <p className="tw-text-lg tw-text-gray-600">{character.description}</p>
        </div>
    );
};

export default NextStepPage;
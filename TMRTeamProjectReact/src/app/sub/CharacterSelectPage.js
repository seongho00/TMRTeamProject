"use client";

import React, {useState} from 'react';

const characters = [
    {id: 1, name: '청년 창업가', description: '열정 넘치는 20대 창업가', img: '/images/young.png'},
    {id: 2, name: '중년 사장님', description: '노하우 가득한 베테랑', img: '/images/middle.png'},
    {id: 3, name: '은퇴한 투자자', description: '자본은 많지만 체력은 부족', img: '/images/retired.png'},
];

const CharacterSelectPage = ({onSelect}) => {
    const [selectedId, setSelectedId] = useState(null);

    const handleSelect = (id) => {
        setSelectedId(id);
    };

    const handleNext = () => {
        if (selectedId === null) return alert('캐릭터를 선택해주세요!');
        const character = characters.find(c => c.id === selectedId);
        onSelect(character); // 부모로 전달
    };

    return (
        <div className="tw-flex tw-justify-center tw-items-center tw-min-h-screen">
            <div className="tw-max-w-4xl tw-mx-auto tw-mt-12 tw-px-4">
                <h1 className="tw-text-3xl tw-font-bold tw-text-center tw-mb-8">🧑‍💼 캐릭터를 선택하세요</h1>
                <div className="tw-grid tw-grid-cols-1 sm:tw-grid-cols-3 tw-gap-6">
                    {characters.map((char) => (
                        <div
                            key={char.id}
                            onClick={() => handleSelect(char.id)}
                            className={`tw-cursor-pointer tw-border tw-rounded-2xl tw-p-8 tw-text-center tw-shadow-md tw-transition-all  ${
                                selectedId === char.id
                                    ? 'tw-border-blue-500 tw-ring-2 tw-ring-blue-300'
                                    : 'hover:tw-shadow-xl'
                            }`}
                        >
                            <img
                                src={char.img}
                                alt={char.name}
                                className="	tw-w-48 tw-h-48 tw-mx-auto tw-mb-4 tw-object-contain"
                            />
                            <h2 className="tw-text-xl tw-font-semibold">{char.name}</h2>
                            <p className="tw-text-sm tw-text-gray-600">{char.description}</p>
                        </div>
                    ))}
                </div>

                <div className="tw-text-center tw-mt-10">
                    <button
                        onClick={handleNext}
                        className="tw-bg-blue-500 tw-text-white tw-px-6 tw-py-2 tw-rounded-xl hover:tw-bg-blue-600 tw-transition"
                    >
                        다음 단계 →
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CharacterSelectPage;

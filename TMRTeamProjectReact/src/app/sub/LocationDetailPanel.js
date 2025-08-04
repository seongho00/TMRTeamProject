import React from 'react';

const LocationDetailPanel = ({ info, onClose }) => {
    if (!info) return null;

    return (
        <div className="fixed right-0 top-0 h-full w-[300px] bg-white shadow-lg p-4 z-50">
            <button
                onClick={onClose}
                className="text-sm text-gray-600 mb-4 hover:text-black"
            >
                ✖ 닫기
            </button>

            <h2 className="text-xl font-bold mb-2">{info.address}</h2>

            {/* 추가로 차트, 링크, 등등도 삽입 가능 */}
        </div>
    );
};

export default LocationDetailPanel;

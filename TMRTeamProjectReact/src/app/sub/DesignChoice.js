import { useState } from "react";

function DesignChoice({ onSelect }) {
    const designOptions = [
        { id: "basic", label: "저가형 디자인", cost: 25000000, popularity: 10, description: "저렴하지만 단순한 인테리어" },
        { id: "standard", label: "중급 디자인", cost: 30000000, popularity: 20, description: "균형 잡힌 인테리어, 무난한 인기도" },
        { id: "premium", label: "프리미엄 디자인", cost: 40000000, popularity: 30, description: "화려하고 세련된 인테리어, 높은 인기도" },
    ];

    const [selected, setSelected] = useState("");

    const handleChange = (e) => {
        const selectedId = e.target.value;
        const option = designOptions.find((opt) => opt.id === selectedId);
        setSelected(selectedId);
        if (option) onSelect(option);
    };

    const selectedOption = designOptions.find((opt) => opt.id === selected);

    return (
        <div className="tw-p-4 tw-bg-yellow-100 tw-rounded-lg tw-w-full tw-max-w-md">
            <p className="tw-font-bold tw-mb-2">인테리어 디자인 선택</p>

            <select
                value={selected}
                onChange={handleChange}
                className="tw-border tw-rounded-lg tw-px-3 tw-py-2 tw-w-full"
            >
                <option value="">-- 디자인을 선택하세요 --</option>
                {designOptions.map((opt) => (
                    <option key={opt.id} value={opt.id}>
                        {opt.label} (비용 {(opt.cost / 10000).toLocaleString()}만원)
                    </option>
                ))}
            </select>

            {selectedOption && (
                <div className="tw-mt-4 tw-p-3 tw-bg-white tw-border tw-rounded-lg">
                    <p className="tw-font-semibold">{selectedOption.label}</p>
                    <p className="tw-text-sm tw-text-gray-600">{selectedOption.description}</p>
                    <p className="tw-text-sm tw-text-gray-500">
                        비용: {(selectedOption.cost / 10000).toLocaleString()}만원 / 인기도: +{selectedOption.popularity}
                    </p>
                </div>
            )}
        </div>
    );
}

export default DesignChoice;

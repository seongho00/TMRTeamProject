import {useState} from "react";

function DesignChoice({onSelect}) {
    const designOptions = [
        {id: "basic", label: "저가형 디자인", cost: 2500000, popularity: 10, description: "저렴하지만 단순한 인테리어"},
        {id: "standard", label: "중급 디자인", cost: 3000000, popularity: 20, description: "균형 잡힌 인테리어, 무난한 인기도"},
        {id: "premium", label: "프리미엄 디자인", cost: 4000000, popularity: 30, description: "화려하고 세련된 인테리어, 높은 인기도"},
    ];

    const [selected, setSelected] = useState(null);

    const handleSelect = (opt) => {
        setSelected(opt);
        onSelect(opt); // 상위 컴포넌트에 전달
    };

    return (
        <div className="tw-p-4 tw-bg-yellow-100 tw-rounded-lg tw-mb-4 tw-w-full tw-max-w-2xl">
            <p className="tw-font-bold tw-mb-4">인테리어 디자인을 선택하세요</p>
            {designOptions.map((opt, idx) => (
                <button
                    key={idx}
                    onClick={() => handleSelect(opt)}
                    className={`tw-block tw-text-left tw-px-4 tw-py-3 tw-rounded-xl tw-mb-3 tw-w-full tw-transition-colors
            ${selected?.id === opt.id
                        ? "tw-bg-blue-600 tw-text-white"
                        : "tw-bg-white tw-border tw-border-gray-300 hover:tw-bg-blue-100"
                    }`}
                >
                    <p className="tw-font-semibold">{opt.label}</p>
                    <p className="tw-text-sm tw-text-gray-600">{opt.description}</p>
                    <p className="tw-text-sm tw-text-gray-500">
                        비용: {(opt.cost / 10000).toLocaleString()}만원 / 인기도: +{opt.popularity}
                    </p>
                </button>
            ))}
        </div>
    );
}


export default DesignChoice;

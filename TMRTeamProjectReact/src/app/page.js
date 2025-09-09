"use client";

import React, {useState} from "react";
import CharacterSelectPage from "./sub/CharacterSelectPage";
import BusinessSelectPage from "./sub/BusinessSelectPage";
import CostSettingPage from "./sub/CostSettingPage";
import LocationSelectPage from "./sub/LocationSelectPage";
import WeeklySimulationPage from "./sub/WeeklySimulationPage";
import ResultPage from "./sub/ResultPage";


import './globals.css';  // 파일 경로에 맞게 수정

const Page = () => {
    const [character, setCharacter] = useState(null);
    const [business, setBusiness] = useState(null);
    const [costs, setCosts] = useState(null);
    const [location, setLocation] = useState(null);
    const [isResult, setIsResult] = useState(false);

    const goBack = () => {
        if (costs) {
            setCosts(null);
        } else if (location) {
            setLocation(null);
        } else if (business) {
            setBusiness(null);
        } else if (character) {
            setCharacter(null);
        }
    };


    if (!character) {
        return <CharacterSelectPage onSelect={setCharacter} onBack={goBack}/>;
    }

    if (!business) {
        return <BusinessSelectPage onSelect={setBusiness} onBack={goBack}/>;
    }

    if (!location) return <LocationSelectPage onSelect={setLocation} onBack={goBack}/>;


    if (!costs)
        return (
            <CostSettingPage
                character={character}
                business={business}
                onSubmit={setCosts}
                onBack={goBack}
                location={location}
            />
        );

    // 시뮬레이션 결과 페이지
    if (isResult) {
        return <ResultPage history={history} onBack={() => window.location.reload()} />;
    }


    return (
        <WeeklySimulationPage
            character={character}
            business={business}
            location={location}
            initialCost={costs.initialCost}
            goLoan={costs.loanAmount}
            onFinish={setIsResult}
        />
    );

};

export default Page;
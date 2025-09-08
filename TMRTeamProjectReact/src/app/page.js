"use client";

import React, {useState} from "react";
import CharacterSelectPage from "./sub/CharacterSelectPage";
import BusinessSelectPage from "./sub/BusinessSelectPage";
import CostSettingPage from "./sub/CostSettingPage";
import LocationSelectPage from "./sub/LocationSelectPage";
import WeeklySimulationPage from "./sub/WeeklySimulationPage";
import LoanPage from "./sub/LoanPage";

import './globals.css';  // 파일 경로에 맞게 수정

const Page = () => {
    const [character, setCharacter] = useState(null);
    const [business, setBusiness] = useState(null);
    const [costs, setCosts] = useState(null);
    const [location, setLocation] = useState(null);
    const [loan, setLoan] = useState(null); // 대출 결과 저장

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
            />
        );

    // 비용이 자본보다 크면 → 대출 페이지
    if (costs < 0) {
        return (
            <LoanPage onSelect={setLoan}/>
        );
    }


    return (
        <WeeklySimulationPage
            character={character}
            business={business}
            location={location}
            initialCost={costs.initialCost}
        />
    );

};

export default Page;
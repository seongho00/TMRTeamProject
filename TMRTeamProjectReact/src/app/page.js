"use client";

import React, {useState} from "react";
import CharacterSelectPage from "./sub/CharacterSelectPage";
import BusinessSelectPage from "./sub/BusinessSelectPage";
import CostSettingPage from "./sub/CostSettingPage";
import LocationSelectPage from "./sub/LocationSelectPage";
import SimulationPage from "./sub/SimulationPage";

const Page = () => {
    const [character, setCharacter] = useState(null);
    const [business, setBusiness] = useState(null);
    const [costs, setCosts] = useState(null);
    const [location, setLocation] = useState(null);


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

    return (
        <SimulationPage
            character={character}
            business={business}
            location={location}
            onBack={goBack}
        />
    );
};

export default Page;
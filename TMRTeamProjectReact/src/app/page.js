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


    if (!character) {
        return <CharacterSelectPage onSelect={setCharacter}/>;
    }

    if (!business) {
        return <BusinessSelectPage onSelect={setBusiness}/>;
    }

    if (!location) return <LocationSelectPage onSelect={setLocation} />;

    if (!costs)
        return (
            <CostSettingPage
                character={character}
                business={business}
                onSubmit={setCosts}
            />
        );

    return (
        <SimulationPage
            character={character}
            business={business}
        />
    );
};

export default Page;
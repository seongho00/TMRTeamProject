"use client";

import React, { useState } from "react";
import CharacterSelectPage from "./sub/CharacterSelectPage";
import BusinessSelectPage from "./sub/BusinessSelectPage";
import SimulationPage from "./sub/SimulationPage";

const Page = () => {
    const [selectedCharacter, setSelectedCharacter] = useState(null);
    const [selectedBusiness, setSelectedBusiness] = useState(null);

    if (!selectedCharacter) {
        return <CharacterSelectPage onSelect={setSelectedCharacter} />;
    }

    if (!selectedBusiness) {
        return <BusinessSelectPage onSelect={setSelectedBusiness} />;
    }

    return (
        <SimulationPage
            character={selectedCharacter}
            business={selectedBusiness}
        />
    );
};

export default Page;
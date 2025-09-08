import React, { useState, useRef, useEffect } from "react";

function LoanPage({ debt, setDebt }) {
    const [amount, setAmount] = useState(0);
    const [rate, setRate] = useState(0.05);
    const [months, setMonths] = useState(12);

    const handleConfirm = () => {
        const monthlyPayment =
            (amount * (rate / 12)) /
            (1 - Math.pow(1 + rate / 12, -months));

        onSelect({
            amount,
            rate,
            months,
            monthlyPayment,
        });
    };

    return (
        <div>
            <h1>대출 시스템</h1>
            <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                placeholder="대출 금액"
            />
            <button onClick={handleConfirm}>확정</button>
        </div>
    );
}

export default LoanPage;

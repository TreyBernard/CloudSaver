import React from 'react';
import { analyzeBillingData } from "./api";

export default function UploadForm({ setResults, setLoading }) {
    const handleSubmit = async (e) => {
        e.preventDefault();
        const file = e.target.elements.billing.files[0];
        if (!file) {
            alert("Please choose a CSV file.");
            return;
        }

        setLoading(true);
        try {
            const res = await analyzeBillingData(file);
            setResults(res);
        } catch (err) {
            console.error(err);
            alert("Error analyzing file: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input type="file" name="billing" accept=".csv" />
            <button type="submit" style={{ marginLeft: 8 }}>Analyze</button>
        </form>
    );
}

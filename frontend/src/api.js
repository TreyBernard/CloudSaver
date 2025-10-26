import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function analyzeBillingData(file){
    const form = new FormData();
    form.append('file', file);
    const response = await axios.post(`${API_BASE_URL}/analyze`, form, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes
    });
    return response.data;
}
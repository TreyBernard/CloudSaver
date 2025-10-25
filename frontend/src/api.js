import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

export async function analyzeBillingData(formData) {
    const form = new FormData();
    form.append('file', formData.get('file'));
    const response = await axios.post(`${API_BASE_URL}/analyze`, form, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes
    });
    return response.data;
}
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to attach JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('kai_token');
        if (token) {
            console.log(`[API] Attaching token to ${config.url}`);
            config.headers.Authorization = `Bearer ${token}`;
        } else {
            console.warn(`[API] No token found for ${config.url}`);
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Add a response interceptor to handle 401s
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            console.warn("Unauthorized access - clearing token.");
            localStorage.removeItem('kai_token');
            localStorage.removeItem('kai_user');
            // We could trigger a window refresh or context update here, 
            // but let the components handle the missing token.
        }
        return Promise.reject(error);
    }
);

// Auth Endpoints
export const getSessionLogs = async (sessionId) => {
    const response = await api.get(`/api/v1/sessions/${sessionId}/logs`);
    return response.data;
};

export const getAnalysisStatus = async (sessionId) => {
    const response = await api.get(`/api/v1/status/${sessionId}`);
    return response.data;
};

export const loginUser = async (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const response = await api.post('/auth/token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
};

export const registerUser = async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
};

export const getMe = async () => {
    const response = await api.get('/auth/me');
    return response.data;
};

export const initiateAnalysis = async (ticker, riskPersona, userId) => {
    try {
        const response = await api.post('/api/v1/analyze', {
            ticker: ticker,
            persona: riskPersona.toLowerCase(),
            user_id: userId
        });
        return response.data;
    } catch (error) {
        console.error("API Error initiating analysis:", error);
        throw error;
    }
};

export const approveMandate = async (sessionId, challengeId) => {
    try {
        const response = await api.post(`/api/v1/approve/${sessionId}`, {
            challenge_id: challengeId,
            user_confirmation: 'approved'
        });
        return response.data;
    } catch (error) {
        console.error("API Error approving mandate:", error);
        throw error;
    }
};

export const rejectMandate = async (sessionId) => {
    try {
        const response = await api.post(`/api/v1/reject/${sessionId}`);
        return response.data;
    } catch (error) {
        console.error("API Error rejecting mandate:", error);
        throw error;
    }
};

// Market Data
export const getIndices = async () => {
    try {
        const response = await api.get('/api/v1/market/indices');
        return response.data;
    } catch (error) {
        console.error("API Error fetching indices:", error);
        return [];
    }
};

export const getQuote = async (symbol) => {
    try {
        const response = await api.get(`/api/v1/ticker/${symbol}/quote`);
        return response.data;
    } catch (error) {
        console.error("API Error fetching quote:", error);
        throw error;
    }
};

export const getHistory = async (symbol, period = '1d') => {
    try {
        const response = await api.get(`/api/v1/ticker/${symbol}/history?period=${period}`);
        return response.data;
    } catch (error) {
        console.error("API Error fetching history:", error);
        return [];
    }
};

// Chat with AI
export const getChatHistory = async (userId) => {
    try {
        const response = await api.get(`/api/v1/chat/history?user_id=${userId}`);
        return response.data;
    } catch (error) {
        console.error("API Error fetching chat history:", error);
        return [];
    }
};

export const chatWithAI = async (message, userId) => {
    try {
        const response = await api.post('/api/v1/chat', { message, user_id: userId });
        return response.data;
    } catch (error) {
        throw error.response?.data?.detail || 'Chat failed';
    }
};

export default api;

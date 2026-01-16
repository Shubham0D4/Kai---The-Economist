import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('kai_token'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // If we have a token but no user, we could fetch user info here
        // For now, we'll just trust the token exists
        if (token) {
            // Simplified: in real app, fetch /auth/me
            const savedUser = JSON.parse(localStorage.getItem('kai_user'));
            if (savedUser) setUser(savedUser);
        }
        setLoading(false);
    }, [token]);

    const login = (userData, userToken) => {
        setToken(userToken);
        setUser(userData);
        localStorage.setItem('kai_token', userToken);
        localStorage.setItem('kai_user', JSON.stringify(userData));
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('kai_token');
        localStorage.removeItem('kai_user');
    };

    const isAuthenticated = !!token;

    return (
        <AuthContext.Provider value={{ user, token, loading, login, logout, isAuthenticated }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);

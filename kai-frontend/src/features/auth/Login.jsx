import React, { useState } from 'react';
import { Form, Button, Card, Container, Alert } from 'react-bootstrap';
import { LogIn, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { loginUser, getMe } from '../../services/api';
import { useNavigate, Link } from 'react-router-dom';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const data = await loginUser(username, password);
            localStorage.setItem('kai_token', data.access_token);
            const user = await getMe();
            login(user, data.access_token);
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed. Please check credentials.');
            localStorage.removeItem('kai_token');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="kai-layout-center kai-auth-container">
            <div className="w-100" style={{ maxWidth: '400px' }}>
                <Card className="auth-card border-0 rounded-4 overflow-hidden">
                    <div className="auth-header p-4 text-white text-center">
                        <div className="bg-white bg-opacity-10 rounded-circle d-inline-flex p-3 mb-3">
                            <ShieldCheck size={40} className="text-white" />
                        </div>
                        <h3 className="fw-bold mb-1">Kai Access</h3>
                        <p className="small opacity-75 mb-0 text-uppercase tracking-wider">Analyst Cockpit</p>
                    </div>
                    <Card.Body className="p-4 p-md-5">
                        {error && <Alert variant="danger" className="py-2 small border-0 bg-danger bg-opacity-10 text-danger">{error}</Alert>}
                        <Form onSubmit={handleSubmit}>
                            <Form.Group className="mb-3">
                                <Form.Label className="small fw-semibold text-muted">Username</Form.Label>
                                <Form.Control
                                    type="text"
                                    placeholder="analyst_name"
                                    className="py-2 rounded-3"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                />
                            </Form.Group>

                            <Form.Group className="mb-4">
                                <Form.Label className="small fw-semibold text-muted">Password</Form.Label>
                                <Form.Control
                                    type="password"
                                    placeholder="••••••••"
                                    className="py-2 rounded-3"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                            </Form.Group>

                            <div className="d-grid gap-2 mb-4">
                                <Button variant="primary" type="submit" size="lg" disabled={loading} className="fw-bold py-3 rounded-3 shadow-sm">
                                    {loading ? 'Authenticating...' : <><LogIn size={20} className="me-2" /> Sign In</>}
                                </Button>
                            </div>

                            <div className="text-center">
                                <span className="small text-muted">Missing credentials? </span>
                                <Link to="/register" className="small fw-bold text-primary text-decoration-none">Initialize Credentials</Link>
                            </div>
                        </Form>
                    </Card.Body>
                </Card>
                <div className="text-center mt-4 text-muted small">
                    <span className="opacity-50">Powered by</span> <strong className="text-primary">MCP Convergence</strong>
                </div>
            </div>
        </div>
    );
};

export default Login;

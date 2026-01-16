import React, { useState } from 'react';
import { Form, Button, Card, Container, Alert } from 'react-bootstrap';
import { UserPlus, ArrowLeft } from 'lucide-react';
import { registerUser } from '../../services/api';
import { useNavigate, Link } from 'react-router-dom';

const Register = () => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        role: 'analyst'
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await registerUser(formData);
            setSuccess(true);
            setTimeout(() => navigate('/login'), 2000);
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed.');
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
                            <UserPlus size={40} className="text-white" />
                        </div>
                        <h3 className="fw-bold mb-1">New Identity</h3>
                        <p className="small opacity-75 mb-0 text-uppercase tracking-wider">Analyst Onboarding</p>
                    </div>
                    <Card.Body className="p-4 p-md-5">
                        {error && <Alert variant="danger" className="py-2 small border-0 bg-danger bg-opacity-10 text-danger">{error}</Alert>}
                        {success && <Alert variant="success" className="py-2 small border-0 bg-success bg-opacity-10 text-success">Registration successful! Redirecting...</Alert>}

                        <Form onSubmit={handleSubmit}>
                            <Form.Group className="mb-3">
                                <Form.Label className="small fw-semibold text-muted">Username</Form.Label>
                                <Form.Control
                                    type="text"
                                    placeholder="Choose username"
                                    className="py-2 rounded-3"
                                    value={formData.username}
                                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                                    required
                                />
                            </Form.Group>

                            <Form.Group className="mb-3">
                                <Form.Label className="small fw-semibold text-muted">Email</Form.Label>
                                <Form.Control
                                    type="email"
                                    placeholder="analyst@kai.ai"
                                    className="py-2 rounded-3"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    required
                                />
                            </Form.Group>

                            <Form.Group className="mb-4">
                                <Form.Label className="small fw-semibold text-muted">Password</Form.Label>
                                <Form.Control
                                    type="password"
                                    placeholder="••••••••"
                                    className="py-2 rounded-3"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    required
                                />
                            </Form.Group>

                            <div className="d-grid gap-2 mb-4">
                                <Button variant="primary" type="submit" size="lg" disabled={loading || success} className="fw-bold py-3 rounded-3 shadow-sm">
                                    {loading ? 'Initializing...' : 'Create Account'}
                                </Button>
                            </div>

                            <div className="text-center">
                                <Link to="/login" className="small text-muted d-flex align-items-center justify-content-center gap-1 text-decoration-none hover-text-primary transition-all">
                                    <ArrowLeft size={14} /> Back to Sign In
                                </Link>
                            </div>
                        </Form>
                    </Card.Body>
                </Card>
            </div>
        </div>
    );
};

export default Register;

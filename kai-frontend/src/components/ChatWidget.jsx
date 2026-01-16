import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import { chatWithAI, getChatHistory } from '../services/api';
import { useAuth } from '../context/AuthContext';
import ReactMarkdown from 'react-markdown';

const ChatWidget = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef(null);
    const { user } = useAuth();

    // Initial load: Fetch history
    useEffect(() => {
        const loadHistory = async () => {
            if (user && isOpen) {
                try {
                    const history = await getChatHistory(user.username);
                    if (history.length > 0) {
                        // Transform backend response to UI format if needed
                        const formatted = history.map(msg => ({
                            role: msg.role || 'assistant', // Default to assistant if undefined?
                            content: msg.response || msg.message // handle naming diffs
                        }));
                        setMessages(formatted);
                    } else {
                        // Default welcome if empty
                        setMessages([
                            { role: 'assistant', content: 'Hello! I am Kai, your AI investment copilot. How can I help you navigate the markets today?' }
                        ]);
                    }
                } catch (e) {
                    console.error("Failed to load chat history", e);
                }
            }
        };

        loadHistory();
    }, [user, isOpen]);

    // Scroll to bottom
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isOpen]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || !user) return;

        const userMsg = input;
        setInput('');

        // Add user message immediately
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setLoading(true);

        try {
            const result = await chatWithAI(userMsg, user.username);
            setMessages(prev => [...prev, { role: 'assistant', content: result.response }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I'm having trouble connecting to the network." }]);
        } finally {
            setLoading(false);
        }
    };

    if (!user) return null; // Don't show if not logged in

    return (
        <div className="position-fixed bottom-0 end-0 m-4" style={{ zIndex: 1050 }}>
            {/* Toggle Button */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="btn btn-primary rounded-circle shadow-lg d-flex align-items-center justify-content-center animate-bounce-subtle btn-glow"
                    style={{ width: '60px', height: '60px' }}
                >
                    <MessageCircle size={28} />
                </button>
            )}

            {/* Chat Window */}
            {isOpen && (
                <div className="card glass-panel shadow-2xl overflow-hidden animate-slide-up" style={{ width: '380px', height: '600px', display: 'flex', flexDirection: 'column' }}>
                    <div className="card-header bg-primary text-white p-3 d-flex justify-content-between align-items-center">
                        <div className="d-flex align-items-center gap-2">
                            <div className="bg-white rounded-circle p-1">
                                <Bot size={20} className="text-primary" />
                            </div>
                            <div>
                                <h6 className="mb-0 fw-bold">Kai Copilot</h6>
                                <small className="opacity-75" style={{ fontSize: '0.7em' }}>Online via Groq LPU</small>
                            </div>
                        </div>
                        <button onClick={() => setIsOpen(false)} className="btn btn-sm btn-link text-white p-0">
                            <X size={20} />
                        </button>
                    </div>

                    <div className="card-body p-3 overflow-auto custom-scrollbar flex-grow-1 bg-white bg-opacity-10" style={{ backdropFilter: 'blur(10px)' }}>
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`d-flex mb-3 ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}>
                                {msg.role === 'assistant' && (
                                    <div className="flex-shrink-0 me-2 mt-1">
                                        <div className="bg-primary bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center" style={{ width: '32px', height: '32px' }}>
                                            <Bot size={18} className="text-primary" />
                                        </div>
                                    </div>
                                )}
                                <div
                                    className={`p-3 rounded-4 shadow-sm text-break ${msg.role === 'user' ? 'bg-primary text-white rounded-tr-none' : 'bg-white text-dark rounded-tl-none'}`}
                                    style={{ maxWidth: '85%', fontSize: '0.9rem', wordWrap: 'break-word' }}
                                >
                                    {msg.role === 'assistant' ? (
                                        <ReactMarkdown
                                            components={{
                                                p: ({ node, ...props }) => <p className="mb-1" {...props} />,
                                                ul: ({ node, ...props }) => <ul className="mb-1 ps-3" {...props} />,
                                                li: ({ node, ...props }) => <li className="mb-0" {...props} />,
                                                strong: ({ node, ...props }) => <strong className="fw-bold text-dark" {...props} />
                                            }}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                                {msg.role === 'user' && (
                                    <div className="flex-shrink-0 ms-2 mt-1">
                                        <div className="bg-light rounded-circle d-flex align-items-center justify-content-center" style={{ width: '32px', height: '32px' }}>
                                            <User size={18} className="text-secondary" />
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                        {loading && (
                            <div className="d-flex justify-content-start mb-3">
                                <div className="bg-white p-3 rounded-4 rounded-tl-none shadow-sm">
                                    <div className="typing-dot-container">
                                        <span className="typing-dot"></span>
                                        <span className="typing-dot"></span>
                                        <span className="typing-dot"></span>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={bottomRef} />
                    </div>

                    <div className="card-footer bg-white p-3 border-top">
                        <form onSubmit={handleSend} className="d-flex gap-2">
                            <input
                                type="text"
                                className="form-control rounded-pill bg-light border-0 px-3"
                                placeholder="Ask about the market..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                disabled={loading}
                            />
                            <button type="submit" className="btn btn-primary rounded-circle d-flex align-items-center justify-content-center p-0" style={{ width: '38px', height: '38px' }} disabled={loading || !input.trim()}>
                                <Send size={18} />
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatWidget;

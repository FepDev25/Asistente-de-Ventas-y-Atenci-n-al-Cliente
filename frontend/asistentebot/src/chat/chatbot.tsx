// src/chat/chatbot.tsx - VERSIÓN CON RAG DOCS VISUALES (OPCIONAL)
import React, { useState, useRef, useEffect } from 'react';
import { chatService, ragService } from '../services/graphqlservices';
import type { SemanticSearchResult, RAGDoc } from '../services/graphqlservices';
import './chatbot.css';
import { FiMessageCircle, FiX, FiSend, FiAlertCircle, FiRefreshCw, FiFileText } from 'react-icons/fi';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  error?: string | null;
  ragDocs?: RAGDoc[]; // NUEVO: documentos RAG usados
}

const ChatBot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: '¡Hola! Soy Alex, tu asistente de ventas. ¿En qué puedo ayudarte hoy?',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showRagDocs, setShowRagDocs] = useState(false); // Toggle para mostrar docs RAG
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) inputRef.current.focus();
  }, [isOpen]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const text = inputMessage.trim();
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      // OPCIÓN 1: Solo usar chatService (RAG ya incluido internamente)
      const response: SemanticSearchResult = await chatService.sendMessage(text);

      // OPCIÓN 2 (OPCIONAL): Obtener documentos RAG por separado para mostrarlos
      let ragDocs: RAGDoc[] = [];
      if (showRagDocs) {
        try {
          ragDocs = await ragService.searchDocs(text, 3);
        } catch (err) {
          console.warn('No se pudieron obtener docs RAG:', err);
        }
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer || 'Lo siento, no obtuve respuesta.',
        sender: 'bot',
        timestamp: new Date(),
        error: response.error,
        ragDocs: ragDocs.length > 0 ? ragDocs : undefined
      };

      setTimeout(() => {
        setMessages(prev => [...prev, botMessage]);
        setIsTyping(false);
      }, 400);

    } catch (err) {
      console.error('Error enviando mensaje:', err);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Lo siento, hubo un problema conectando con el servidor.',
        sender: 'bot',
        timestamp: new Date(),
        error: 'connection_error'
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleChat = () => setIsOpen(o => !o);

  const handleNewConversation = () => {
    chatService.resetSession();
    setMessages([
      {
        id: Date.now().toString(),
        text: '¡Hola de nuevo! Iniciamos una nueva conversación. ¿En qué puedo ayudarte?',
        sender: 'bot',
        timestamp: new Date()
      }
    ]);
  };

  const getErrorIcon = (error: string | null | undefined) => {
    if (!error) return null;
    const errorMessages: Record<string, string> = {
      'timeout': 'La respuesta tardó mucho tiempo',
      'service_unavailable': 'Servicio temporalmente no disponible',
      'internal_error': 'Error interno del servidor',
      'connection_error': 'Error de conexión',
      'graphql_error': 'Error en la consulta'
    };
    return (
      <div className="message-error" title={errorMessages[error] || 'Error'}>
        <FiAlertCircle size={14} />
      </div>
    );
  };

  return (
    <>
      <button 
        className={`chat-toggle-btn ${isOpen ? 'open' : ''}`}
        onClick={toggleChat}
        aria-label={isOpen ? 'Cerrar chat' : 'Abrir chat'}
      >
        {isOpen ? <FiX size={28} /> : <FiMessageCircle size={28} />}
      </button>

      <div className={`chat-window ${isOpen ? 'open' : ''}`}>
        <div className="chat-header">
          <div className="chat-header-info">
            <div className="bot-avatar">🤖</div>
            <div>
              <h3>Alex - Asistente de Ventas</h3>
              <p className="status"><span className="status-dot"></span> En línea</p>
            </div>
          </div>
          <div className="chat-header-actions">
            {/* Toggle para mostrar docs RAG (debugging) */}
            <button 
              className={`icon-button ${showRagDocs ? 'active' : ''}`}
              onClick={() => setShowRagDocs(!showRagDocs)} 
              title={showRagDocs ? 'Ocultar docs RAG' : 'Mostrar docs RAG'}
              aria-label="Toggle RAG docs"
            >
              <FiFileText size={18} />
            </button>
            <button className="icon-button" onClick={handleNewConversation} title="Nueva conversación" aria-label="Nueva conversación">
              <FiRefreshCw size={18} />
            </button>
            <button className="close-chat-btn" onClick={toggleChat} aria-label="Cerrar chat">
              <FiX size={24} />
            </button>
          </div>
        </div>

        <div className="chat-messages" role="log" aria-live="polite">
          {messages.map((message) => (
            <div key={message.id}>
              <div className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}>
                <div className="message-content">
                  <p>{message.text}</p>
                  <div className="message-footer">
                    <span className="message-time">
                      {message.timestamp.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {getErrorIcon(message.error)}
                  </div>
                </div>
              </div>

              {/* MOSTRAR DOCS RAG SI EXISTEN */}
              {message.ragDocs && message.ragDocs.length > 0 && (
                <div className="rag-docs-container">
                  <div className="rag-docs-header">
                    <FiFileText size={14} />
                    <span>Documentos consultados ({message.ragDocs.length})</span>
                  </div>
                  {message.ragDocs.map((doc, idx) => (
                    <div key={idx} className="rag-doc">
                      <div className="rag-doc-header">
                        <span className="rag-doc-category">{doc.category}</span>
                        <span className="rag-doc-score">
                          {(doc.relevance_score * 100).toFixed(0)}% relevante
                        </span>
                      </div>
                      <p className="rag-doc-content">{doc.content.slice(0, 200)}...</p>
                      <span className="rag-doc-source">Fuente: {doc.source}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {isTyping && (
            <div className="message bot-message">
              <div className="message-content typing">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <input
            ref={inputRef}
            type="text"
            placeholder="Escribe tu mensaje..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            className="chat-input"
            disabled={isTyping}
            aria-label="Mensaje"
            autoComplete="off"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isTyping}
            className="send-button"
            aria-label="Enviar mensaje"
          >
            <FiSend size={20} />
          </button>
        </div>

        <div className="chat-footer">
          <small>Session ID: {chatService.getSessionId().slice(-8)}</small>
          {showRagDocs && <small className="rag-mode-indicator"> • Modo RAG activo</small>}
        </div>
      </div>
    </>
  );
};

export default ChatBot;
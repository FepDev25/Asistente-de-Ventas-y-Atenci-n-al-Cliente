// chatbot.tsx - MEJORADO con Markdown y Diseño Brutal Minimalista
import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { chatService, ragService } from '../services/graphqlservices';
import type { SemanticSearchResult, RAGDoc } from '../services/graphqlservices';
import './chatbot.css';
import {
  FiMessageCircle,
  FiX,
  FiSend,
  FiAlertCircle,
  FiRefreshCw,
  FiFileText,
  FiCheck,
  FiClock
} from 'react-icons/fi';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  error?: string | null;
  ragDocs?: RAGDoc[];
  status?: 'sending' | 'sent' | 'error';
}

interface QuickAction {
  id: string;
  label: string;
  message: string;
}

const ChatBot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: '¡Hola! Soy **Alex**, tu asistente de ventas. 👋\n\nEstoy aquí para ayudarte con:\n- Información de productos\n- Recomendaciones personalizadas\n- Preguntas sobre envíos y pagos\n\n¿En qué puedo ayudarte hoy?',
      sender: 'bot',
      timestamp: new Date(),
      status: 'sent'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showRagDocs, setShowRagDocs] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const chatMessagesRef = useRef<HTMLDivElement>(null);

  // Quick actions para sugerencias rápidas
  const quickActions: QuickAction[] = [
    { id: '1', label: '📦 Ver productos', message: 'Muéstrame los productos disponibles' },
    { id: '2', label: '🎯 Recomendaciones', message: 'Dame recomendaciones personalizadas' },
    { id: '3', label: '💳 Formas de pago', message: '¿Cuáles son las formas de pago?' },
    { id: '4', label: '🚚 Envíos', message: 'Información sobre envíos' }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
      setUnreadCount(0);
    }
  }, [isOpen]);

  // Simular mensajes no leídos cuando el chat está cerrado
  useEffect(() => {
    if (!isOpen && messages.length > 1) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.sender === 'bot') {
        setUnreadCount(prev => prev + 1);
      }
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (messageText?: string) => {
    const text = (messageText || inputMessage).trim();
    if (!text) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date(),
      status: 'sending'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    // Actualizar estado a "sent"
    setTimeout(() => {
      setMessages(prev =>
        prev.map(msg =>
          msg.id === userMessage.id ? { ...msg, status: 'sent' } : msg
        )
      );
    }, 300);

    try {
      // Llamar al servicio de chat
      const response: SemanticSearchResult = await chatService.sendMessage(text);

      // Obtener documentos RAG si está habilitado
      let ragDocs: RAGDoc[] = [];
      if (showRagDocs) {
        try {
          ragDocs = await ragService.searchDocs(text, 3);
        } catch (err) {
          console.warn('No se pudieron obtener docs RAG:', err);
        }
      }

      // Simular tiempo de "escritura" más realista
      const typingDelay = Math.min(response.answer.length * 10, 2000);

      setTimeout(() => {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: response.answer || 'Lo siento, no obtuve respuesta.',
          sender: 'bot',
          timestamp: new Date(),
          error: response.error,
          ragDocs: ragDocs.length > 0 ? ragDocs : undefined,
          status: 'sent'
        };

        setMessages(prev => [...prev, botMessage]);
        setIsTyping(false);
      }, typingDelay);

    } catch (err) {
      console.error('Error enviando mensaje:', err);

      setTimeout(() => {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: '❌ **Error de conexión**\n\nLo siento, hubo un problema conectando con el servidor. Por favor, intenta de nuevo.',
          sender: 'bot',
          timestamp: new Date(),
          error: 'connection_error',
          status: 'error'
        };

        setMessages(prev => [...prev, errorMessage]);
        setIsTyping(false);
      }, 500);
    }
  };

  const handleQuickAction = (action: QuickAction) => {
    handleSendMessage(action.message);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleChat = () => {
    setIsOpen(o => !o);
  };

  const handleNewConversation = () => {
    chatService.resetSession();
    setMessages([
      {
        id: Date.now().toString(),
        text: '🔄 **Nueva conversación iniciada**\n\n¡Hola de nuevo! Estoy listo para ayudarte. ¿En qué puedo asistirte?',
        sender: 'bot',
        timestamp: new Date(),
        status: 'sent'
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
        <span>{errorMessages[error] || 'Error'}</span>
      </div>
    );
  };

  const getMessageStatusIcon = (status?: 'sending' | 'sent' | 'error') => {
    switch (status) {
      case 'sending':
        return <FiClock size={12} style={{ opacity: 0.5 }} />;
      case 'sent':
        return <FiCheck size={12} style={{ opacity: 0.6 }} />;
      case 'error':
        return <FiAlertCircle size={12} style={{ color: 'var(--error)' }} />;
      default:
        return null;
    }
  };

  return (
    <>
      {/* Toggle Button */}
      <button
        className={`chat-toggle-btn ${isOpen ? 'open' : ''}`}
        onClick={toggleChat}
        aria-label={isOpen ? 'Cerrar chat' : 'Abrir chat'}
      >
        {isOpen ? (
          <FiX size={32} />
        ) : (
          <>
            <FiMessageCircle size={32} />
            {unreadCount > 0 && (
              <span className="chat-badge">{unreadCount}</span>
            )}
          </>
        )}
      </button>

      {/* Chat Window */}
      <div className={`chat-window ${isOpen ? 'open' : ''}`}>
        {/* Header */}
        <div className="chat-header">
          <div className="chat-header-info">
            <div className={`bot-avatar ${isTyping ? 'typing' : ''}`}>
              🤖
            </div>
            <div>
              <h3>Alex - Asistente de Ventas</h3>
              <p className="status">
                <span className="status-dot"></span>
                {isTyping ? 'Escribiendo...' : 'En línea'}
              </p>
            </div>
          </div>

          <div className="chat-header-actions">
            <button
              className={`icon-button ${showRagDocs ? 'active' : ''}`}
              onClick={() => setShowRagDocs(!showRagDocs)}
              title={showRagDocs ? 'Ocultar docs RAG' : 'Mostrar docs RAG'}
              aria-label="Toggle RAG docs"
            >
              <FiFileText size={18} />
            </button>
            <button
              className="icon-button"
              onClick={handleNewConversation}
              title="Nueva conversación"
              aria-label="Nueva conversación"
            >
              <FiRefreshCw size={18} />
            </button>
            <button
              className="close-chat-btn"
              onClick={toggleChat}
              aria-label="Cerrar chat"
            >
              <FiX size={20} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div
          className="chat-messages"
          ref={chatMessagesRef}
          role="log"
          aria-live="polite"
        >
          {messages.map((message, index) => (
            <div key={message.id}>
              {/* Message Bubble */}
              <div
                className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <div className="message-content">
                  {message.sender === 'bot' ? (
                    <ReactMarkdown
                      components={{
                        // Personalizar componentes de markdown
                        p: ({ node, ...props }) => <p {...props} />,
                        strong: ({ node, ...props }) => <strong {...props} />,
                        em: ({ node, ...props }) => <em {...props} />,
                        // Lo que cambié específicamente en la línea de 'code':
                        code({ node, className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '');

                          // Si hay un match de lenguaje, lo tratamos como bloque (pre)
                          return match ? (
                            <pre className="code-block">
                              <code className={className} {...props}>{children}</code>
                            </pre>
                          ) : (
                            <code className="code-inline" {...props}>{children}</code>
                          );
                        },
                        ul: ({ node, ...props }) => <ul {...props} />,
                        ol: ({ node, ...props }) => <ol {...props} />,
                        li: ({ node, ...props }) => <li {...props} />,
                        h1: ({ node, ...props }) => <h1 {...props} />,
                        h2: ({ node, ...props }) => <h2 {...props} />,
                        h3: ({ node, ...props }) => <h3 {...props} />,
                        a: ({ node, ...props }) => (
                          <a {...props} target="_blank" rel="noopener noreferrer" />
                        ),
                        blockquote: ({ node, ...props }) => <blockquote {...props} />,
                        hr: ({ node, ...props }) => <hr {...props} />
                      }}
                    >
                      {message.text}
                    </ReactMarkdown>
                  ) : (
                    <p>{message.text}</p>
                  )}

                  <div className="message-footer">
                    <span className="message-time">
                      {message.timestamp.toLocaleTimeString('es-ES', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                    {message.sender === 'user' && getMessageStatusIcon(message.status)}
                    {getErrorIcon(message.error)}
                  </div>
                </div>
              </div>

              {/* RAG Documents Display */}
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
                      <p className="rag-doc-content">
                        {doc.content.slice(0, 200)}...
                      </p>
                      <span className="rag-doc-source">
                        Fuente: {doc.source}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Quick Actions - Solo mostrar después del primer mensaje del bot */}
              {index === 0 && message.sender === 'bot' && (
                <div className="quick-actions">
                  {quickActions.map(action => (
                    <button
                      key={action.id}
                      className="quick-action"
                      onClick={() => handleQuickAction(action)}
                      disabled={isTyping}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="message bot-message">
              <div className="message-content typing">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
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
            maxLength={500}
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputMessage.trim() || isTyping}
            className="send-button"
            aria-label="Enviar mensaje"
          >
            <FiSend size={22} />
          </button>
        </div>

        {/* Footer */}
        <div className="chat-footer">
          <small>Session: {chatService.getSessionId().slice(-8)}</small>
          {showRagDocs && (
            <small className="rag-mode-indicator"> • Modo RAG activo</small>
          )}
        </div>
      </div>
    </>
  );
};

export default ChatBot;
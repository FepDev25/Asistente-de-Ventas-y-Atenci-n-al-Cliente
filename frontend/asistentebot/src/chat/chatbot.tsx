// src/components/ChatBot/ChatBot.tsx
import React, { useState, useRef, useEffect } from 'react';
import type { Message } from '../types/types';
import { chatAPI } from '../services/api';
import './chatbot.css';
import { FiMessageCircle, FiX, FiSend } from 'react-icons/fi';

const ChatBot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: '¡Hola! Soy tu asistente de ventas. ¿En qué puedo ayudarte hoy?',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      // Intenta enviar al backend
      const response = await chatAPI.sendMessage(inputMessage).catch(() => {
        // Si falla, usa respuesta mock
        return getMockResponse(inputMessage);
      });

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: typeof response === 'string' ? response : response.text,
        sender: 'bot',
        timestamp: new Date()
      };

      setTimeout(() => {
        setMessages(prev => [...prev, botMessage]);
        setIsTyping(false);
      }, 500);
    } catch (error) {
      setIsTyping(false);
      console.error('Error enviando mensaje:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* Botón flotante */}
      <button 
        className={`chat-toggle-btn ${isOpen ? 'open' : ''}`}
        onClick={toggleChat}
      >
        {isOpen ? <FiX size={28} /> : <FiMessageCircle size={28} />}
      </button>

      {/* Ventana de chat */}
      <div className={`chat-window ${isOpen ? 'open' : ''}`}>
        <div className="chat-header">
          <div className="chat-header-info">
            <div className="bot-avatar">🤖</div>
            <div>
              <h3>Asistente de Ventas</h3>
              <p className="status">En línea</p>
            </div>
          </div>
          <button className="close-chat-btn" onClick={toggleChat}>
            <FiX size={24} />
          </button>
        </div>

        <div className="chat-messages">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
            >
              <div className="message-content">
                <p>{message.text}</p>
                <span className="message-time">
                  {message.timestamp.toLocaleTimeString('es-ES', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            </div>
          ))}
          
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

        <div className="chat-input-container">
          <input
            type="text"
            placeholder="Escribe tu mensaje..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            className="chat-input"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim()}
            className="send-button"
          >
            <FiSend size={20} />
          </button>
        </div>
      </div>
    </>
  );
};

// Respuestas mock para desarrollo
const getMockResponse = (message: string): string => {
  const lowerMessage = message.toLowerCase();
  
  if (lowerMessage.includes('precio') || lowerMessage.includes('cuesta')) {
    return 'Los precios de nuestros productos varían. ¿Hay algún producto específico del que quieras saber el precio?';
  }
  
  if (lowerMessage.includes('envío') || lowerMessage.includes('entrega')) {
    return 'Realizamos envíos a todo el país. El tiempo de entrega es de 3-5 días hábiles. ¿Necesitas información sobre alguna dirección en particular?';
  }
  
  if (lowerMessage.includes('pago') || lowerMessage.includes('tarjeta')) {
    return 'Aceptamos tarjetas de crédito, débito, transferencias bancarias y pagos en efectivo. ¿Cuál prefieres?';
  }
  
  if (lowerMessage.includes('laptop') || lowerMessage.includes('computadora')) {
    return 'Tenemos varias opciones de laptops disponibles. Te recomiendo revisar nuestra sección de Electrónica donde encontrarás las especificaciones completas.';
  }
  
  if (lowerMessage.includes('stock') || lowerMessage.includes('disponible')) {
    return 'Puedes ver la disponibilidad de cada producto directamente en su tarjeta. Si hay pocas unidades, aparecerá una etiqueta indicándolo.';
  }
  
  if (lowerMessage.includes('gracias')) {
    return '¡De nada! Estoy aquí para ayudarte. ¿Hay algo más en lo que pueda asistirte?';
  }
  
  if (lowerMessage.includes('hola') || lowerMessage.includes('buenos')) {
    return '¡Hola! ¿En qué puedo ayudarte hoy? Puedo responder preguntas sobre productos, precios, envíos y más.';
  }
  
  return 'Entiendo tu consulta. ¿Podrías ser más específico? Puedo ayudarte con información sobre productos, precios, envíos, métodos de pago y más.';
};

export default ChatBot;
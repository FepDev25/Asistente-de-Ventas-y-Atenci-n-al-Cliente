// src/pages/OrderDetail/OrderDetail.tsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './orderdetail.css';
import { 
  FiArrowLeft, FiPackage, FiMapPin, FiTruck, 
  FiCheck, FiClock, FiDownload 
} from 'react-icons/fi';

interface OrderItem {
  id: string;
  name: string;
  quantity: number;
  price: number;
  image: string;
  sku: string;
}

interface Order {
  id: string;
  orderNumber: string;
  date: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  total: number;
  subtotal: number;
  shipping: number;
  tax: number;
  items: OrderItem[];
  shippingAddress: {
    name: string;
    street: string;
    city: string;
    state: string;
    zipCode: string;
    phone: string;
  };
  timeline: TimelineEvent[];
}

interface TimelineEvent {
  status: string;
  date: string;
  message: string;
  completed: boolean;
}

const OrderDetail: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrderDetail();
  }, [orderId]);

  const loadOrderDetail = async () => {
    try {
      setLoading(true);
      // TODO: Reemplazar con API real
      // const response = await ordersAPI.getById(orderId);
      // setOrder(response.data);

      // Datos de ejemplo
      const mockOrder: Order = {
        id: orderId || '1',
        orderNumber: 'ORD-2024-001',
        date: '2024-01-28T10:30:00',
        status: 'delivered',
        subtotal: 1329.98,
        shipping: 15.00,
        tax: 132.99,
        total: 1477.97,
        items: [
          {
            id: '1',
            name: 'Laptop Gaming ROG Strix',
            quantity: 1,
            price: 1299.99,
            image: 'https://via.placeholder.com/150x150?text=Laptop',
            sku: 'LAP-001'
          },
          {
            id: '2',
            name: 'Mouse Inalámbrico Logitech',
            quantity: 1,
            price: 29.99,
            image: 'https://via.placeholder.com/150x150?text=Mouse',
            sku: 'MOU-002'
          }
        ],
        shippingAddress: {
          name: 'Juan Pérez',
          street: 'Av. Principal 123, Apto 4B',
          city: 'Quito',
          state: 'Pichincha',
          zipCode: '170501',
          phone: '+593 99 123 4567'
        },
        timeline: [
          {
            status: 'Pedido recibido',
            date: '2024-01-28T10:30:00',
            message: 'Tu pedido ha sido recibido y está siendo procesado',
            completed: true
          },
          {
            status: 'En preparación',
            date: '2024-01-28T14:00:00',
            message: 'Estamos preparando tu pedido para el envío',
            completed: true
          },
          {
            status: 'Enviado',
            date: '2024-01-29T09:00:00',
            message: 'Tu pedido está en camino',
            completed: true
          },
          {
            status: 'Entregado',
            date: '2024-01-30T16:45:00',
            message: 'Pedido entregado exitosamente',
            completed: true
          }
        ]
      };

      setOrder(mockOrder);
    } catch (error) {
      console.error('Error cargando orden:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusInfo = (status: string) => {
    const statusMap = {
      pending: { label: 'Pendiente', color: '#f59e0b', icon: FiClock },
      processing: { label: 'Procesando', color: '#3b82f6', icon: FiPackage },
      shipped: { label: 'Enviado', color: '#8b5cf6', icon: FiTruck },
      delivered: { label: 'Entregado', color: '#10b981', icon: FiCheck },
      cancelled: { label: 'Cancelado', color: '#ef4444', icon: FiClock }
    };
    return statusMap[status as keyof typeof statusMap] || statusMap.pending;
  };

  if (loading) {
    return (
      <div className="order-detail-container">
        <div className="loading">Cargando detalle...</div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="order-detail-container">
        <div className="error-message">Orden no encontrada</div>
      </div>
    );
  }

  const statusInfo = getStatusInfo(order.status);
  const StatusIcon = statusInfo.icon;

  return (
    <div className="order-detail-container">
      {/* Header */}
      <div className="detail-header">
        <button className="back-button" onClick={() => navigate('/ordenes')}>
          <FiArrowLeft size={20} />
          Volver
        </button>

        <div className="header-info">
          <h1>Orden {order.orderNumber}</h1>
          <span 
            className="status-badge"
            style={{ backgroundColor: statusInfo.color }}
          >
            <StatusIcon size={16} />
            {statusInfo.label}
          </span>
        </div>

        <div className="header-date">
          Realizada el {new Date(order.date).toLocaleDateString('es-ES', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>

      <div className="detail-content">
        {/* Timeline */}
        <div className="timeline-section">
          <h2>Estado del Pedido</h2>
          <div className="timeline">
            {order.timeline.map((event, index) => (
              <div 
                key={index} 
                className={`timeline-item ${event.completed ? 'completed' : 'pending'}`}
              >
                <div className="timeline-marker">
                  {event.completed ? <FiCheck size={16} /> : <FiClock size={16} />}
                </div>
                <div className="timeline-content">
                  <div className="timeline-status">{event.status}</div>
                  <div className="timeline-date">
                    {new Date(event.date).toLocaleDateString('es-ES', {
                      day: '2-digit',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                  <div className="timeline-message">{event.message}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Productos */}
        <div className="items-section">
          <h2>Productos ({order.items.length})</h2>
          <div className="items-list">
            {order.items.map(item => (
              <div key={item.id} className="item-card">
                <img src={item.image} alt={item.name} className="item-image" />
                <div className="item-info">
                  <h3>{item.name}</h3>
                  <p className="item-sku">SKU: {item.sku}</p>
                  <p className="item-quantity">Cantidad: {item.quantity}</p>
                </div>
                <div className="item-price">
                  ${(item.price * item.quantity).toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Dirección de envío */}
        <div className="shipping-section">
          <h2>
            <FiMapPin size={20} />
            Dirección de Envío
          </h2>
          <div className="shipping-address">
            <p className="address-name">{order.shippingAddress.name}</p>
            <p>{order.shippingAddress.street}</p>
            <p>
              {order.shippingAddress.city}, {order.shippingAddress.state} {order.shippingAddress.zipCode}
            </p>
            <p className="address-phone">{order.shippingAddress.phone}</p>
          </div>
        </div>

        {/* Resumen de pago */}
        <div className="summary-section">
          <h2>Resumen de Pago</h2>
          <div className="summary-details">
            <div className="summary-row">
              <span>Subtotal</span>
              <span>${order.subtotal.toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>Envío</span>
              <span>${order.shipping.toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>Impuestos</span>
              <span>${order.tax.toFixed(2)}</span>
            </div>
            <div className="summary-row total">
              <span>Total</span>
              <span>${order.total.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Acciones */}
        <div className="actions-section">
          <button className="action-button primary">
            <FiDownload size={20} />
            Descargar Factura
          </button>
          <button className="action-button secondary">
            Contactar Soporte
          </button>
        </div>
      </div>
    </div>
  );
};

export default OrderDetail;
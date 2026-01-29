// src/pages/Orders/Orders.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './orders.css';
import { FiPackage, FiClock, FiCheck, FiX, FiChevronRight } from 'react-icons/fi';

interface Order {
  id: string;
  orderNumber: string;
  date: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  total: number;
  itemsCount: number;
  items: OrderItem[];
}

interface OrderItem {
  id: string;
  name: string;
  quantity: number;
  price: number;
  image: string;
}

const Orders: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const navigate = useNavigate();

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      // TODO: Reemplazar con API real
      // const response = await ordersAPI.getAll();
      // setOrders(response.data);
      
      // Datos de ejemplo
      const mockOrders: Order[] = [
        {
          id: '1',
          orderNumber: 'ORD-2024-001',
          date: '2024-01-28',
          status: 'delivered',
          total: 1329.98,
          itemsCount: 2,
          items: [
            {
              id: '1',
              name: 'Laptop Gaming',
              quantity: 1,
              price: 1299.99,
              image: 'https://via.placeholder.com/100x100?text=Laptop'
            },
            {
              id: '2',
              name: 'Mouse Inalámbrico',
              quantity: 1,
              price: 29.99,
              image: 'https://via.placeholder.com/100x100?text=Mouse'
            }
          ]
        },
        {
          id: '2',
          orderNumber: 'ORD-2024-002',
          date: '2024-01-26',
          status: 'shipped',
          total: 89.99,
          itemsCount: 1,
          items: [
            {
              id: '3',
              name: 'Teclado Mecánico',
              quantity: 1,
              price: 89.99,
              image: 'https://via.placeholder.com/100x100?text=Teclado'
            }
          ]
        },
        {
          id: '3',
          orderNumber: 'ORD-2024-003',
          date: '2024-01-25',
          status: 'processing',
          total: 299.99,
          itemsCount: 1,
          items: [
            {
              id: '4',
              name: 'Monitor 27"',
              quantity: 1,
              price: 299.99,
              image: 'https://via.placeholder.com/100x100?text=Monitor'
            }
          ]
        }
      ];
      
      setOrders(mockOrders);
    } catch (error) {
      console.error('Error cargando órdenes:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusInfo = (status: string) => {
    const statusMap = {
      pending: { label: 'Pendiente', icon: FiClock, color: '#f59e0b' },
      processing: { label: 'Procesando', icon: FiPackage, color: '#3b82f6' },
      shipped: { label: 'Enviado', icon: FiPackage, color: '#8b5cf6' },
      delivered: { label: 'Entregado', icon: FiCheck, color: '#10b981' },
      cancelled: { label: 'Cancelado', icon: FiX, color: '#ef4444' }
    };
    return statusMap[status as keyof typeof statusMap] || statusMap.pending;
  };

  const filteredOrders = filter === 'all' 
    ? orders 
    : orders.filter(order => order.status === filter);

  const handleOrderClick = (orderId: string) => {
    navigate(`/ordenes/${orderId}`);
  };

  if (loading) {
    return (
      <div className="orders-container">
        <div className="loading">Cargando órdenes...</div>
      </div>
    );
  }

  return (
    <div className="orders-container">
      {/* Header */}
      <div className="orders-header">
        <div className="orders-header-content">
          <h1>Mis Órdenes</h1>
          <p>{orders.length} orden{orders.length !== 1 ? 'es' : ''} en total</p>
        </div>
        <button 
          className="back-button"
          onClick={() => navigate('/tienda')}
        >
          Volver a la Tienda
        </button>
      </div>

      {/* Filtros */}
      <div className="filters-section">
        <div className="filters-scroll">
          <button
            className={`filter-chip ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            Todas
          </button>
          <button
            className={`filter-chip ${filter === 'pending' ? 'active' : ''}`}
            onClick={() => setFilter('pending')}
          >
            Pendientes
          </button>
          <button
            className={`filter-chip ${filter === 'delivered' ? 'active' : ''}`}
            onClick={() => setFilter('delivered')}
          >
            Entregadas
          </button>
          <button
            className={`filter-chip ${filter === 'cancelled' ? 'active' : ''}`}
            onClick={() => setFilter('cancelled')}
          >
            Canceladas
          </button>
        </div>
      </div>

      {/* Lista de órdenes */}
      <div className="orders-list">
        {filteredOrders.length === 0 ? (
          <div className="no-orders">
            <FiPackage size={48} />
            <p>No hay órdenes para mostrar</p>
          </div>
        ) : (
          filteredOrders.map(order => {
            const statusInfo = getStatusInfo(order.status);
            const StatusIcon = statusInfo.icon;

            return (
              <div 
                key={order.id} 
                className="order-card"
                onClick={() => handleOrderClick(order.id)}
              >
                <div className="order-header-row">
                  <div className="order-number">
                    <FiPackage size={20} />
                    <span>{order.orderNumber}</span>
                  </div>
                  <span 
                    className="order-status"
                    style={{ backgroundColor: statusInfo.color }}
                  >
                    <StatusIcon size={14} />
                    {statusInfo.label}
                  </span>
                </div>

                <div className="order-date">
                  {new Date(order.date).toLocaleDateString('es-ES', {
                    day: '2-digit',
                    month: 'long',
                    year: 'numeric'
                  })}
                </div>

                <div className="order-items-preview">
                  {order.items.slice(0, 3).map((item, index) => (
                    <img 
                      key={index}
                      src={item.image} 
                      alt={item.name}
                      className="item-preview-image"
                    />
                  ))}
                  {order.items.length > 3 && (
                    <div className="more-items">
                      +{order.items.length - 3}
                    </div>
                  )}
                </div>

                <div className="order-footer-row">
                  <div className="order-total">
                    <span className="total-label">Total:</span>
                    <span className="total-amount">${order.total.toFixed(2)}</span>
                  </div>
                  <FiChevronRight size={20} className="chevron-icon" />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default Orders;
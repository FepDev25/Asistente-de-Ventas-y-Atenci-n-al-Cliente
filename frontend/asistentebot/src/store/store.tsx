// src/components/Store/Store.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import type { Product } from '../types/types';
import { productsAPI } from '../services/api';
import ProductCard from './productcard';
import './store.css';
import { FiShoppingCart, FiLogOut } from 'react-icons/fi';

const Store: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('Todos');
  const [cartCount, setCartCount] = useState(0);
  
  const { user, logout } = useAuth();

  useEffect(() => {
    loadProducts();
  }, []);

  useEffect(() => {
    filterProducts();
  }, [searchTerm, selectedCategory, products]);

  const loadProducts = async () => {
    try {
      setIsLoading(true);
      // Si no hay conexión con el backend, usa datos de ejemplo
      const data = await productsAPI.getAll().catch(() => getMockProducts());
      setProducts(data);
      setFilteredProducts(data);
    } catch (error) {
      console.error('Error cargando productos:', error);
      setProducts(getMockProducts());
      setFilteredProducts(getMockProducts());
    } finally {
      setIsLoading(false);
    }
  };

  const filterProducts = () => {
    let filtered = products;

    if (selectedCategory !== 'Todos') {
      filtered = filtered.filter(p => p.category === selectedCategory);
    }

    if (searchTerm) {
      filtered = filtered.filter(p => 
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredProducts(filtered);
  };

  const categories = ['Todos', ...Array.from(new Set(products.map(p => p.category)))];

  const handleAddToCart = (product: Product) => {
    setCartCount(prev => prev + 1);
    // Aquí puedes agregar lógica adicional del carrito
    console.log('Producto agregado:', product);
  };

  return (
    <div className="store-container">
      {/* Header */}
      <header className="store-header">
        <div className="header-content">
          <div className="header-left">
            <h1>Mi Tienda</h1>
            <p>Hola, {user?.name}</p>
          </div>
          <div className="header-right">
            <button className="cart-button">
              <FiShoppingCart size={24} />
              {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
            </button>
            <button className="logout-button" onClick={logout}>
              <FiLogOut size={24} />
            </button>
          </div>
        </div>
      </header>

      {/* Barra de búsqueda */}
      <div className="search-section">
        <input
          type="text"
          placeholder="Buscar productos..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      {/* Filtros de categorías */}
      <div className="categories-section">
        <div className="categories-scroll">
          {categories.map((category) => (
            <button
              key={category}
              className={`category-chip ${selectedCategory === category ? 'active' : ''}`}
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Grid de productos */}
      <div className="products-section">
        {isLoading ? (
          <div className="loading">Cargando productos...</div>
        ) : filteredProducts.length === 0 ? (
          <div className="no-products">No se encontraron productos</div>
        ) : (
          <div className="products-grid">
            {filteredProducts.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={handleAddToCart}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Datos de ejemplo para desarrollo
const getMockProducts = (): Product[] => [
  {
    id: '1',
    name: 'Laptop Gaming',
    description: 'Laptop de alto rendimiento para gaming',
    price: 1299.99,
    image: 'https://via.placeholder.com/300x200?text=Laptop',
    category: 'Electrónica',
    stock: 10
  },
  {
    id: '2',
    name: 'Mouse Inalámbrico',
    description: 'Mouse ergonómico con 6 botones',
    price: 29.99,
    image: 'https://via.placeholder.com/300x200?text=Mouse',
    category: 'Accesorios',
    stock: 50
  },
  {
    id: '3',
    name: 'Teclado Mecánico',
    description: 'Teclado mecánico RGB',
    price: 89.99,
    image: 'https://via.placeholder.com/300x200?text=Teclado',
    category: 'Accesorios',
    stock: 30
  },
  {
    id: '4',
    name: 'Monitor 27"',
    description: 'Monitor Full HD 144Hz',
    price: 299.99,
    image: 'https://via.placeholder.com/300x200?text=Monitor',
    category: 'Electrónica',
    stock: 15
  },
  {
    id: '5',
    name: 'Auriculares Gaming',
    description: 'Auriculares con sonido 7.1',
    price: 79.99,
    image: 'https://via.placeholder.com/300x200?text=Auriculares',
    category: 'Accesorios',
    stock: 25
  },
  {
    id: '6',
    name: 'Webcam HD',
    description: 'Webcam 1080p con micrófono',
    price: 49.99,
    image: 'https://via.placeholder.com/300x200?text=Webcam',
    category: 'Accesorios',
    stock: 20
  }
];

export default Store;
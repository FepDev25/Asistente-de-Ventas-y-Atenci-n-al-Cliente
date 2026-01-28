// src/components/Store/ProductCard.tsx
import React from 'react';
import type { Product } from '../types/types';
import { FiShoppingCart } from 'react-icons/fi';

interface ProductCardProps {
  product: Product;
  onAddToCart: (product: Product) => void;
}

const ProductCard: React.FC<ProductCardProps> = ({ product, onAddToCart }) => {
  return (
    <div className="product-card">
      <div className="product-image">
        <img src={product.image} alt={product.name} />
        {product.stock < 10 && product.stock > 0 && (
          <span className="low-stock-badge">¡Quedan {product.stock}!</span>
        )}
        {product.stock === 0 && (
          <span className="out-of-stock-badge">Agotado</span>
        )}
      </div>
      
      <div className="product-info">
        <div className="product-category">{product.category}</div>
        <h3 className="product-name">{product.name}</h3>
        <p className="product-description">{product.description}</p>
        
        <div className="product-footer">
          <div className="product-price">
            <span className="currency">$</span>
            <span className="amount">{product.price.toFixed(2)}</span>
          </div>
          
          <button
            className="add-to-cart-btn"
            onClick={() => onAddToCart(product)}
            disabled={product.stock === 0}
          >
            <FiShoppingCart size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
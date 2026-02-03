// src/types/types.ts

export interface User {
  id: string;
  email: string;
  username: string;
  role: number;
}

export interface LoginResponse {
  access_token: string;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  image: string;
  category: string;
  stock: number;
}

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export interface CartItem extends Product {
  quantity: number;
}

export interface LoginCredentials {
  email?: string;
  username?: string;
  password: string;
}
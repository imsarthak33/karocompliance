// @ts-nocheck
import { create } from 'zustand';

interface AuthState {
  user: any | null;
  caFirm: any | null;
  setUser: (user: any) => void;
  setCaFirm: (caFirm: any) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  caFirm: { id: 'default-ca-id' }, // Placeholder for initial load
  setUser: (user) => set({ user }),
  setCaFirm: (caFirm) => set({ caFirm }),
  logout: () => set({ user: null, caFirm: null })
}));

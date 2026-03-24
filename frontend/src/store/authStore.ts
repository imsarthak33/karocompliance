import { create } from 'zustand';
import type { IUser, ICAFirm, ISession } from '../types';

interface AuthState {
  user: IUser | null;
  session: ISession | null;
  caFirm: ICAFirm | null;
  setUser: (user: IUser) => void;
  setSession: (session: ISession) => void;
  setCaFirm: (caFirm: ICAFirm) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  session: null,
  caFirm: null,
  setUser: (user) => set({ user }),
  setSession: (session) => set({ session }),
  setCaFirm: (caFirm) => set({ caFirm }),
  logout: () => set({ user: null, session: null, caFirm: null }),
}));

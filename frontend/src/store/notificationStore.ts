// @ts-nocheck
import { create } from 'zustand';

interface NotificationState {
  notifications: any[];
  addNotification: (title: string, message: string, type: string) => void;
  removeNotification: (index: number) => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  addNotification: (title, message, type) => set((state) => ({
    notifications: [{ title, message, type }, ...state.notifications]
  })),
  removeNotification: (index) => set((state) => ({
    notifications: state.notifications.filter((_, i) => i !== index)
  }))
}));

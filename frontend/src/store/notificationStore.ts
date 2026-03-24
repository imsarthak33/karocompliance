import { create } from 'zustand';
import type { INotification, NotificationType } from '../types';

interface NotificationState {
  notifications: INotification[];
  addNotification: (title: string, message: string, type: NotificationType) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

let _notificationCounter = 0;

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  addNotification: (title, message, type) =>
    set((state) => ({
      notifications: [
        {
          id: `notif_${++_notificationCounter}`,
          title,
          message,
          type,
          timestamp: Date.now(),
        },
        ...state.notifications,
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearAll: () => set({ notifications: [] }),
}));

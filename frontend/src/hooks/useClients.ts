import React, { useEffect, useState } from 'react';
import { api } from '../api/axiosClient';
import type { IClient } from '../types';

export const useClients = () => {
  const [clients, setClients] = useState<IClient[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const response = await api.get<IClient[]>('/clients/');
        setClients(response.data);
      } catch (error) {
        console.error('Failed to fetch clients:', error);
      } finally {
        setLoading(false);
      }
    };

    void fetchClients();
  }, []);

  return { clients, loading };
};

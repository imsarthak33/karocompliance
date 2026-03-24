import React, { useState } from 'react';
import { useAuthStore } from '../../store/authStore';
import { api } from '../../api/axiosClient';

// Add type declarations for Razorpay window object integration
declare global {
  interface Window {
    Razorpay: any;
  }
}

const loadRazorpayScript = () => {
  return new Promise<boolean>((resolve) => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

export const BillingPage = () => {
  const { caFirm } = useAuthStore();
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);

  const handleUpgrade = async (plan: string) => {
    setLoadingPlan(plan);
    const res = await loadRazorpayScript();

    if (!res) {
      alert('Razorpay SDK failed to load. Are you online?');
      setLoadingPlan(null);
      return;
    }

    try {
      // 1. Create subscription on backend
      const { data } = await api.post<{subscription_id: string}>(`/payments/create-subscription?plan=${plan}`);

      // 2. Initialize Razorpay Checkout
      const options = {
        key: import.meta.env.VITE_RAZORPAY_KEY_ID,
        subscription_id: data.subscription_id,
        name: 'KaroCompliance',
        description: `${plan.toUpperCase()} Plan Subscription`,
        handler: function (response: { razorpay_payment_id: string }) {
          alert(`Payment successful! Payment ID: ${response.razorpay_payment_id}`);
          // The backend webhook will handle the actual database update
          window.location.reload();
        },
        prefill: {
          name: caFirm?.firm_name,
          email: caFirm?.email, // Changed from caFirm?.id based on typical Razorpay prefill
        },
        theme: {
          color: '#2563EB',
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (error) {
      console.error(error);
      alert('Failed to initiate subscription.');
    } finally {
      setLoadingPlan(null);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-2">Billing & Subscriptions</h2>
      <p className="text-gray-600 mb-8">
        Current Plan: <span className="font-semibold text-blue-600 capitalize">{caFirm?.subscription_plan || 'free'}</span>
      </p>

      <div className="grid grid-cols-3 gap-6">
        <PlanCard 
          title="Starter" 
          price="₹2,999/mo" 
          features={['Up to 50 Clients', 'WhatsApp Automation', 'Basic Agent Extraction']}
          onUpgrade={() => void handleUpgrade('starter')}
          isLoading={loadingPlan === 'starter'}
        />
        <PlanCard 
          title="Professional" 
          price="₹4,999/mo" 
          features={['Up to 200 Clients', 'WhatsApp Automation', 'Advanced Reconciliation', 'Anomaly Detection']}
          onUpgrade={() => void handleUpgrade('professional')}
          isLoading={loadingPlan === 'professional'}
          isPopular
        />
        <PlanCard 
          title="Enterprise" 
          price="₹9,999/mo" 
          features={['Unlimited Clients', 'Custom Branding', 'Dedicated Account Manager', 'Voice Note Extraction']}
          onUpgrade={() => void handleUpgrade('enterprise')}
          isLoading={loadingPlan === 'enterprise'}
        />
      </div>
    </div>
  );
};

interface PlanCardProps {
  title: string;
  price: string;
  features: string[];
  onUpgrade: () => void;
  isLoading: boolean;
  isPopular?: boolean;
}

const PlanCard: React.FC<PlanCardProps> = ({ title, price, features, onUpgrade, isLoading, isPopular }) => (
  <div className={`relative p-6 rounded-lg border ${isPopular ? 'border-blue-500 shadow-md' : 'border-gray-200'}`}>
    {isPopular && <span className="absolute top-0 right-0 bg-blue-500 text-white text-xs px-2 py-1 rounded-bl-lg rounded-tr-lg">Most Popular</span>}
    <h3 className="text-lg font-bold">{title}</h3>
    <p className="text-3xl font-extrabold my-4">{price}</p>
    <ul className="space-y-2 mb-6 text-sm text-gray-600">
      {features.map((f, i) => <li key={i}>✓ {f}</li>)}
    </ul>
    <button 
      onClick={onUpgrade} 
      disabled={isLoading}
      className={`w-full py-2 rounded-md font-medium text-white ${isPopular ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-800 hover:bg-gray-900'} disabled:opacity-50`}
    >
      {isLoading ? 'Processing...' : `Choose ${title}`}
    </button>
  </div>
);

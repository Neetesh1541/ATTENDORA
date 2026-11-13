import React, { useState } from 'react';
import { CreditCard, CheckCircle, Plus } from 'lucide-react';
import { SubscriptionPlanModel } from '../../../types';
import Card from '../../../components/ui/Card';
import Badge from '../../../components/ui/Badge';
import Button from '../../../components/ui/Button';

export const AdminPlansPage: React.FC = () => {
  const [plans, setPlans] = useState<SubscriptionPlanModel[]>([
    {
      id: 'p1',
      name: 'Starter Plan',
      plan_type: 'starter',
      max_people: 50,
      max_cameras: 2,
      max_admins: 2,
      price_monthly: 49,
      price_yearly: 470,
      features: ['Up to 50 members', '2 camera feeds', 'CSV reports'],
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'p2',
      name: 'Professional Plan',
      plan_type: 'professional',
      max_people: 300,
      max_cameras: 8,
      max_admins: 10,
      price_monthly: 129,
      price_yearly: 1240,
      features: ['Up to 300 members', '8 camera feeds', 'Advanced analytics', 'Shift management'],
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'p3',
      name: 'Enterprise Plan',
      plan_type: 'enterprise',
      max_people: 5000,
      max_cameras: 50,
      max_admins: 50,
      price_monthly: 499,
      price_yearly: 4790,
      features: ['Unlimited members', '50 camera feeds', 'Dedicated SLA', 'Full audit logging'],
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    },
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          SaaS Subscription Plans
        </h1>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Super Admin pricing models, capacity limits, and feature toggles.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <Card key={plan.id}>
            <Card.Content className="p-6">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-base text-slate-900 dark:text-white">
                  {plan.name}
                </h3>
                <Badge color="green">Active</Badge>
              </div>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
                  ${plan.price_monthly}
                </span>
                <span className="text-xs text-slate-400">/month</span>
              </div>

              <div className="mt-4 space-y-2 border-y border-slate-100 dark:border-slate-800 py-3 text-xs text-slate-600 dark:text-slate-400">
                <p>Max Members: <strong className="text-slate-900 dark:text-white">{plan.max_people}</strong></p>
                <p>Max Cameras: <strong className="text-slate-900 dark:text-white">{plan.max_cameras}</strong></p>
                <p>Max Admins: <strong className="text-slate-900 dark:text-white">{plan.max_admins}</strong></p>
              </div>
            </Card.Content>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default AdminPlansPage;

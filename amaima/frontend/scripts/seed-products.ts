import { getUncachableStripeClient } from '../src/lib/stripeClient';

async function seedProducts() {
  const stripe = await getUncachableStripeClient();

  const plans = [
    {
      name: 'AMAIMA Community',
      description: 'Free tier for non-commercial use. 1,000 queries/month with access to all 14 NVIDIA NIM models.',
      metadata: { tier: 'community', queries_per_month: '1000' },
      price: null,
    },
    {
      name: 'AMAIMA Production',
      description: 'Production tier for commercial use. 10,000 queries/month with priority routing and all domain services.',
      metadata: { tier: 'production', queries_per_month: '10000' },
      price: 4900,
    },
    {
      name: 'AMAIMA Enterprise',
      description: 'Enterprise tier with unlimited queries, custom SLA, dedicated support, and advanced analytics.',
      metadata: { tier: 'enterprise', queries_per_month: 'unlimited' },
      price: 49900,
    },
  ];

  for (const plan of plans) {
    const existing = await stripe.products.search({ query: `name:'${plan.name}'` });
    if (existing.data.length > 0) {
      console.log(`${plan.name} already exists (${existing.data[0].id})`);
      continue;
    }

    const product = await stripe.products.create({
      name: plan.name,
      description: plan.description,
      metadata: plan.metadata,
    });
    console.log(`Created product: ${product.id} - ${plan.name}`);

    if (plan.price) {
      const price = await stripe.prices.create({
        product: product.id,
        unit_amount: plan.price,
        currency: 'usd',
        recurring: { interval: 'month' },
      });
      console.log(`  Created price: ${price.id} - $${plan.price / 100}/month`);
    }
  }

  console.log('Seed complete!');
}

seedProducts().catch(console.error);

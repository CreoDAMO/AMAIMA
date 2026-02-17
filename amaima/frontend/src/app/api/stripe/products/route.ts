import { NextResponse } from 'next/server';
import { getUncachableStripeClient } from '@/lib/stripeClient';
import { initStripe } from '@/lib/stripeInit';
import { Pool } from 'pg';

let pool: Pool | null = null;
function getPool() {
  if (!pool) {
    pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 2 });
  }
  return pool;
}

export async function GET() {
  try {
    await initStripe();
    const db = getPool();

    const result = await db.query(`
      SELECT 
        p.id as product_id,
        p.name as product_name,
        p.description as product_description,
        p.metadata as product_metadata,
        pr.id as price_id,
        pr.unit_amount,
        pr.currency,
        pr.recurring
      FROM stripe.products p
      LEFT JOIN stripe.prices pr ON pr.product = p.id AND pr.active = true
      WHERE p.active = true
      ORDER BY pr.unit_amount ASC NULLS FIRST
    `);

    if (result.rows.length > 0) {
      const productsMap = new Map();
      for (const row of result.rows) {
        if (!productsMap.has(row.product_id)) {
          productsMap.set(row.product_id, {
            id: row.product_id,
            name: row.product_name,
            description: row.product_description,
            metadata: row.product_metadata,
            prices: [],
          });
        }
        if (row.price_id) {
          productsMap.get(row.product_id).prices.push({
            id: row.price_id,
            unit_amount: row.unit_amount,
            currency: row.currency,
            recurring: row.recurring,
          });
        }
      }
      return NextResponse.json({ data: Array.from(productsMap.values()) });
    }

    const stripe = await getUncachableStripeClient();
    const products = await stripe.products.list({ active: true, limit: 10 });
    const prices = await stripe.prices.list({ active: true, limit: 50 });

    const data = products.data.map((p) => ({
      id: p.id,
      name: p.name,
      description: p.description,
      metadata: p.metadata || {},
      prices: prices.data
        .filter((pr) => pr.product === p.id)
        .map((pr) => ({
          id: pr.id,
          unit_amount: pr.unit_amount,
          currency: pr.currency,
          recurring: pr.recurring,
        })),
    }));

    return NextResponse.json({ data });
  } catch (error: any) {
    console.error('Products error:', error.message);
    return NextResponse.json({ data: [] });
  }
}

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils/cn';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary text-primary-foreground',
        secondary: 'border-transparent bg-secondary text-secondary-foreground',
        destructive: 'border-transparent bg-destructive text-destructive-foreground',
        outline: 'text-foreground',
        glass: 'border-white/20 bg-white/10 text-white backdrop-blur-xl',
        cyan: 'border-cyan-500/30 bg-cyan-500/20 text-cyan-300',
        purple: 'border-purple-500/30 bg-purple-500/20 text-purple-300',
        pink: 'border-pink-500/30 bg-pink-500/20 text-pink-300',
        emerald: 'border-emerald-500/30 bg-emerald-500/20 text-emerald-300',
        amber: 'border-amber-500/30 bg-amber-500/20 text-amber-300',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };

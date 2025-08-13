import React from 'react';
import { render, screen } from '@testing-library/react';
import { Badge } from './badge';

describe('Badge Component', () => {
  it('renders with default variant', () => {
    render(<Badge>Test Badge</Badge>);
    const badge = screen.getByText('Test Badge');
    
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-primary');
  });

  it('renders with different variants', () => {
    const { rerender } = render(<Badge variant="secondary">Secondary Badge</Badge>);
    let badge = screen.getByText('Secondary Badge');
    
    expect(badge).toHaveClass('bg-secondary');

    rerender(<Badge variant="destructive">Destructive Badge</Badge>);
    badge = screen.getByText('Destructive Badge');
    
    expect(badge).toHaveClass('bg-destructive');
  });

  it('renders with different sizes', () => {
    const { rerender } = render(<Badge size="sm">Small Badge</Badge>);
    let badge = screen.getByText('Small Badge');
    
    expect(badge).toHaveClass('text-xs px-2 py-0.5');

    rerender(<Badge size="lg">Large Badge</Badge>);
    badge = screen.getByText('Large Badge');
    
    expect(badge).toHaveClass('text-sm px-3 py-1');
  });

  it('applies custom className', () => {
    render(<Badge className="custom-class">Custom Badge</Badge>);
    const badge = screen.getByText('Custom Badge');
    
    expect(badge).toHaveClass('custom-class');
  });
});

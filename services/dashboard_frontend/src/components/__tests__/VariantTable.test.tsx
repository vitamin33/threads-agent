/**
 * Tests for VariantTable component.
 * Following TDD - write failing tests first.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { VariantTable } from '../VariantTable';

describe('VariantTable', () => {
  test('renders variant table with headers', () => {
    const mockVariants = [];
    
    render(<VariantTable variants={mockVariants} />);
    
    // Check for table headers
    expect(screen.getByText('Variant ID')).toBeInTheDocument();
    expect(screen.getByText('Engagement Rate')).toBeInTheDocument();
    expect(screen.getByText('Impressions')).toBeInTheDocument();
    expect(screen.getByText('Early Kill Status')).toBeInTheDocument();
    expect(screen.getByText('Pattern Fatigue')).toBeInTheDocument();
  });

  test('displays variant data correctly', () => {
    const mockVariants = [
      {
        variant_id: 'test_variant_1',
        engagement_rate: 0.15,
        impressions: 100,
        successes: 15,
        early_kill_status: 'monitoring',
        pattern_fatigue_warning: false,
        freshness_score: 0.8
      }
    ];
    
    render(<VariantTable variants={mockVariants} />);
    
    // Check for variant data
    expect(screen.getByText('test_variant_1')).toBeInTheDocument();
    expect(screen.getByText('15.0%')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('monitoring')).toBeInTheDocument();
  });

  test('shows early kill warning for variants being monitored', () => {
    const mockVariants = [
      {
        variant_id: 'warning_variant',
        engagement_rate: 0.05, // Low engagement
        impressions: 50,
        successes: 2,
        early_kill_status: 'monitoring',
        pattern_fatigue_warning: false,
        freshness_score: 0.8
      }
    ];
    
    render(<VariantTable variants={mockVariants} />);
    
    // Should show warning styling for low engagement
    const row = screen.getByText('warning_variant').closest('tr');
    expect(row).toHaveClass('warning');
  });

  test('shows pattern fatigue warning styling', () => {
    const mockVariants = [
      {
        variant_id: 'fatigued_variant',
        engagement_rate: 0.12,
        impressions: 80,
        successes: 10,
        early_kill_status: 'not_monitored',
        pattern_fatigue_warning: true,
        freshness_score: 0.1
      }
    ];
    
    render(<VariantTable variants={mockVariants} />);
    
    // Should show fatigue warning
    const row = screen.getByText('fatigued_variant').closest('tr');
    expect(row).toHaveClass('pattern-fatigue');
  });
});
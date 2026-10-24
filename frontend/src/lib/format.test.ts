import { describe, expect, it } from 'vitest';
import { formatCurrency, formatDate, percent, severityTone, titleCase } from './format';

describe('format helpers', () => {
  it('formats INR values', () => {
    expect(formatCurrency(1250000)).toContain('12,50,000');
  });

  it('formats dates safely', () => {
    expect(formatDate('2026-10-23')).toBe('23 Oct 2026');
    expect(formatDate('')).toBe('—');
  });

  it('converts labels to title case', () => {
    expect(titleCase('structural_frame')).toBe('Structural Frame');
  });

  it('computes percentages and risk tones', () => {
    expect(percent(25, 100)).toBe(25);
    expect(percent(1, 0)).toBe(0);
    expect(severityTone('critical')).toBe('danger');
    expect(severityTone('minor')).toBe('success');
  });
});

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { SeverityBadge, StatusBadge, FindingStatusBadge } from '../components/common/Badge';

describe('SeverityBadge', () => {
  it('renders high severity correctly', () => {
    render(<SeverityBadge severity="high" />);
    expect(screen.getByText('high')).toBeInTheDocument();
  });

  it('renders medium severity correctly', () => {
    render(<SeverityBadge severity="medium" />);
    expect(screen.getByText('medium')).toBeInTheDocument();
  });

  it('renders informational as fallback', () => {
    render(<SeverityBadge severity="unknown" />);
    expect(screen.getByText('unknown')).toBeInTheDocument();
  });
});

describe('StatusBadge', () => {
  it('renders completed status', () => {
    render(<StatusBadge status="completed" />);
    expect(screen.getByText('completed')).toBeInTheDocument();
  });

  it('renders running status with pulse indicator', () => {
    render(<StatusBadge status="running" />);
    const elem = screen.getByText('running');
    expect(elem).toBeInTheDocument();
  });
});

describe('FindingStatusBadge', () => {
  it('renders Open status by default', () => {
    render(<FindingStatusBadge status="open" />);
    expect(screen.getByText('Open')).toBeInTheDocument();
  });

  it('renders Remediated status', () => {
    render(<FindingStatusBadge status="remediated" />);
    expect(screen.getByText('Remediated')).toBeInTheDocument();
  });

  it('renders Acknowledged and Accepted Risk statuses', () => {
    render(<FindingStatusBadge status="acknowledged" />);
    expect(screen.getByText('Acknowledged')).toBeInTheDocument();
  });
});

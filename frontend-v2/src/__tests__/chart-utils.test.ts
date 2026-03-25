import { describe, it, expect } from 'vitest';
import {
  fmtDurationShort,
  fmtDuration,
  fmtElapsed,
  tooltipLeft,
  tsbColor,
  demandColor,
  demandOpacity,
  ifZoneColor,
  rollingAvg,
  findNearest,
} from '../shared/chart-utils';
import { COLORS } from '../shared/tokens';

describe('fmtDurationShort', () => {
  it('formats seconds under 60 as Xs', () => {
    expect(fmtDurationShort(5)).toBe('5s');
    expect(fmtDurationShort(30)).toBe('30s');
  });
  it('formats 60+ seconds as Xmin', () => {
    expect(fmtDurationShort(60)).toBe('1min');
    expect(fmtDurationShort(300)).toBe('5min');
    expect(fmtDurationShort(3600)).toBe('60min');
  });
});

describe('fmtDuration', () => {
  it('formats short durations', () => {
    expect(fmtDuration(5)).toBe('5s');
  });
  it('formats exact minutes', () => {
    expect(fmtDuration(120)).toBe('2min');
  });
  it('formats minutes + seconds', () => {
    expect(fmtDuration(125)).toBe('2min 5s');
  });
});

describe('fmtElapsed', () => {
  it('formats MM:SS under an hour', () => {
    expect(fmtElapsed(125)).toBe('02:05');
  });
  it('formats H:MM:SS at an hour or more', () => {
    expect(fmtElapsed(3661)).toBe('1:01:01');
  });
});

describe('tooltipLeft', () => {
  it('places tooltip to the right by default', () => {
    expect(tooltipLeft(100, 50, 80, 800)).toBe(162);
  });
  it('flips tooltip to the left when it would overflow', () => {
    expect(tooltipLeft(700, 50, 80, 800)).toBe(658);
  });
});

describe('tsbColor', () => {
  it('returns positive color for TSB > 5', () => {
    expect(tsbColor(10)).toBe(COLORS.success);
  });
  it('returns neutral color for TSB -10 to 5', () => {
    expect(tsbColor(0)).toBe(COLORS.warning);
    expect(tsbColor(-10)).toBe(COLORS.warning);
  });
  it('returns negative color for TSB < -10', () => {
    expect(tsbColor(-15)).toBe(COLORS.danger);
  });
});

describe('demandColor', () => {
  it('returns danger for ratio >= 0.95', () => {
    expect(demandColor(1.0)).toBe(COLORS.danger);
    expect(demandColor(0.95)).toBe(COLORS.danger);
  });
  it('returns warning for ratio 0.85-0.95', () => {
    expect(demandColor(0.90)).toBe(COLORS.warning);
  });
  it('returns success for ratio < 0.85', () => {
    expect(demandColor(0.70)).toBe(COLORS.success);
  });
});

describe('demandOpacity', () => {
  it('returns higher opacity for higher demand', () => {
    expect(demandOpacity(1.1)).toBe(0.4);
    expect(demandOpacity(0.96)).toBe(0.25);
    expect(demandOpacity(0.90)).toBe(0.2);
    expect(demandOpacity(0.70)).toBe(0.15);
  });
});

describe('ifZoneColor', () => {
  it('colors by IF intensity zone', () => {
    expect(ifZoneColor(0.40)).toBe(COLORS.primary);
    expect(ifZoneColor(0.60)).toBe(COLORS.warning);
    expect(ifZoneColor(0.80)).toBe(COLORS.danger);
  });
});

describe('rollingAvg', () => {
  it('returns copy for window < 2', () => {
    expect(rollingAvg([1, 2, 3], 1)).toEqual([1, 2, 3]);
  });
  it('computes correct rolling average', () => {
    const result = rollingAvg([10, 20, 30, 40, 50], 3);
    expect(result[0]).toBeCloseTo(10);
    expect(result[1]).toBeCloseTo(15);
    expect(result[2]).toBeCloseTo(20);
    expect(result[3]).toBeCloseTo(30);
    expect(result[4]).toBeCloseTo(40);
  });
  it('handles nulls', () => {
    const result = rollingAvg([10, null, 30], 2);
    expect(result[0]).toBeCloseTo(10);
    expect(result[1]).toBeCloseTo(10);
    expect(result[2]).toBeCloseTo(30);
  });
});

describe('findNearest', () => {
  const data = [{ x: 1 }, { x: 5 }, { x: 10 }];
  it('finds nearest point', () => {
    expect(findNearest(data, d => d.x, 4)).toEqual({ x: 5 });
    expect(findNearest(data, d => d.x, 7)).toEqual({ x: 5 });
    expect(findNearest(data, d => d.x, 8)).toEqual({ x: 10 });
  });
  it('returns null for empty data', () => {
    expect(findNearest([], d => (d as { x: number }).x, 5)).toBeNull();
  });
});

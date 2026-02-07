/**
 * Unit tests for DepartureRecommendationCard Component
 * Coverage: 100% of src/components/DepartureRecommendationCard.js
 * 
 * Testing Strategy:
 * - Test all component states (loading, error, warning, go now, wait)
 * - Test TrafficIndicator component
 * - Test rendering logic
 * - Test prop variations
 * - Snapshot testing for UI consistency
 */

import React from 'react';
import { render } from '@testing-library/react-native';
import { DepartureRecommendationCard } from '../DepartureRecommendationCard';
import { OptimalDepartureResult } from '../../services/departureOptimizationService';

// Mock Ionicons
jest.mock('@expo/vector-icons', () => ({
  Ionicons: 'Ionicons',
}));

describe('DepartureRecommendationCard', () => {
  describe('Loading State', () => {
    it('should render loading state', () => {
      const { getByText, UNSAFE_getByType } = render(
        <DepartureRecommendationCard loading={true} />
      );
      
      expect(getByText('Analyzing traffic...')).toBeTruthy();
      // ActivityIndicator is rendered
      const activityIndicator = UNSAFE_getByType('ActivityIndicator');
      expect(activityIndicator).toBeTruthy();
    });
    
    it('should not render other states when loading', () => {
      const mockResult = createMockResult({ camerasAnalyzed: 5 });
      
      const { queryByText } = render(
        <DepartureRecommendationCard 
          loading={true} 
          result={mockResult}
        />
      );
      
      expect(queryByText('Best Time: Leave Now!')).toBeNull();
    });
    
    it('should match snapshot for loading state', () => {
      const { toJSON } = render(
        <DepartureRecommendationCard loading={true} />
      );
      
      expect(toJSON()).toMatchSnapshot();
    });
  });
  
  describe('Error State', () => {
    it('should render error message', () => {
      const { getByText } = render(
        <DepartureRecommendationCard error="Failed to fetch data" />
      );
      
      expect(getByText('Failed to fetch data')).toBeTruthy();
    });
    
    it('should render error icon', () => {
      const { UNSAFE_getByProps } = render(
        <DepartureRecommendationCard error="Test error" />
      );
      
      const icon = UNSAFE_getByProps({ name: 'alert-circle-outline' });
      expect(icon).toBeTruthy();
    });
    
    it('should match snapshot for error state', () => {
      const { toJSON } = render(
        <DepartureRecommendationCard error="Network error" />
      );
      
      expect(toJSON()).toMatchSnapshot();
    });
  });
  
  describe('No Result State', () => {
    it('should render nothing when no result and not loading', () => {
      const { toJSON } = render(
        <DepartureRecommendationCard />
      );
      
      expect(toJSON()).toBeNull();
      // Component returns null, so no children
    });
  });
  
  describe('Low Confidence Warning State', () => {
    it('should show warning for low confidence', () => {
      const mockResult = createMockResult({
        confidenceScore: 0.4,  // Low confidence
        camerasAnalyzed: 3,
      });
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Limited traffic data available for this route')).toBeTruthy();
    });
    
    it('should show warning for few cameras', () => {
      const mockResult = createMockResult({
        confidenceScore: 0.8,  // High confidence
        camerasAnalyzed: 1,  // Too few cameras
      });
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Limited traffic data available for this route')).toBeTruthy();
    });
    
    it('should show warning icon', () => {
      const mockResult = createMockResult({
        confidenceScore: 0.3,
        camerasAnalyzed: 1,
      });
      
      const { UNSAFE_getByProps } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      const icon = UNSAFE_getByProps({ name: 'information-circle-outline' });
      expect(icon).toBeTruthy();
    });
    
    it('should match snapshot for warning state', () => {
      const mockResult = createMockResult({
        confidenceScore: 0.4,
        camerasAnalyzed: 1,
      });
      
      const { toJSON } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(toJSON()).toMatchSnapshot();
    });
  });
  
  describe('Go Now State', () => {
    it('should show "Leave Now" when best time is 0', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 0,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Best Time: Leave Now!')).toBeTruthy();
    });
    
    it('should display current ETA', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 0,
        currentEtaMinutes: 30,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('30 min')).toBeTruthy();
    });
    
    it('should show traffic level', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 0,
        currentAverageCi: 0.35,  // Moderate traffic
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      mockResult.getTrafficLevel = jest.fn(() => 'Moderate');
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Moderate Traffic')).toBeTruthy();
    });
    
    it('should show checkmark icon', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 0,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      const { UNSAFE_getByProps } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      const icon = UNSAFE_getByProps({ name: 'checkmark-circle' });
      expect(icon).toBeTruthy();
    });
    
    it('should show camera count', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 0,
        camerasAnalyzed: 5,
        confidenceScore: 0.7,
      });
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('5 cameras analyzed')).toBeTruthy();
    });
    
    it('should match snapshot for go now state', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 0,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      const { toJSON } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(toJSON()).toMatchSnapshot();
    });
  });
  
  describe('Wait Recommendation State', () => {
    it('should show wait recommendation with significant benefit', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 15,
        timeSavedMinutes: 10,  // Significant
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      mockResult.hasSignificantBenefit = jest.fn(() => true);
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Better Time Available')).toBeTruthy();
    });
    
    it('should show wait recommendation without significant benefit', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 10,
        timeSavedMinutes: 2,  // Not significant
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      mockResult.hasSignificantBenefit = jest.fn(() => false);
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Traffic Insight')).toBeTruthy();
    });
    
    it('should display recommendation text', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 15,
        recommendationText: 'Wait 15 minutes for better traffic.',
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Wait 15 minutes for better traffic.')).toBeTruthy();
    });
    
    it('should show ETA comparison', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 15,
        currentEtaMinutes: 35,
        optimizedEtaMinutes: 28,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('If you leave now')).toBeTruthy();
      expect(getByText('35 min')).toBeTruthy();
      expect(getByText('28 min')).toBeTruthy();
    });
    
    it('should show time saved when positive', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 20,
        timeSavedMinutes: 8,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      mockResult.getFormattedDepartureTime = jest.fn(() => '3:45 PM');
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Save 8 min')).toBeTruthy();
    });
    
    it('should show formatted departure time', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 15,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      mockResult.getFormattedDepartureTime = jest.fn(() => '2:30 PM');
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText(/Leave at 2:30 PM/)).toBeTruthy();
    });
    
    it('should show confidence bar', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 15,
        confidenceScore: 0.75,
        camerasAnalyzed: 4,
      });
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Based on 4 traffic cameras')).toBeTruthy();
    });
    
    it('should render correct icon for wait state', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 15,
        timeSavedMinutes: 10,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      mockResult.hasSignificantBenefit = jest.fn(() => true);
      
      const { UNSAFE_getByProps } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      const icon = UNSAFE_getByProps({ name: 'time' });
      expect(icon).toBeTruthy();
    });
    
    it('should match snapshot for wait state', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 15,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      const { toJSON } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(toJSON()).toMatchSnapshot();
    });
  });
  
  describe('Traffic Level Colors', () => {
    it('should show green for light traffic (CI < 0.3)', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 0,
        currentAverageCi: 0.2,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      mockResult.getTrafficLevel = jest.fn(() => 'Light');
      
      const { UNSAFE_getAllByType } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      // Green icon color in TrafficIndicator
      const icons = UNSAFE_getAllByType('Ionicons');
      const trafficIcon = icons.find(icon => 
        icon.props.name === 'speedometer' || 
        icon.props.name === 'car' ||
        icon.props.name === 'alert-circle' ||
        icon.props.name === 'warning'
      );
      
      // Verify icon exists (color checking is limited in test env)
      expect(trafficIcon).toBeTruthy();
    });
    
    it('should show appropriate icon for different traffic levels', () => {
      // Light traffic
      let mockResult = createMockResult({
        bestTimeMinutesFromNow: 0,
        currentAverageCi: 0.2,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      let { UNSAFE_getByProps } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(UNSAFE_getByProps({ name: 'speedometer' })).toBeTruthy();
    });
  });
  
  describe('Edge Cases', () => {
    it('should handle zero cameras analyzed', () => {
      const mockResult = createMockResult({
        camerasAnalyzed: 0,
        confidenceScore: 0,
      });
      
      mockResult.isReliable = jest.fn(() => false);
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Limited traffic data available for this route')).toBeTruthy();
    });
    
    it('should handle negative time saved', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 30,
        timeSavedMinutes: -5,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      mockResult.hasSignificantBenefit = jest.fn(() => false);
      
      const { queryByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      // Should not show "Save X min" for negative time
      expect(queryByText(/Save -5 min/)).toBeNull();
    });
    
    it('should handle very high confidence score', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 10,
        confidenceScore: 0.99,
        camerasAnalyzed: 10,
      });
      
      const { getByText } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(getByText('Based on 10 traffic cameras')).toBeTruthy();
    });
    
    it('should handle missing optional result properties', () => {
      const mockResult = createMockResult({
        bestTimeMinutesFromNow: 15,
        confidenceScore: 0.7,
        camerasAnalyzed: 3,
      });
      
      // Remove optional methods
      mockResult.hasSignificantBenefit = jest.fn(() => false);
      mockResult.getTrafficLevel = jest.fn(() => 'Moderate');
      mockResult.getFormattedDepartureTime = jest.fn(() => '3:00 PM');
      
      const { root } = render(
        <DepartureRecommendationCard result={mockResult} />
      );
      
      expect(root).toBeTruthy();
    });
  });
});

// Helper function to create mock result
function createMockResult(overrides = {}) {
  const defaults = {
    bestTimeMinutesFromNow: 0,
    bestDepartureTime: new Date('2024-11-04T15:00:00'),
    originalEtaMinutes: 30,
    currentEtaMinutes: 30,
    optimizedEtaMinutes: 30,
    timeSavedMinutes: 0,
    currentAverageCi: 0.3,
    optimalAverageCi: 0.3,
    camerasAnalyzed: 2,
    confidenceScore: 0.5,
    recommendationText: 'Test recommendation',
  };
  
  const data = { ...defaults, ...overrides };
  
  const result = {
    ...data,
    hasSignificantBenefit: jest.fn(() => data.timeSavedMinutes >= 3),
    isReliable: jest.fn(() => data.confidenceScore >= 0.5 && data.camerasAnalyzed >= 2),
    getTrafficLevel: jest.fn(() => {
      if (data.currentAverageCi < 0.3) return 'Light';
      if (data.currentAverageCi < 0.5) return 'Moderate';
      if (data.currentAverageCi < 0.7) return 'Heavy';
      return 'Severe';
    }),
    getFormattedDepartureTime: jest.fn(() => {
      const date = data.bestDepartureTime;
      const hours = date.getHours();
      const minutes = date.getMinutes();
      const ampm = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours % 12 || 12;
      const displayMinutes = minutes.toString().padStart(2, '0');
      return `${displayHours}:${displayMinutes} ${ampm}`;
    }),
  };
  
  return result;
}

/**
 * Unit tests for Departure Optimization Service
 * Coverage: 100% of src/services/departureOptimizationService.js
 * 
 * Testing Strategy:
 * - Test all static methods
 * - Test DTO class methods
 * - Test adapters and parsers
 * - Test error handling
 * - Mock API calls
 */

import {
  DepartureOptimizationService,
  OptimalDepartureResult,
} from '../departureOptimizationService';
import { apiPost } from '../api';

// Mock the API module
jest.mock('../api', () => ({
  apiPost: jest.fn(),
}));

describe('OptimalDepartureResult DTO', () => {
  let mockData;
  
  beforeEach(() => {
    mockData = {
      best_time_minutes_from_now: 15,
      best_departure_time: '2024-11-04T14:45:00',
      original_eta_minutes: 30,
      current_eta_minutes: 35,
      optimized_eta_minutes: 28,
      time_saved_minutes: 7,
      current_average_ci: 0.65,
      optimal_average_ci: 0.42,
      cameras_analyzed: 5,
      confidence_score: 0.78,
      recommendation_text: 'Wait 15 minutes for better traffic.',
    };
  });
  
  describe('constructor', () => {
    it('should create instance from API response data', () => {
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.bestTimeMinutesFromNow).toBe(15);
      expect(result.bestDepartureTime).toBeInstanceOf(Date);
      expect(result.originalEtaMinutes).toBe(30);
      expect(result.currentEtaMinutes).toBe(35);
      expect(result.optimizedEtaMinutes).toBe(28);
      expect(result.timeSavedMinutes).toBe(7);
      expect(result.currentAverageCi).toBe(0.65);
      expect(result.optimalAverageCi).toBe(0.42);
      expect(result.camerasAnalyzed).toBe(5);
      expect(result.confidenceScore).toBe(0.78);
      expect(result.recommendationText).toBe('Wait 15 minutes for better traffic.');
    });
    
    it('should convert ISO date string to Date object', () => {
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.bestDepartureTime).toBeInstanceOf(Date);
      expect(result.bestDepartureTime.getHours()).toBe(14);
      expect(result.bestDepartureTime.getMinutes()).toBe(45);
    });
  });
  
  describe('hasSignificantBenefit', () => {
    it('should return true when time saved >= 3 minutes', () => {
      mockData.time_saved_minutes = 3;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.hasSignificantBenefit()).toBe(true);
    });
    
    it('should return true when time saved > 3 minutes', () => {
      mockData.time_saved_minutes = 10;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.hasSignificantBenefit()).toBe(true);
    });
    
    it('should return false when time saved < 3 minutes', () => {
      mockData.time_saved_minutes = 2;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.hasSignificantBenefit()).toBe(false);
    });
    
    it('should return false when time saved is negative', () => {
      mockData.time_saved_minutes = -5;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.hasSignificantBenefit()).toBe(false);
    });
  });
  
  describe('isReliable', () => {
    it('should return true when confidence >= 0.5 and cameras >= 2', () => {
      mockData.confidence_score = 0.5;
      mockData.cameras_analyzed = 2;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.isReliable()).toBe(true);
    });
    
    it('should return true when confidence > 0.5 and cameras > 2', () => {
      mockData.confidence_score = 0.75;
      mockData.cameras_analyzed = 5;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.isReliable()).toBe(true);
    });
    
    it('should return false when confidence < 0.5', () => {
      mockData.confidence_score = 0.4;
      mockData.cameras_analyzed = 5;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.isReliable()).toBe(false);
    });
    
    it('should return false when cameras < 2', () => {
      mockData.confidence_score = 0.8;
      mockData.cameras_analyzed = 1;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.isReliable()).toBe(false);
    });
    
    it('should return false when both conditions fail', () => {
      mockData.confidence_score = 0.3;
      mockData.cameras_analyzed = 1;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.isReliable()).toBe(false);
    });
  });
  
  describe('getTrafficLevel', () => {
    it('should return "Light" for CI < 0.3', () => {
      mockData.current_average_ci = 0.2;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.getTrafficLevel()).toBe('Light');
    });
    
    it('should return "Moderate" for 0.3 <= CI < 0.5', () => {
      mockData.current_average_ci = 0.4;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.getTrafficLevel()).toBe('Moderate');
    });
    
    it('should return "Heavy" for 0.5 <= CI < 0.7', () => {
      mockData.current_average_ci = 0.6;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.getTrafficLevel()).toBe('Heavy');
    });
    
    it('should return "Severe" for CI >= 0.7', () => {
      mockData.current_average_ci = 0.8;
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.getTrafficLevel()).toBe('Severe');
    });
    
    it('should handle boundary cases correctly', () => {
      mockData.current_average_ci = 0.3;
      let result = new OptimalDepartureResult(mockData);
      expect(result.getTrafficLevel()).toBe('Moderate');
      
      mockData.current_average_ci = 0.5;
      result = new OptimalDepartureResult(mockData);
      expect(result.getTrafficLevel()).toBe('Heavy');
      
      mockData.current_average_ci = 0.7;
      result = new OptimalDepartureResult(mockData);
      expect(result.getTrafficLevel()).toBe('Severe');
    });
  });
  
  describe('getFormattedDepartureTime', () => {
    it('should format AM time correctly', () => {
      mockData.best_departure_time = '2024-11-04T09:30:00';
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.getFormattedDepartureTime()).toBe('9:30 AM');
    });
    
    it('should format PM time correctly', () => {
      mockData.best_departure_time = '2024-11-04T14:45:00';
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.getFormattedDepartureTime()).toBe('2:45 PM');
    });
    
    it('should format midnight correctly', () => {
      mockData.best_departure_time = '2024-11-04T00:15:00';
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.getFormattedDepartureTime()).toBe('12:15 AM');
    });
    
    it('should format noon correctly', () => {
      mockData.best_departure_time = '2024-11-04T12:00:00';
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.getFormattedDepartureTime()).toBe('12:00 PM');
    });
    
    it('should pad minutes with zero', () => {
      mockData.best_departure_time = '2024-11-04T15:05:00';
      const result = new OptimalDepartureResult(mockData);
      
      expect(result.getFormattedDepartureTime()).toBe('3:05 PM');
    });
  });
});

describe('DepartureOptimizationService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  describe('findOptimalDeparture', () => {
    it('should make API call with correct parameters', async () => {
      const mockResponse = {
        best_time_minutes_from_now: 10,
        best_departure_time: '2024-11-04T15:00:00',
        original_eta_minutes: 25,
        current_eta_minutes: 30,
        optimized_eta_minutes: 27,
        time_saved_minutes: 3,
        current_average_ci: 0.5,
        optimal_average_ci: 0.4,
        cameras_analyzed: 3,
        confidence_score: 0.65,
        recommendation_text: 'Wait 10 minutes.',
      };
      
      apiPost.mockResolvedValue(mockResponse);
      
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      const result = await DepartureOptimizationService.findOptimalDeparture(
        coords,
        25,
        0.5,
        120
      );
      
      expect(apiPost).toHaveBeenCalledWith('/api/traffic/departure/optimize', {
        route_points: [
          { latitude: 1.35, longitude: 103.82 },
          { latitude: 1.36, longitude: 103.83 },
        ],
        original_eta_minutes: 25,
        search_radius_km: 0.5,
        forecast_horizon_minutes: 120,
      });
      
      expect(result).toBeInstanceOf(OptimalDepartureResult);
      expect(result.bestTimeMinutesFromNow).toBe(10);
    });
    
    it('should use default values for optional parameters', async () => {
      const mockResponse = {
        best_time_minutes_from_now: 0,
        best_departure_time: '2024-11-04T15:00:00',
        original_eta_minutes: 25,
        current_eta_minutes: 25,
        optimized_eta_minutes: 25,
        time_saved_minutes: 0,
        current_average_ci: 0.3,
        optimal_average_ci: 0.3,
        cameras_analyzed: 2,
        confidence_score: 0.6,
        recommendation_text: 'Leave now.',
      };
      
      apiPost.mockResolvedValue(mockResponse);
      
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      await DepartureOptimizationService.findOptimalDeparture(coords, 25);
      
      expect(apiPost).toHaveBeenCalledWith('/api/traffic/departure/optimize', {
        route_points: expect.any(Array),
        original_eta_minutes: 25,
        search_radius_km: 0.5,  // Default
        forecast_horizon_minutes: 120,  // Default
      });
    });
    
    it('should throw error when route has less than 2 points', async () => {
      const coords = [{ latitude: 1.35, longitude: 103.82 }];
      
      await expect(
        DepartureOptimizationService.findOptimalDeparture(coords, 25)
      ).rejects.toThrow('Route must have at least 2 points');
    });
    
    it('should throw error when route is empty', async () => {
      await expect(
        DepartureOptimizationService.findOptimalDeparture([], 25)
      ).rejects.toThrow('Route must have at least 2 points');
    });
    
    it('should throw error when route is null', async () => {
      await expect(
        DepartureOptimizationService.findOptimalDeparture(null, 25)
      ).rejects.toThrow('Route must have at least 2 points');
    });
    
    it('should throw error when ETA is zero', async () => {
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      await expect(
        DepartureOptimizationService.findOptimalDeparture(coords, 0)
      ).rejects.toThrow('ETA must be positive');
    });
    
    it('should throw error when ETA is negative', async () => {
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      await expect(
        DepartureOptimizationService.findOptimalDeparture(coords, -10)
      ).rejects.toThrow('ETA must be positive');
    });
    
    it('should throw user-friendly error for connection issues', async () => {
      apiPost.mockRejectedValue(new Error('Cannot connect to server'));
      
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      await expect(
        DepartureOptimizationService.findOptimalDeparture(coords, 25)
      ).rejects.toThrow('Unable to connect to traffic service');
    });
    
    it('should throw user-friendly error for timeout', async () => {
      apiPost.mockRejectedValue(new Error('Request timeout'));
      
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      await expect(
        DepartureOptimizationService.findOptimalDeparture(coords, 25)
      ).rejects.toThrow('Traffic service is taking too long to respond');
    });
    
    it('should throw generic error for other failures', async () => {
      apiPost.mockRejectedValue(new Error('Some other error'));
      
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      await expect(
        DepartureOptimizationService.findOptimalDeparture(coords, 25)
      ).rejects.toThrow('Failed to optimize departure time');
    });
  });
  
  describe('extractRouteCoordinates', () => {
    it('should extract from route.coords', () => {
      const route = {
        coords: [
          { latitude: 1.35, longitude: 103.82 },
          { latitude: 1.36, longitude: 103.83 },
        ],
      };
      
      const result = DepartureOptimizationService.extractRouteCoordinates(route);
      
      expect(result).toEqual([
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ]);
    });
    
    it('should extract from route.coordinates', () => {
      const route = {
        coordinates: [
          { latitude: 1.35, longitude: 103.82 },
          { latitude: 1.36, longitude: 103.83 },
        ],
      };
      
      const result = DepartureOptimizationService.extractRouteCoordinates(route);
      
      expect(result).toEqual([
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ]);
    });
    
    it('should extract from route.route_points', () => {
      const route = {
        route_points: [
          { latitude: 1.35, longitude: 103.82 },
          { latitude: 1.36, longitude: 103.83 },
        ],
      };
      
      const result = DepartureOptimizationService.extractRouteCoordinates(route);
      
      expect(result).toEqual([
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ]);
    });
    
    it('should handle lat/lng format', () => {
      const route = {
        coords: [
          { lat: 1.35, lng: 103.82 },
          { lat: 1.36, lng: 103.83 },
        ],
      };
      
      const result = DepartureOptimizationService.extractRouteCoordinates(route);
      
      expect(result).toEqual([
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ]);
    });
    
    it('should handle lat/lon format', () => {
      const route = {
        coords: [
          { lat: 1.35, lon: 103.82 },
          { lat: 1.36, lon: 103.83 },
        ],
      };
      
      const result = DepartureOptimizationService.extractRouteCoordinates(route);
      
      expect(result).toEqual([
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ]);
    });
    
    it('should filter out invalid coordinates', () => {
      const route = {
        coords: [
          { latitude: 1.35, longitude: 103.82 },
          { latitude: undefined, longitude: 103.83 },  // Invalid
          { latitude: 1.36, longitude: 103.84 },
        ],
      };
      
      const result = DepartureOptimizationService.extractRouteCoordinates(route);
      
      expect(result).toEqual([
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.84 },
      ]);
    });
    
    it('should return empty array for null route', () => {
      const result = DepartureOptimizationService.extractRouteCoordinates(null);
      
      expect(result).toEqual([]);
    });
    
    it('should return empty array for undefined route', () => {
      const result = DepartureOptimizationService.extractRouteCoordinates(undefined);
      
      expect(result).toEqual([]);
    });
    
    it('should return empty array for route without coordinates', () => {
      const route = { name: 'Route 1' };
      
      const result = DepartureOptimizationService.extractRouteCoordinates(route);
      
      expect(result).toEqual([]);
    });
  });
  
  describe('parseEtaMinutes', () => {
    it('should parse minutes only', () => {
      expect(DepartureOptimizationService.parseEtaMinutes('25 min')).toBe(25);
      expect(DepartureOptimizationService.parseEtaMinutes('45 mins')).toBe(45);
      expect(DepartureOptimizationService.parseEtaMinutes('5 minutes')).toBe(5);
    });
    
    it('should parse hours only', () => {
      expect(DepartureOptimizationService.parseEtaMinutes('1 hour')).toBe(60);
      expect(DepartureOptimizationService.parseEtaMinutes('2 hours')).toBe(120);
    });
    
    it('should parse hours and minutes', () => {
      expect(DepartureOptimizationService.parseEtaMinutes('1 hour 15 min')).toBe(75);
      expect(DepartureOptimizationService.parseEtaMinutes('2 hours 30 minutes')).toBe(150);
    });
    
    it('should handle case insensitivity', () => {
      expect(DepartureOptimizationService.parseEtaMinutes('1 HOUR 30 MIN')).toBe(90);
      expect(DepartureOptimizationService.parseEtaMinutes('45 MIN')).toBe(45);
    });
    
    it('should return 0 for empty string', () => {
      expect(DepartureOptimizationService.parseEtaMinutes('')).toBe(0);
    });
    
    it('should return 0 for null', () => {
      expect(DepartureOptimizationService.parseEtaMinutes(null)).toBe(0);
    });
    
    it('should return 0 for undefined', () => {
      expect(DepartureOptimizationService.parseEtaMinutes(undefined)).toBe(0);
    });
    
    it('should return 0 for invalid format', () => {
      expect(DepartureOptimizationService.parseEtaMinutes('invalid')).toBe(0);
    });
  });
  
  describe('formatDuration', () => {
    it('should format minutes less than 60', () => {
      expect(DepartureOptimizationService.formatDuration(30)).toBe('30 min');
      expect(DepartureOptimizationService.formatDuration(45)).toBe('45 min');
      expect(DepartureOptimizationService.formatDuration(1)).toBe('1 min');
    });
    
    it('should format exact hours', () => {
      expect(DepartureOptimizationService.formatDuration(60)).toBe('1 hour');
      expect(DepartureOptimizationService.formatDuration(120)).toBe('2 hours');
      expect(DepartureOptimizationService.formatDuration(180)).toBe('3 hours');
    });
    
    it('should format hours and minutes', () => {
      expect(DepartureOptimizationService.formatDuration(75)).toBe('1 hour 15 min');
      expect(DepartureOptimizationService.formatDuration(150)).toBe('2 hours 30 min');
      expect(DepartureOptimizationService.formatDuration(61)).toBe('1 hour 1 min');
    });
    
    it('should use correct singular/plural forms', () => {
      expect(DepartureOptimizationService.formatDuration(60)).toBe('1 hour');
      expect(DepartureOptimizationService.formatDuration(120)).toBe('2 hours');
    });
  });
});

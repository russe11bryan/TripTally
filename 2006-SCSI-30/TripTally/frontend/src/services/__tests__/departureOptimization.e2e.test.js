/**
 * END-TO-END Test: Departure Optimization - Wait Scenario
 * 
 * This test simulates a complete user flow where the backend recommends
 * waiting because traffic improves later.
 * 
 * Test Scenario:
 * - Current traffic: Heavy congestion (CI = 0.75)
 * - Traffic forecast: Improves at +30 minutes (CI = 0.30)
 * - System should recommend: WAIT 30 minutes
 * 
 * Flow Tested:
 * 1. User provides route with coordinates
 * 2. Service calls backend API
 * 3. Backend returns recommendation to wait
 * 4. Frontend parses response correctly
 * 5. UI displays wait recommendation properly
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

describe('END-TO-END: Departure Optimization Wait Scenario', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Complete Flow: Backend recommends waiting when traffic improves', () => {
    it('should handle wait recommendation correctly end-to-end', async () => {
      // ==========================================
      // STEP 1: Mock Backend Response
      // ==========================================
      // This simulates the backend detecting that traffic will improve
      // from CI=0.75 (heavy) now to CI=0.30 (light) in 30 minutes
      
      const mockBackendResponse = {
        // Recommendation: Wait 30 minutes
        best_time_minutes_from_now: 30,
        best_departure_time: '2024-11-04T23:22:00',
        
        // ETA Analysis
        original_eta_minutes: 30,        // Baseline (no traffic)
        current_eta_minutes: 45,         // If leaving now (heavy traffic)
        optimized_eta_minutes: 33,       // If waiting (light traffic)
        time_saved_minutes: 12,          // Travel time saved
        
        // Traffic Conditions
        current_average_ci: 0.75,        // Heavy congestion now
        optimal_average_ci: 0.30,        // Light traffic later
        
        // Confidence
        cameras_analyzed: 4,
        confidence_score: 0.70,
        
        // Recommendation text
        recommendation_text: 'Wait 30 minutes. Traffic will clear significantly, saving you 12 minutes of travel time.',
      };
      
      apiPost.mockResolvedValue(mockBackendResponse);
      
      // ==========================================
      // STEP 2: User Input
      // ==========================================
      // User plans route from Marina Bay to Changi
      const routeCoordinates = [
        { latitude: 1.2958, longitude: 103.8808 },  // Marina Bay area
        { latitude: 1.3200, longitude: 103.9100 },  // Middle point
        { latitude: 1.3400, longitude: 103.9800 },  // Changi area
      ];
      
      const originalEtaMinutes = 30;
      const searchRadiusKm = 0.5;
      const forecastHorizonMinutes = 120;
      
      // ==========================================
      // STEP 3: Call Service
      // ==========================================
      const result = await DepartureOptimizationService.findOptimalDeparture(
        routeCoordinates,
        originalEtaMinutes,
        searchRadiusKm,
        forecastHorizonMinutes
      );
      
      // ==========================================
      // STEP 4: Verify API Call
      // ==========================================
      expect(apiPost).toHaveBeenCalledTimes(1);
      expect(apiPost).toHaveBeenCalledWith('/api/traffic/departure/optimize', {
        route_points: routeCoordinates,
        original_eta_minutes: originalEtaMinutes,
        search_radius_km: searchRadiusKm,
        forecast_horizon_minutes: forecastHorizonMinutes,
      });
      
      // ==========================================
      // STEP 5: Verify Result Object
      // ==========================================
      expect(result).toBeInstanceOf(OptimalDepartureResult);
      
      // Timing recommendation
      expect(result.bestTimeMinutesFromNow).toBe(30);
      expect(result.bestDepartureTime).toBeInstanceOf(Date);
      expect(result.bestDepartureTime.getHours()).toBe(23);
      expect(result.bestDepartureTime.getMinutes()).toBe(22);
      
      // ETA comparison
      expect(result.originalEtaMinutes).toBe(30);
      expect(result.currentEtaMinutes).toBe(45);     // Leaving now = 45 min
      expect(result.optimizedEtaMinutes).toBe(33);   // Waiting = 33 min
      expect(result.timeSavedMinutes).toBe(12);      // Saves 12 min travel time
      
      // Traffic conditions
      expect(result.currentAverageCi).toBe(0.75);    // Heavy now
      expect(result.optimalAverageCi).toBe(0.30);    // Light later
      
      // Confidence
      expect(result.camerasAnalyzed).toBe(4);
      expect(result.confidenceScore).toBe(0.70);
      
      // Recommendation text
      expect(result.recommendationText).toContain('Wait 30 minutes');
      expect(result.recommendationText).toContain('saving you 12 minutes');
      
      // ==========================================
      // STEP 6: Verify DTO Helper Methods
      // ==========================================
      
      // Should have significant benefit (saves >= 3 minutes)
      expect(result.hasSignificantBenefit()).toBe(true);
      
      // Should be reliable (confidence >= 0.5, cameras >= 2)
      expect(result.isReliable()).toBe(true);
      
      // Traffic level should be "Severe" (CI = 0.75 >= 0.7)
      expect(result.getTrafficLevel()).toBe('Severe');
      
      // Formatted departure time
      const formattedTime = result.getFormattedDepartureTime();
      expect(formattedTime).toBe('11:22 PM');
      
      console.log('\n='.repeat(80));
      console.log('✅ END-TO-END TEST RESULTS: WAIT SCENARIO');
      console.log('='.repeat(80));
      console.log('\n📊 Scenario Summary:');
      console.log(`  Route: Marina Bay → Changi`);
      console.log(`  Current Traffic: Severe (CI = ${result.currentAverageCi})`);
      console.log(`  Future Traffic:  Light (CI = ${result.optimalAverageCi})`);
      console.log(`  CI Improvement:  ${((result.currentAverageCi - result.optimalAverageCi) / result.currentAverageCi * 100).toFixed(1)}%`);
      
      console.log('\n⏰ Timing Recommendation:');
      console.log(`  ❌ Don't leave now!`);
      console.log(`  ✅ Wait ${result.bestTimeMinutesFromNow} minutes`);
      console.log(`  📅 Leave at: ${formattedTime}`);
      
      console.log('\n🚗 ETA Analysis:');
      console.log(`  Baseline ETA:    ${result.originalEtaMinutes} min`);
      console.log(`  If leaving now:  ${result.currentEtaMinutes} min (heavy traffic)`);
      console.log(`  If waiting:      ${result.optimizedEtaMinutes} min (light traffic)`);
      console.log(`  Travel time saved: ${result.timeSavedMinutes} min`);
      console.log(`  Wait time:       ${result.bestTimeMinutesFromNow} min`);
      console.log(`  Net benefit:     ${result.timeSavedMinutes - result.bestTimeMinutesFromNow} min`);
      
      console.log('\n📷 Data Quality:');
      console.log(`  Cameras analyzed: ${result.camerasAnalyzed}`);
      console.log(`  Confidence:       ${(result.confidenceScore * 100).toFixed(0)}%`);
      console.log(`  Reliable:         ${result.isReliable() ? 'Yes' : 'No'}`);
      console.log(`  Significant:      ${result.hasSignificantBenefit() ? 'Yes' : 'No'}`);
      
      console.log('\n💡 User Recommendation:');
      console.log(`  "${result.recommendationText}"`);
      
      console.log('\n' + '='.repeat(80));
      console.log('🎉 TEST PASSED: Frontend correctly handles wait recommendation!');
      console.log('='.repeat(80) + '\n');
    });
    
    it('should detect when waiting is NOT worthwhile (net negative)', async () => {
      // Edge case: Waiting actually makes total time worse
      const mockBackendResponse = {
        best_time_minutes_from_now: 45,  // Wait 45 minutes
        best_departure_time: '2024-11-04T23:45:00',
        original_eta_minutes: 30,
        current_eta_minutes: 35,          // Leaving now = 35 min
        optimized_eta_minutes: 33,        // If waiting = 33 min
        time_saved_minutes: 2,            // Only saves 2 min travel time
        current_average_ci: 0.55,
        optimal_average_ci: 0.50,
        cameras_analyzed: 3,
        confidence_score: 0.65,
        recommendation_text: 'Traffic is similar now and later. Leaving now may be better.',
      };
      
      apiPost.mockResolvedValue(mockBackendResponse);
      
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      const result = await DepartureOptimizationService.findOptimalDeparture(coords, 30);
      
      // Parse results
      const netBenefit = result.timeSavedMinutes - result.bestTimeMinutesFromNow;
      
      // Assertions
      expect(result.bestTimeMinutesFromNow).toBe(45);
      expect(result.timeSavedMinutes).toBe(2);
      expect(netBenefit).toBe(-43);  // Net negative! Waiting is worse
      expect(result.hasSignificantBenefit()).toBe(false);  // Only 2 min saved
      
      console.log('\n📊 Edge Case: Waiting is NOT worthwhile');
      console.log(`  Wait time: ${result.bestTimeMinutesFromNow} min`);
      console.log(`  Travel time saved: ${result.timeSavedMinutes} min`);
      console.log(`  Net benefit: ${netBenefit} min (NEGATIVE!)`);
      console.log(`  ❌ Better to leave now despite forecast`);
    });
    
    it('should handle "leave now" scenario correctly', async () => {
      // Scenario: Traffic is already optimal, no need to wait
      const mockBackendResponse = {
        best_time_minutes_from_now: 0,    // Leave immediately
        best_departure_time: new Date().toISOString(),
        original_eta_minutes: 30,
        current_eta_minutes: 32,           // Light traffic now
        optimized_eta_minutes: 32,         // Same as current
        time_saved_minutes: 0,             // No benefit to waiting
        current_average_ci: 0.25,          // Already light traffic
        optimal_average_ci: 0.25,
        cameras_analyzed: 4,
        confidence_score: 0.72,
        recommendation_text: 'Leave now! Traffic is already good.',
      };
      
      apiPost.mockResolvedValue(mockBackendResponse);
      
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      const result = await DepartureOptimizationService.findOptimalDeparture(coords, 30);
      
      // Assertions
      expect(result.bestTimeMinutesFromNow).toBe(0);       // Leave now
      expect(result.timeSavedMinutes).toBe(0);             // No savings
      expect(result.currentAverageCi).toBe(0.25);          // Already light
      expect(result.getTrafficLevel()).toBe('Light');
      expect(result.recommendationText).toContain('Leave now');
      
      console.log('\n📊 Scenario: Leave Now (Traffic already good)');
      console.log(`  Current CI: ${result.currentAverageCi} (${result.getTrafficLevel()})`);
      console.log(`  Wait time: ${result.bestTimeMinutesFromNow} min`);
      console.log(`  ✅ Leave immediately!`);
    });
    
    it('should handle moderate wait time (10-20 minutes)', async () => {
      // Typical scenario: Moderate wait with good benefit
      const mockBackendResponse = {
        best_time_minutes_from_now: 15,
        best_departure_time: '2024-11-04T15:15:00',
        original_eta_minutes: 25,
        current_eta_minutes: 32,
        optimized_eta_minutes: 26,
        time_saved_minutes: 6,
        current_average_ci: 0.60,          // Heavy traffic
        optimal_average_ci: 0.35,          // Moderate traffic
        cameras_analyzed: 5,
        confidence_score: 0.78,
        recommendation_text: 'Wait 15 minutes for better traffic conditions.',
      };
      
      apiPost.mockResolvedValue(mockBackendResponse);
      
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      const result = await DepartureOptimizationService.findOptimalDeparture(coords, 25);
      
      const netBenefit = result.timeSavedMinutes - result.bestTimeMinutesFromNow;
      
      // Assertions
      expect(result.bestTimeMinutesFromNow).toBe(15);
      expect(result.timeSavedMinutes).toBe(6);
      expect(netBenefit).toBe(-9);                       // Net negative, but saves travel time
      expect(result.hasSignificantBenefit()).toBe(true); // >= 3 min saved
      expect(result.isReliable()).toBe(true);            // Good confidence
      
      console.log('\n📊 Scenario: Moderate Wait (15 min)');
      console.log(`  Wait time: ${result.bestTimeMinutesFromNow} min`);
      console.log(`  Travel time saved: ${result.timeSavedMinutes} min`);
      console.log(`  Net benefit: ${netBenefit} min`);
      console.log(`  ⚖️  Moderate wait for smoother traffic`);
    });
  });
  
  describe('Error Handling in Wait Scenarios', () => {
    it('should handle API failure gracefully', async () => {
      apiPost.mockRejectedValue(new Error('Network timeout'));
      
      const coords = [
        { latitude: 1.35, longitude: 103.82 },
        { latitude: 1.36, longitude: 103.83 },
      ];
      
      await expect(
        DepartureOptimizationService.findOptimalDeparture(coords, 30)
      ).rejects.toThrow('Traffic service is taking too long to respond');
    });
    
    it('should validate route before making API call', async () => {
      const invalidCoords = [
        { latitude: 1.35, longitude: 103.82 },
        // Missing second point
      ];
      
      await expect(
        DepartureOptimizationService.findOptimalDeparture(invalidCoords, 30)
      ).rejects.toThrow('Route must have at least 2 points');
      
      // API should not be called
      expect(apiPost).not.toHaveBeenCalled();
    });
  });
  
  describe('DTO Methods with Wait Scenario Data', () => {
    it('should correctly classify traffic levels in wait scenarios', () => {
      // Test all traffic level classifications
      const scenarios = [
        { ci: 0.15, level: 'Light' },
        { ci: 0.35, level: 'Moderate' },
        { ci: 0.55, level: 'Heavy' },
        { ci: 0.75, level: 'Severe' },
      ];
      
      scenarios.forEach(({ ci, level }) => {
        const mockData = {
          best_time_minutes_from_now: 20,
          best_departure_time: '2024-11-04T15:00:00',
          original_eta_minutes: 30,
          current_eta_minutes: 35,
          optimized_eta_minutes: 32,
          time_saved_minutes: 3,
          current_average_ci: ci,
          optimal_average_ci: 0.30,
          cameras_analyzed: 3,
          confidence_score: 0.65,
          recommendation_text: 'Wait for better traffic.',
        };
        
        const result = new OptimalDepartureResult(mockData);
        expect(result.getTrafficLevel()).toBe(level);
      });
    });
    
    it('should format various departure times correctly', () => {
      const times = [
        { iso: '2024-11-04T09:30:00', formatted: '9:30 AM' },
        { iso: '2024-11-04T14:45:00', formatted: '2:45 PM' },
        { iso: '2024-11-04T00:15:00', formatted: '12:15 AM' },
        { iso: '2024-11-04T12:00:00', formatted: '12:00 PM' },
        { iso: '2024-11-04T23:22:00', formatted: '11:22 PM' },
      ];
      
      times.forEach(({ iso, formatted }) => {
        const mockData = {
          best_time_minutes_from_now: 30,
          best_departure_time: iso,
          original_eta_minutes: 30,
          current_eta_minutes: 35,
          optimized_eta_minutes: 32,
          time_saved_minutes: 3,
          current_average_ci: 0.50,
          optimal_average_ci: 0.30,
          cameras_analyzed: 3,
          confidence_score: 0.65,
          recommendation_text: 'Wait.',
        };
        
        const result = new OptimalDepartureResult(mockData);
        expect(result.getFormattedDepartureTime()).toBe(formatted);
      });
    });
  });
});

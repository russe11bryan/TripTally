/**
 * Departure Time Optimization Service
 * 
 * Architecture: Service Layer Pattern
 * Handles all API calls related to departure time optimization
 * 
 * Design Pattern: Facade Pattern - Simple interface to complex backend
 */

import { apiPost } from './api';

/**
 * DTO: Optimal Departure Response
 */
export class OptimalDepartureResult {
  constructor(data) {
    this.bestTimeMinutesFromNow = data.best_time_minutes_from_now;
    this.bestDepartureTime = new Date(data.best_departure_time);
    this.originalEtaMinutes = data.original_eta_minutes;
    this.currentEtaMinutes = data.current_eta_minutes;
    this.optimizedEtaMinutes = data.optimized_eta_minutes;
    this.timeSavedMinutes = data.time_saved_minutes;
    this.currentAverageCi = data.current_average_ci;
    this.optimalAverageCi = data.optimal_average_ci;
    this.camerasAnalyzed = data.cameras_analyzed;
    this.confidenceScore = data.confidence_score;
    this.recommendationText = data.recommendation_text;
  }

  /**
   * Check if optimization provides significant benefit
   */
  hasSignificantBenefit() {
    return true;
  }

  /**
   * Check if recommendation is reliable
   */
  isReliable() {
    return this.confidenceScore >= 0.5 && this.camerasAnalyzed >= 2;
  }

  /**
   * Get traffic level description
   */
  getTrafficLevel() {
    if (this.currentAverageCi < 0.3) return 'Light';
    if (this.currentAverageCi < 0.5) return 'Moderate';
    if (this.currentAverageCi < 0.7) return 'Heavy';
    return 'Severe';
  }

  /**
   * Get formatted departure time
   */
  getFormattedDepartureTime() {
    const hours = this.bestDepartureTime.getHours();
    const minutes = this.bestDepartureTime.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    const displayMinutes = minutes.toString().padStart(2, '0');
    return `${displayHours}:${displayMinutes} ${ampm}`;
  }
}

/**
 * Departure Time Optimization Service
 * 
 * Responsibilities:
 * - Convert route data to API format
 * - Call backend API
 * - Parse and validate response
 * - Handle errors gracefully
 */
export class DepartureOptimizationService {
  /**
   * Find optimal departure time for a route
   * 
   * @param {Array} routeCoordinates - Array of {latitude, longitude} objects
   * @param {number} originalEtaMinutes - Original ETA in minutes
   * @param {number} searchRadiusKm - Search radius for cameras (default: 0.5)
   * @param {number} forecastHorizonMinutes - Forecast horizon (default: 120)
   * @returns {Promise<OptimalDepartureResult>}
   */
  static async findOptimalDeparture(
    routeCoordinates,
    originalEtaMinutes,
    searchRadiusKm = 0.5,
    forecastHorizonMinutes = 120
  ) {
    try {
      // Validate inputs
      if (!routeCoordinates || routeCoordinates.length < 2) {
        throw new Error('Route must have at least 2 points');
      }

      if (originalEtaMinutes <= 0) {
        throw new Error('ETA must be positive');
      }

      // Convert route coordinates to API format
      const routePoints = routeCoordinates.map(coord => ({
        latitude: coord.latitude,
        longitude: coord.longitude,
      }));

      // Call backend API
      const response = await apiPost('/api/traffic/departure/optimize', {
        route_points: routePoints,
        original_eta_minutes: originalEtaMinutes,
        search_radius_km: searchRadiusKm,
        forecast_horizon_minutes: forecastHorizonMinutes,
      });

      // Parse response into domain object
      return new OptimalDepartureResult(response);
    } catch (error) {
      console.error('Error finding optimal departure:', error);
      
      // Re-throw with user-friendly message
      if (error.message.includes('Cannot connect to server')) {
        throw new Error('Unable to connect to traffic service. Please check your connection.');
      }
      
      if (error.message.includes('timeout')) {
        throw new Error('Traffic service is taking too long to respond. Please try again.');
      }
      
      throw new Error(`Failed to optimize departure time: ${error.message}`);
    }
  }

  /**
   * Extract route coordinates from various route formats
   * 
   * Design Pattern: Adapter Pattern - adapts different route formats
   * 
   * @param {Object} route - Route object with coords or coordinates
   * @returns {Array} Array of {latitude, longitude} objects
   */
  static extractRouteCoordinates(route) {
    if (!route) {
      return [];
    }

    // Handle different route formats
    const coords = route.coords || route.coordinates || route.route_points || [];
    
    // Ensure all coords have latitude/longitude
    return coords.map(coord => ({
      latitude: coord.latitude || coord.lat,
      longitude: coord.longitude || coord.lng || coord.lon,
    })).filter(coord => 
      coord.latitude !== undefined && 
      coord.longitude !== undefined
    );
  }

  /**
   * Parse ETA from duration text
   * 
   * Examples: "25 min", "1 hour 15 min", "45 mins"
   * 
   * @param {string} durationText - Duration text
   * @returns {number} Duration in minutes
   */
  static parseEtaMinutes(durationText) {
    if (!durationText) return 0;

    const text = durationText.toLowerCase();
    let totalMinutes = 0;

    // Extract hours
    const hourMatch = text.match(/(\d+)\s*hour/);
    if (hourMatch) {
      totalMinutes += parseInt(hourMatch[1]) * 60;
    }

    // Extract minutes
    const minMatch = text.match(/(\d+)\s*min/);
    if (minMatch) {
      totalMinutes += parseInt(minMatch[1]);
    }

    return totalMinutes || 0;
  }

  /**
   * Format minutes to human-readable duration
   * 
   * @param {number} minutes - Duration in minutes
   * @returns {string} Formatted duration
   */
  static formatDuration(minutes) {
    if (minutes < 60) {
      return `${minutes} min`;
    }
    
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (mins === 0) {
      return `${hours} ${hours === 1 ? 'hour' : 'hours'}`;
    }
    
    return `${hours} ${hours === 1 ? 'hour' : 'hours'} ${mins} min`;
  }
}

export default DepartureOptimizationService;

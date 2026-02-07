/**
 * Departure Recommendation Card Component
 * 
 * Architecture: Presentational Component (View in MVC)
 * Displays optimal departure time recommendation
 * 
 * Design Pattern: Observer Pattern - responds to data changes
 */

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

/**
 * Traffic level indicator
 */
const TrafficIndicator = ({ level, ci }) => {
  const getColor = () => {
    if (ci < 0.3) return '#10B981'; // Green - Light
    if (ci < 0.5) return '#F59E0B'; // Orange - Moderate
    if (ci < 0.7) return '#EF4444'; // Red - Heavy
    return '#7F1D1D'; // Dark red - Severe
  };

  const getIcon = () => {
    if (ci < 0.3) return 'speedometer';
    if (ci < 0.5) return 'car';
    if (ci < 0.7) return 'alert-circle';
    return 'warning';
  };

  return (
    <View style={styles.trafficIndicator}>
      <Ionicons name={getIcon()} size={16} color={getColor()} />
      <Text style={[styles.trafficText, { color: getColor() }]}>
        {level} Traffic
      </Text>
    </View>
  );
};

/**
 * Main Departure Recommendation Card
 */
export const DepartureRecommendationCard = ({
  result,
  loading = false,
  error = null,
}) => {
  // Loading state
  if (loading) {
    return (
      <View style={styles.card}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color="#3B82F6" />
          <Text style={styles.loadingText}>Analyzing traffic...</Text>
        </View>
      </View>
    );
  }

  // Error state
  if (error) {
    return (
      <View style={[styles.card, styles.errorCard]}>
        <Ionicons name="alert-circle-outline" size={20} color="#EF4444" />
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  // No result
  if (!result) {
    return null;
  }

  // Low confidence warning
  // Don't use
  // if (!result.isReliable()) {
  //   return (
  //     <View style={[styles.card, styles.warningCard]}>
  //       <Ionicons name="information-circle-outline" size={20} color="#F59E0B" />
  //       <Text style={styles.warningText}>
  //         Limited traffic data available for this route
  //       </Text>
  //     </View>
  //   );
  // }

  // Optimal time is now
  if (result.bestTimeMinutesFromNow === 0) {
    return (
      <View style={[styles.card, styles.goNowCard]}>
        <View style={styles.header}>
          <Ionicons name="checkmark-circle" size={24} color="#10B981" />
          <Text style={styles.goNowTitle}>Best Time: Leave Now!</Text>
        </View>
        <TrafficIndicator 
          level={result.getTrafficLevel()} 
          ci={result.currentAverageCi} 
        />
        <View style={styles.etaRow}>
          <Text style={styles.etaLabel}>Estimated Arrival:</Text>
          <Text style={styles.etaValue}>
            {result.currentEtaMinutes} min
          </Text>
        </View>
        <Text style={styles.confidence}>
          {result.camerasAnalyzed} cameras analyzed
        </Text>
      </View>
    );
  }

  // Wait recommendation
  const shouldWait = result.hasSignificantBenefit();
  
  return (
    <View style={[styles.card, shouldWait && styles.waitCard]}>
      <View style={styles.header}>
        <Ionicons 
          name={shouldWait ? "time" : "information-circle"} 
          size={24} 
          color={shouldWait ? "#3B82F6" : "#6B7280"} 
        />
        <Text style={styles.title}>
          {shouldWait ? 'Better Time Available' : 'Traffic Insight'}
        </Text>
      </View>

      {/* Recommendation text */}
      <Text style={styles.recommendationText}>
        {result.recommendationText}
      </Text>

      {/* Time comparison */}
      <View style={styles.comparisonContainer}>
        {/* Current (if leaving now) */}
        <View style={styles.comparisonItem}>
          <Text style={styles.comparisonLabel}>If you leave now</Text>
          <Text style={styles.comparisonTime}>
            {result.currentEtaMinutes} min
          </Text>
          <TrafficIndicator 
            level={result.getTrafficLevel()} 
            ci={result.currentAverageCi} 
          />
        </View>

        {/* Arrow */}
        <Ionicons name="arrow-forward" size={20} color="#9CA3AF" />

        {/* Optimal */}
        <View style={styles.comparisonItem}>
          <Text style={styles.comparisonLabel}>
            Leave at {result.getFormattedDepartureTime()}
          </Text>
          <Text style={[styles.comparisonTime, styles.optimizedTime]}>
            {result.optimizedEtaMinutes} min
          </Text>
          <Text style={styles.timeSaved}>
            {result.timeSavedMinutes > 0 && `Save ${result.timeSavedMinutes} min`}
          </Text>
        </View>
      </View>

      {/* Confidence indicator */}
      <View style={styles.footer}>
        <View style={styles.confidenceBar}>
          <View 
            style={[
              styles.confidenceFill, 
              { width: `${result.confidenceScore * 100}%` }
            ]} 
          />
        </View>
        <Text style={styles.confidenceText}>
          Based on {result.camerasAnalyzed} traffic cameras
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  
  // Loading state
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: '#6B7280',
  },
  
  // Error state
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#FEF2F2',
    borderColor: '#FCA5A5',
  },
  errorText: {
    fontSize: 14,
    color: '#EF4444',
    flex: 1,
  },
  
  // Warning state
  warningCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#FFFBEB',
    borderColor: '#FCD34D',
  },
  warningText: {
    fontSize: 14,
    color: '#D97706',
    flex: 1,
  },
  
  // Go now card
  goNowCard: {
    backgroundColor: '#F0FDF4',
    borderColor: '#86EFAC',
  },
  goNowTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#065F46',
  },
  
  // Wait card
  waitCard: {
    backgroundColor: '#EFF6FF',
    borderColor: '#93C5FD',
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
  },
  
  // Recommendation text
  recommendationText: {
    fontSize: 15,
    color: '#374151',
    marginBottom: 16,
    lineHeight: 22,
  },
  
  // Traffic indicator
  trafficIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  trafficText: {
    fontSize: 13,
    fontWeight: '600',
  },
  
  // ETA row
  etaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  etaLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  etaValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  
  // Comparison container
  comparisonContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    marginTop: 16,
    padding: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
  },
  comparisonItem: {
    flex: 1,
    alignItems: 'center',
  },
  comparisonLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
    textAlign: 'center',
  },
  comparisonTime: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  optimizedTime: {
    color: '#3B82F6',
  },
  timeSaved: {
    fontSize: 12,
    fontWeight: '600',
    color: '#10B981',
    marginTop: 2,
  },
  
  // Footer
  footer: {
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  confidenceBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: 6,
  },
  confidenceFill: {
    height: '100%',
    backgroundColor: '#3B82F6',
  },
  confidenceText: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
  },
  confidence: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
  },
});

export default DepartureRecommendationCard;

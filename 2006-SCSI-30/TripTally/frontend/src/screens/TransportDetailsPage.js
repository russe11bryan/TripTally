// pages/TransportDetailsPage.js
import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, Platform, StyleSheet as RNStyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import FontAwesome5 from '@expo/vector-icons/FontAwesome5';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import TransportDetailsCard from '../components/TransportDetailsCard';
import useThemedStyles from '../hooks/useThemedStyles';
import { BASE_URL } from '../config/keys';

export default function TransportDetailsPage({ navigation, route }) {
  const [details, setDetails] = useState({
    Time: 'Loading...',
    Distance: 'Loading...',
    'ERP Fare': 'Loading...',
    'Fuel Cost Per Km': 'Loading...',
    'Total Cost': 'Loading...',
    CO2: 'Loading...',
    'Departure Time': 'Loading...',
    'Arrival Time': 'Loading...',
  });

  const [error, setError] = useState(null);

  const { 
    mode = 'Driving', 
    destination = 'Lee Wee Nam Library',
    coordinates = null,
    origin = null
  } = route?.params ?? {};

  useEffect(() => {
    // Reset error when coordinates or origin changes
    setError(null);
  }, [coordinates, origin]);

  const [carparks, setCarparks] = useState([]);
  const [loadingCarparks, setLoadingCarparks] = useState(false);
  const [routeSteps, setRouteSteps] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      if (!coordinates) {
        console.error('Missing destination coordinates');
        return;
      }
      
      setLoadingCarparks(false);
      try {
        const API_BASE = BASE_URL || (Platform.OS === 'android' ? 'http://10.0.2.2:8080' : 'http://localhost:8080');
        
        // Only fetch carparks for driving mode
        if (mode === 'Driving') {
          setLoadingCarparks(true);
          const carparkUrl = `${API_BASE}/metrics/carparks?latitude=${coordinates.latitude}&longitude=${coordinates.longitude}`;
          const carparkResponse = await fetch(carparkUrl);
          const carparkData = await carparkResponse.json();
          setCarparks(carparkData);
        }
        
        // Get route details based on transport mode
        const routeEndpoint = {
          'Driving': 'driving',
          'Public Transport': 'public-transport',
          'Walking': 'walking',
          'Cycling': 'cycling'
        }[mode];

        if (!routeEndpoint) {
          throw new Error(`Unsupported transport mode: ${mode}`);
        }

        let routeUrl = `${API_BASE}/metrics/${routeEndpoint}?dest_lat=${coordinates.latitude}&dest_lng=${coordinates.longitude}`;
        
        // Add origin coordinates if available
        if (origin && origin.latitude && origin.longitude) {
          routeUrl += `&origin_lat=${origin.latitude}&origin_lng=${origin.longitude}`;
        }
        
        const routeResponse = await fetch(routeUrl);
        const routeData = await routeResponse.json();
        
        // Base details that are common across all modes
        const updatedDetails = {
          Time: `${Math.round(routeData.duration_minutes)} mins`,
          Distance: `${(routeData.distance_km).toFixed(1)} km`,
          'Departure Time': routeData.departure_time,
          'Arrival Time': routeData.arrival_time,
        };

        // Mode-specific details
        if (mode === 'Driving') {
          updatedDetails['ERP Fare'] = `$${routeData.erp_charges.toFixed(2)}`;
          updatedDetails['Fuel Cost Per Km'] = `$${routeData.fuel_cost_per_km.toFixed(2)}`;
          updatedDetails['Total Cost'] = `$${(routeData.fuel_cost_sgd + routeData.erp_charges).toFixed(2)}`;
          updatedDetails['CO2'] = `${routeData.co2_emissions_kg.toFixed(1)} kg`;
          
          // Add traffic conditions for driving if available
          if (routeData.traffic_conditions) {
            updatedDetails['Traffic Conditions'] = routeData.traffic_conditions;
          }
        } else if (mode === 'Public Transport') {
          updatedDetails['Fare'] = `$${routeData.fare.toFixed(2)}`;
          updatedDetails['MRT Fare'] = `$${routeData.mrt_fare.toFixed(2)}`;
          updatedDetails['Bus Fare'] = `$${routeData.bus_fare.toFixed(2)}`;
          
          // Store route steps for detailed display
          if (routeData.route_details && Array.isArray(routeData.route_details)) {
            setRouteSteps(routeData.route_details);
          }
        } else if (mode === 'Walking') {
          // Fetch driving metrics to calculate CO2 saved
          try {
            const drivingUrl = `${API_BASE}/metrics/driving?dest_lat=${coordinates.latitude}&dest_lng=${coordinates.longitude}${origin && origin.latitude && origin.longitude ? `&origin_lat=${origin.latitude}&origin_lng=${origin.longitude}` : ''}`;
            const drivingResponse = await fetch(drivingUrl);
            const drivingData = await drivingResponse.json();
            updatedDetails['CO2 Saved'] = `${drivingData.co2_emissions_kg.toFixed(1)} kg`;
          } catch (error) {
            console.error('Error fetching driving metrics for CO2:', error);
            updatedDetails['CO2 Saved'] = 'N/A';
          }
          
          if (routeData.elevation_gain) {
            updatedDetails['Elevation Gain'] = `${routeData.elevation_gain}m`;
          }
        } else if (mode === 'Cycling') {
          // Fetch driving metrics to calculate CO2 saved
          try {
            const drivingUrl = `${API_BASE}/metrics/driving?dest_lat=${coordinates.latitude}&dest_lng=${coordinates.longitude}${origin && origin.latitude && origin.longitude ? `&origin_lat=${origin.latitude}&origin_lng=${origin.longitude}` : ''}`;
            const drivingResponse = await fetch(drivingUrl);
            const drivingData = await drivingResponse.json();
            updatedDetails['CO2 Saved'] = `${drivingData.co2_emissions_kg.toFixed(1)} kg`;
          } catch (error) {
            console.error('Error fetching driving metrics for CO2:', error);
            updatedDetails['CO2 Saved'] = 'N/A';
          }
          
          if (routeData.elevation_gain) {
            updatedDetails['Elevation Gain'] = `${routeData.elevation_gain}m`;
          }
        }
        
        setDetails(updatedDetails);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error.message);
        
        // Clear all details with N/A
        const errorDetails = {};
        Object.keys(details).forEach(key => {
          errorDetails[key] = error.message || 'Error';
        });
        setDetails(errorDetails);
        
        // Clear carparks if in driving mode
        if (mode === 'Driving') {
          setCarparks([]);
        }
      } finally {
        setLoadingCarparks(false);
      }
    };

    fetchData();
  }, [mode, coordinates, origin]);

  // Transform details object to include carpark information
  const enhancedDetails = {
    ...details,
    ...(mode === 'Driving' && carparks.length > 0 && {
      'Nearby Carparks': 'Available below',
    }),
  };

  const { styles, theme } = useThemedStyles(({ colors }) => ({
    container: {
      flex: 1,
      backgroundColor: colors.background,
      paddingTop: 60,
      paddingHorizontal: 20,
    },
    card: {
      backgroundColor: colors.card,
      borderRadius: 12,
      padding: 16,
      borderWidth: RNStyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    carparkTitle: {
      fontSize: 15,
      fontWeight: '600',
      color: colors.text,
      flex: 1,
      marginRight: 8,
    },
    carparkDetails: {
      gap: 4,
    },
    carparkRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginVertical: 2,
    },
    carparkLabel: {
      fontSize: 13,
      color: colors.muted,
      marginRight: 8,
    },
    carparkValue: {
      fontSize: 13,
      fontWeight: '500',
      color: colors.text,
      marginBottom: 2,
    },
    noCarparks: {
      textAlign: 'center',
      color: colors.muted,
      marginTop: 20,
      fontSize: 15,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 20,
    },
    title: {
      fontSize: 16,
      fontWeight: '700',
      color: colors.text,
    },
    modeSection: {
      alignItems: 'center',
      marginBottom: 20,
    },
    modeText: {
      fontSize: 15,
      fontWeight: '600',
      color: colors.text,
    },
    stepCard: {
      backgroundColor: colors.card,
      borderRadius: 12,
      padding: 16,
      borderWidth: RNStyleSheet.hairlineWidth,
      borderColor: colors.border,
      marginBottom: 10,
    },
    stepHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    stepIcon: {
      marginRight: 12,
    },
    stepTitle: {
      fontSize: 15,
      fontWeight: '600',
      color: colors.text,
      flex: 1,
    },
    stepFare: {
      fontSize: 15,
      fontWeight: '700',
      color: colors.accent,
    },
    stepDetails: {
      gap: 6,
    },
    stepRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    stepLabel: {
      fontSize: 13,
      color: colors.muted,
    },
    stepValue: {
      fontSize: 13,
      fontWeight: '500',
      color: colors.text,
    },
  }));

  const modeIcons = {
    Driving: <FontAwesome5 name="car" size={38} color={theme.colors.text} style={{ marginBottom: 4 }} />,
    'Public Transport': <Ionicons name="train" size={38} color={theme.colors.text} style={{ marginBottom: 4 }} />,
    Walking: <Ionicons name="walk" size={38} color={theme.colors.text} style={{ marginBottom: 4 }} />,
    Cycling: (
      <MaterialCommunityIcons
        name="bike"
        size={40}
        color={theme.colors.text}
        style={{ marginBottom: 2 }}
      />
    ),
  };

  const modeIcon = modeIcons[mode] ?? modeIcons.Driving;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>{destination.toUpperCase()}</Text>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="close" size={24} color={theme.colors.muted} />
        </TouchableOpacity>
      </View>

      {/* Mode icon + label */}
      <View style={styles.modeSection}>
        {modeIcon}
        <Text style={styles.modeText}>{mode}</Text>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Details Card */}
        <TransportDetailsCard details={enhancedDetails} />

        {/* Carparks Section */}
        {mode === 'Driving' && (
          <View style={{ marginTop: 20 }}>
            <Text style={[styles.title, { marginBottom: 10 }]}>NEARBY CARPARKS</Text>
            {loadingCarparks ? (
              <ActivityIndicator size="large" color={theme.colors.accent} style={{ marginTop: 20 }} />
            ) : carparks.length > 0 ? (
              carparks.map((carpark, index) => (
                <TouchableOpacity 
                  key={`${carpark.development}-${index}`}
                  style={[
                    styles.card,
                    { marginBottom: index === carparks.length - 1 ? 20 : 10 }
                  ]}
                  onPress={() => {
                    if (carpark.latitude && carpark.longitude) {
                      navigation.navigate('Directions', {
                        origin: origin || null,
                        destination: {
                          name: carpark.development || carpark.area,
                          latitude: carpark.latitude,
                          longitude: carpark.longitude
                        },
                        initialMode: 'driving'
                      });
                    }
                  }}
                  activeOpacity={0.7}
                >
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <Text style={styles.carparkTitle}>
                      {carpark.development || carpark.area}
                      {carpark.total_sections > 1 && ` (${carpark.total_sections} sections)`}
                    </Text>
                    <Ionicons name="navigate-circle-outline" size={20} color={theme.colors.accent} />
                  </View>
                  <View style={styles.carparkDetails}>
                    <View style={styles.carparkRow}>
                      <Text style={styles.carparkLabel}>Total Available Lots:</Text>
                      <Text style={styles.carparkValue}>{carpark.available_lots}</Text>
                    </View>
                    {Array.isArray(carpark.sections) && carpark.sections.length > 1 && (
                      <View style={{ marginTop: 4 }}>
                        {carpark.sections.map((section, idx) => (
                          <View key={section.id} style={[styles.carparkRow, { paddingLeft: 16 }]}>
                            <Text style={[styles.carparkLabel, { fontSize: 12 }]}>
                              {`Section ${idx + 1} (${section.distance_meters}m):`}
                            </Text>
                            <Text style={[styles.carparkValue, { fontSize: 12 }]}>
                              {section.available_lots} lots
                            </Text>
                          </View>
                        ))}
                      </View>
                    )}
                    
                    <View style={styles.carparkRow}>
                      <Text style={styles.carparkLabel}>Distance:</Text>
                      <Text style={styles.carparkValue}>{carpark.distance_meters}m</Text>
                    </View>
                    <View>
                      <Text style={[styles.carparkLabel, { marginBottom: 4 }]}>Parking Rates:</Text>
                      {(carpark.weekday_rate_1 === "N/A" && 
                        carpark.saturday_rates === "N/A" && 
                        carpark.sunday_public_holiday_rates === "N/A") ? (
                        <View style={[styles.carparkRow, { paddingLeft: 12 }]}>
                          <Text style={styles.carparkValue}>N/A</Text>
                        </View>
                      ) : (
                        <>
                          {carpark.weekday_rate_1 !== "N/A" && (
                            <View style={[styles.carparkRow, { paddingLeft: 12 }]}>
                              <Text style={[styles.carparkLabel, { flex: 1 }]}>Weekday:</Text>
                              <View style={{ flex: 2 }}>
                                <Text style={styles.carparkValue}>
                                  {carpark.weekday_rate_1}
                                </Text>
                                {carpark.weekday_rate_2 !== "Not available" && (
                                  <Text style={styles.carparkValue}>
                                    {carpark.weekday_rate_2}
                                  </Text>
                                )}
                              </View>
                            </View>
                          )}
                          {carpark.saturday_rates !== "N/A" && carpark.saturday_rates !== "Not available" && (
                            <View style={[styles.carparkRow, { paddingLeft: 12 }]}>
                              <Text style={[styles.carparkLabel, { flex: 1 }]}>Weekend:</Text>
                              <View style={{ flex: 2 }}>
                                <Text style={styles.carparkValue}>
                                  {carpark.saturday_rates}
                                </Text>
                              </View>
                            </View>
                          )}
                          {carpark.sunday_public_holiday_rates !== "N/A" && 
                           carpark.sunday_public_holiday_rates !== "Not available" && 
                           carpark.sunday_public_holiday_rates.toLowerCase() !== "same as saturday" && (
                            <View style={[styles.carparkRow, { paddingLeft: 12 }]}>
                              <Text style={[styles.carparkLabel, { flex: 1 }]}>Holiday:</Text>
                              <View style={{ flex: 2 }}>
                                <Text style={styles.carparkValue}>
                                  {carpark.sunday_public_holiday_rates}
                                </Text>
                              </View>
                            </View>
                          )}
                        </>
                      )}
                    </View>
                  </View>
                </TouchableOpacity>
              ))
            ) : (
              <Text style={styles.noCarparks}>No carparks found within 1.5km</Text>
            )}
          </View>
        )}

        {/* Route Steps Section for Public Transport */}
        {mode === 'Public Transport' && routeSteps.length > 0 && (
          <View style={{ marginTop: 20 }}>
            <Text style={[styles.title, { marginBottom: 10 }]}>JOURNEY BREAKDOWN</Text>
            {routeSteps.map((step, index) => {
              // Determine icon based on travel mode
              let stepIcon;
              if (step.travel_mode === 'WALKING') {
                stepIcon = <Ionicons name="walk" size={24} color={theme.colors.text} />;
              } else if (step.travel_mode === 'TRANSIT') {
                if (step.vehicle_type === 'BUS') {
                  stepIcon = <Ionicons name="bus" size={24} color={theme.colors.text} />;
                } else {
                  stepIcon = <Ionicons name="train" size={24} color={theme.colors.text} />;
                }
              }

              return (
                <View 
                  key={`step-${index}`}
                  style={[
                    styles.stepCard,
                    { marginBottom: index === routeSteps.length - 1 ? 20 : 10 }
                  ]}
                >
                  {/* Header with icon, title, and fare */}
                  <View style={styles.stepHeader}>
                    <View style={styles.stepIcon}>
                      {stepIcon}
                    </View>
                    <Text style={styles.stepTitle}>
                      {step.travel_mode === 'WALKING' 
                        ? 'Walk' 
                        : `${step.vehicle_type === 'BUS' ? 'Bus' : 'Train'} ${step.line_name || ''}`}
                    </Text>
                    {step.fare != null && (
                      <Text style={styles.stepFare}>${step.fare.toFixed(2)}</Text>
                    )}
                  </View>

                  {/* Step details */}
                  <View style={styles.stepDetails}>
                    {step.travel_mode === 'TRANSIT' && (
                      <>
                        <View style={styles.stepRow}>
                          <Text style={styles.stepLabel}>From:</Text>
                          <Text style={styles.stepValue}>{step.departure_stop}</Text>
                        </View>
                        <View style={styles.stepRow}>
                          <Text style={styles.stepLabel}>To:</Text>
                          <Text style={styles.stepValue}>{step.arrival_stop}</Text>
                        </View>
                        {step.num_stops > 0 && (
                          <View style={styles.stepRow}>
                            <Text style={styles.stepLabel}>Stops:</Text>
                            <Text style={styles.stepValue}>{step.num_stops}</Text>
                          </View>
                        )}
                        <View style={styles.stepRow}>
                          <Text style={styles.stepLabel}>Departure:</Text>
                          <Text style={styles.stepValue}>{step.departure_time}</Text>
                        </View>
                        <View style={styles.stepRow}>
                          <Text style={styles.stepLabel}>Arrival:</Text>
                          <Text style={styles.stepValue}>{step.arrival_time}</Text>
                        </View>
                      </>
                    )}
                    <View style={styles.stepRow}>
                      <Text style={styles.stepLabel}>Duration:</Text>
                      <Text style={styles.stepValue}>{step.duration}</Text>
                    </View>
                    <View style={styles.stepRow}>
                      <Text style={styles.stepLabel}>Distance:</Text>
                      <Text style={styles.stepValue}>{step.distance}</Text>
                    </View>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

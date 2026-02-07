import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator, Alert } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import * as Location from 'expo-location';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';
import { API_BASE_URL } from '../services/api';
import BottomDragTab from '../components/BottomDragTab';

export default function NearbyPlacesMap({ route, navigation }) {
  const { searchQuery, placeType, searchResults, userLocation: passedUserLocation } = route.params || {};
  const { theme } = useTheme();
  const styles = createStyles(theme.colors);
  const mapRef = useRef(null);

  const [loading, setLoading] = useState(true);
  const [places, setPlaces] = useState([]);
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [userLocation, setUserLocation] = useState(passedUserLocation || null);

  console.log('[NearbyPlacesMap] Received params:', { 
    searchQuery, 
    placeType, 
    searchResultsCount: searchResults?.length || 0,
    hasUserLocation: !!passedUserLocation 
  });

  // Calculate distance between two coordinates in kilometers using Haversine formula
  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance in km
  };

  // Format distance for display
  const formatDistance = (distanceKm) => {
    if (distanceKm < 1) {
      return `${Math.round(distanceKm * 1000)}m`;
    }
    return `${distanceKm.toFixed(1)}km`;
  };

  // Get user location and fetch nearby places
  useEffect(() => {
    (async () => {
      try {
        let userLoc = userLocation;
        
        // Get user location if not passed from SearchPage
        if (!userLoc) {
          const { status } = await Location.requestForegroundPermissionsAsync();
          if (status !== 'granted') {
            Alert.alert('Permission Denied', 'Location permission is required to find nearby places.');
            navigation.goBack();
            return;
          }

          const location = await Location.getCurrentPositionAsync({});
          userLoc = {
            latitude: location.coords.latitude,
            longitude: location.coords.longitude,
          };
          setUserLocation(userLoc);
        }

        // If we have search results from SearchPage, use them directly
        if (searchResults && searchResults.length > 0) {
          console.log('[NearbyPlacesMap] Using search results from SearchPage:', searchResults.length);
          
          // Convert search results to places format
          const convertedPlaces = searchResults
            .filter(result => result.lat && result.lng) // Only include results with coordinates
            .map(result => ({
              place_id: result.place_id || result.id,
              name: result.name,
              address: result.address || '',
              lat: result.lat,
              lng: result.lng,
              rating: result.rating || null,
              user_ratings_total: result.user_ratings_total || null,
              distance: result.distance || calculateDistance(
                userLoc.latitude,
                userLoc.longitude,
                result.lat,
                result.lng
              )
            }));
          
          // Sort by distance
          convertedPlaces.sort((a, b) => a.distance - b.distance);
          
          setPlaces(convertedPlaces);
          setLoading(false);
          
          // Fit map to show all markers
          if (convertedPlaces.length > 0 && mapRef.current) {
            const coordinates = convertedPlaces.map(place => ({
              latitude: place.lat,
              longitude: place.lng,
            }));
            
            // Add user location
            coordinates.push(userLoc);
            
            setTimeout(() => {
              mapRef.current?.fitToCoordinates(coordinates, {
                edgePadding: { top: 100, right: 50, bottom: 300, left: 50 },
                animated: true,
              });
            }, 500);
          }
        } else {
          // Fetch nearby places from API as fallback
          console.log('[NearbyPlacesMap] No search results, fetching from API');
          await fetchNearbyPlaces(userLoc);
        }
      } catch (error) {
        console.error('Error getting location:', error);
        Alert.alert('Error', 'Failed to get your location. Please try again.');
        setLoading(false);
      }
    })();
  }, []);

  const fetchNearbyPlaces = async (location) => {
    try {
      setLoading(true);
      const locationStr = `${location.latitude},${location.longitude}`;
      const radius = 5000; // 5km radius
      
      // Build URL with query parameters
      let url = `${API_BASE_URL}/maps/nearby?location=${encodeURIComponent(locationStr)}&radius=${radius}`;
      
      if (placeType) {
        url += `&type=${encodeURIComponent(placeType)}`;
      } else if (searchQuery) {
        url += `&keyword=${encodeURIComponent(searchQuery)}`;
      }

      const response = await fetch(url);
      const data = await response.json();

      if (data.status === 'OK' && data.routes) {
        // Add distance to each place and sort by distance
        const placesWithDistance = data.routes.map(place => ({
          ...place,
          distance: calculateDistance(
            location.latitude,
            location.longitude,
            place.lat,
            place.lng
          )
        }));

        // Sort by distance (closest first)
        placesWithDistance.sort((a, b) => a.distance - b.distance);
        
        setPlaces(placesWithDistance);
        
        // Fit map to show all markers
        if (placesWithDistance.length > 0 && mapRef.current) {
          const coordinates = placesWithDistance.map(place => ({
            latitude: place.lat,
            longitude: place.lng,
          }));
          
          // Add user location
          coordinates.push(location);
          
          setTimeout(() => {
            mapRef.current?.fitToCoordinates(coordinates, {
              edgePadding: { top: 100, right: 50, bottom: 300, left: 50 },
              animated: true,
            });
          }, 500);
        }
      } else {
        Alert.alert('No Results', 'No places found nearby. Try adjusting your search.');
      }
    } catch (error) {
      console.error('Error fetching nearby places:', error);
      Alert.alert('Error', 'Failed to fetch nearby places. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkerPress = (place) => {
    setSelectedPlace(place);
    
    // Animate to marker
    if (mapRef.current) {
      mapRef.current.animateToRegion({
        latitude: place.lat,
        longitude: place.lng,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      }, 500);
    }
  };

  const handleGetDirections = (place) => {
    navigation.navigate('Directions', {
      destination: {
        latitude: place.lat,
        longitude: place.lng,
        name: place.name,
      },
    });
  };

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        initialRegion={{
          latitude: userLocation?.latitude || 1.3521,
          longitude: userLocation?.longitude || 103.8198,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        }}
        showsUserLocation
        showsMyLocationButton={false}
      >
        {places.map((place) => (
          <Marker
            key={place.place_id}
            coordinate={{
              latitude: place.lat,
              longitude: place.lng,
            }}
            title={place.name}
            description={place.address}
            onPress={() => handleMarkerPress(place)}
            pinColor={selectedPlace?.place_id === place.place_id ? theme.colors.accent : 'red'}
          />
        ))}
      </MapView>

      {/* Back Button */}
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => navigation.goBack()}
      >
        <Ionicons name="arrow-back" size={24} color={theme.colors.text} />
      </TouchableOpacity>

      {/* Loading Indicator */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.accent} />
          <Text style={styles.loadingText}>Finding nearby places...</Text>
        </View>
      )}

      {/* Bottom Sheet with Places List */}
      <BottomDragTab
        initialPosition={200}
        collapsedHeight={80}
        maxHeight={500}
      >
        <View style={styles.bottomSheetHeader}>
          <Text style={styles.bottomSheetTitle}>
            {places.length} {places.length === 1 ? 'Place' : 'Places'} Found
          </Text>
          <Text style={styles.bottomSheetSubtitle}>
            {searchQuery ? `Search results for "${searchQuery}"` : placeType || 'Nearby places'}
            {places.length > 0 && places[0].distance !== undefined && (
              ` • Sorted by distance`
            )}
          </Text>
        </View>

        {!loading && places.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="location-outline" size={48} color={theme.colors.muted} />
            <Text style={styles.emptyText}>No places found nearby</Text>
            <Text style={styles.emptySubtext}>Try adjusting your search</Text>
          </View>
        ) : (
          <ScrollView 
            style={styles.placesList}
            showsVerticalScrollIndicator={false}
          >
            {places.map((place, index) => (
              <TouchableOpacity
                key={place.place_id}
                style={[
                  styles.placeCard,
                  selectedPlace?.place_id === place.place_id && styles.placeCardSelected,
                ]}
                onPress={() => handleMarkerPress(place)}
              >
                <View style={styles.placeCardLeft}>
                  <View style={styles.placeIconContainer}>
                    <Ionicons 
                      name="location" 
                      size={20} 
                      color={selectedPlace?.place_id === place.place_id ? theme.colors.accent : theme.colors.muted}
                    />
                  </View>
                  <View style={styles.placeInfo}>
                    <Text 
                      style={[
                        styles.placeName,
                        selectedPlace?.place_id === place.place_id && { color: theme.colors.accent }
                      ]}
                      numberOfLines={1}
                    >
                      {place.name}
                    </Text>
                    {place.address && (
                      <Text style={styles.placeAddress} numberOfLines={1}>
                        {place.address}
                      </Text>
                    )}
                    <View style={styles.placeMetadata}>
                      {place.rating && (
                        <View style={styles.ratingContainer}>
                          <Ionicons name="star" size={14} color="#FFA500" />
                          <Text style={styles.ratingText}>
                            {place.rating} {place.user_ratings_total && `(${place.user_ratings_total})`}
                          </Text>
                        </View>
                      )}
                      {place.distance !== undefined && (
                        <View style={styles.distanceContainer}>
                          <Ionicons name="walk" size={14} color={theme.colors.muted} />
                          <Text style={styles.distanceText}>
                            {formatDistance(place.distance)}
                          </Text>
                        </View>
                      )}
                    </View>
                  </View>
                </View>
                
                <TouchableOpacity
                  style={styles.directionsButton}
                  onPress={() => handleGetDirections(place)}
                >
                  <Ionicons name="navigate" size={20} color={theme.colors.accent} />
                </TouchableOpacity>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}
      </BottomDragTab>
    </View>
  );
}

const createStyles = (colors) => StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
  backButton: {
    position: 'absolute',
    top: 50,
    left: 20,
    backgroundColor: colors.card,
    borderRadius: 20,
    padding: 8,
    elevation: 3,
    shadowColor: '#000',
    shadowOpacity: colors.mode === 'dark' ? 0.3 : 0.15,
    shadowRadius: 6,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  loadingContainer: {
    position: 'absolute',
    top: '40%',
    alignSelf: 'center',
    backgroundColor: colors.card,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  loadingText: {
    marginTop: 12,
    color: colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
  bottomSheetHeader: {
    marginBottom: 16,
  },
  bottomSheetTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.text,
  },
  bottomSheetSubtitle: {
    fontSize: 14,
    color: colors.muted,
    marginTop: 4,
  },
  placesList: {
    flex: 1,
  },
  placeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    backgroundColor: colors.background,
  },
  placeCardSelected: {
    backgroundColor: colors.accent + '10',
  },
  placeCardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  placeIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.pillAlt,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  placeInfo: {
    flex: 1,
  },
  placeName: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
    marginBottom: 4,
  },
  placeAddress: {
    fontSize: 14,
    color: colors.muted,
    marginBottom: 4,
  },
  placeMetadata: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingText: {
    fontSize: 12,
    color: colors.text,
    marginLeft: 4,
  },
  distanceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  distanceText: {
    fontSize: 12,
    color: colors.muted,
    marginLeft: 4,
    fontWeight: '600',
  },
  directionsButton: {
    padding: 8,
    marginLeft: 8,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    marginTop: 12,
  },
  emptySubtext: {
    fontSize: 14,
    color: colors.muted,
    marginTop: 4,
  },
});

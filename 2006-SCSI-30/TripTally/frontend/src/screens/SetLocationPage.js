import React, { useState, useMemo, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, TextInput, ScrollView, ActivityIndicator, Alert, Keyboard } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { apiPut, apiGet } from '../services/api';
import { BASE_URL } from '../config/keys';

const API_BASE = BASE_URL;

const newSessionToken = () =>
  Math.random().toString(36).slice(2) + Date.now().toString(36);

export default function SetLocationPage({ route, navigation }) {
  const { locationType } = route.params; // 'home' or 'work'
  const { user } = useAuth();
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [region, setRegion] = useState({
    latitude: 1.3483,
    longitude: 103.6831,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  });
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  const searchTimeoutRef = useRef(null);
  const sessionRef = useRef(newSessionToken());
  const mapRef = useRef(null);

  const locationTitle = locationType === 'home' ? 'Home' : 'Work';
  const locationIcon = locationType === 'home' ? 'home' : 'briefcase';

  // Get user location
  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') return;

        const location = await Location.getCurrentPositionAsync({});
        const currentPos = {
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
        };
        setUserLocation(currentPos);
        setRegion({
          ...currentPos,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        });
      } catch (error) {
        console.error('Error getting location:', error);
      }
    })();
  }, []);

  // Calculate distance between two coordinates
  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371e3; // Earth radius in meters
    const φ1 = (lat1 * Math.PI) / 180;
    const φ2 = (lat2 * Math.PI) / 180;
    const Δφ = ((lat2 - lat1) * Math.PI) / 180;
    const Δλ = ((lon2 - lon1) * Math.PI) / 180;

    const a =
      Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
      Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c; // Distance in meters
  };

  const formatDistance = (meters) => {
    if (meters < 1000) return `${Math.round(meters)}m`;
    return `${(meters / 1000).toFixed(1)}km`;
  };

  // Debounced search effect
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    searchTimeoutRef.current = setTimeout(() => {
      handleSearch();
    }, 500);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  const handleSearch = async () => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) return;

    setIsSearching(true);
    try {
      let list = [];

      // 1) Nearby Search (if we have user location) — ranked by distance
      if (userLocation) {
        try {
          const nearbyUrl = `${API_BASE}/maps/nearby?location=${userLocation.latitude},${userLocation.longitude}&radius=10000&keyword=${encodeURIComponent(searchQuery)}&rankby=distance`;
          const nearbyRes = await fetch(nearbyUrl);
          
          if (nearbyRes.ok) {
            const nearbyData = await nearbyRes.json();
            const arr = Array.isArray(nearbyData?.results)
              ? nearbyData.results
              : nearbyData?.routes || [];
            if (nearbyData.status === "OK" && arr.length > 0) {
              list = arr.map((place) => {
                const distance = calculateDistance(
                  userLocation.latitude,
                  userLocation.longitude,
                  place.lat,
                  place.lng
                );
                return {
                  id: place.place_id || place.name,
                  name: place.name,
                  address: place.address || null,
                  latitude: place.lat,
                  longitude: place.lng,
                  distance,
                };
              });
            }
          }
        } catch (nearbyError) {
          console.log('Nearby search error:', nearbyError);
        }
      }

      // 2) Autocomplete: fetch BOTH biased and global, then merge & de-dupe
      const fetchPredictions = async (url) => {
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data = await res.json();
        return (data?.predictions || []).map((p) => ({
          id: p.place_id || p.description,
          name: p.structured_formatting?.main_text || p.description.split(',')[0],
          address: p.description,
          place_id: p.place_id,
        }));
      };

      const baseQS = `input=${encodeURIComponent(searchQuery)}`;
      const biasedQS = userLocation
        ? `${baseQS}&location=${userLocation.latitude},${userLocation.longitude}&radius=10000`
        : baseQS;

      const urlBiased = `${API_BASE}/maps/places-autocomplete?${biasedQS}`;
      const urlGlobal = `${API_BASE}/maps/places-autocomplete?${baseQS}`;

      const [biasedPreds, globalPreds] = await Promise.all([
        fetchPredictions(urlBiased),
        fetchPredictions(urlGlobal),
      ]);

      // merge + de-dupe by place_id (or name fallback)
      const seen = new Set();
      const mergedPreds = [...biasedPreds, ...globalPreds].filter((it) => {
        const key = it.place_id || it.name;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });

      // Enrich predictions with coords + distance (if we have location)
      let enrichedPreds = mergedPreds;
      if (userLocation && mergedPreds.length > 0) {
        enrichedPreds = await Promise.all(
          mergedPreds.map(async (item) => {
            try {
              if (!item.place_id)
                return { ...item, distance: null };
              const detailsUrl = `${API_BASE}/maps/place-details?place_id=${encodeURIComponent(
                item.place_id
              )}`;
              const detailsRes = await fetch(detailsUrl);
              if (!detailsRes.ok)
                return { ...item, distance: null };
              const detailsData = await detailsRes.json();

              const lat =
                detailsData?.lat ??
                detailsData?.result?.geometry?.location?.lat;
              const lng =
                detailsData?.lng ??
                detailsData?.result?.geometry?.location?.lng;

              if (lat && lng) {
                const distance = calculateDistance(
                  userLocation.latitude,
                  userLocation.longitude,
                  lat,
                  lng
                );
                return { ...item, distance, latitude: lat, longitude: lng };
              }
              return { ...item, distance: null };
            } catch (e) {
              return { ...item, distance: null };
            }
          })
        );

        // sort by distance if available
        enrichedPreds.sort((a, b) => {
          if (a.distance == null && b.distance == null) return 0;
          if (a.distance == null) return 1;
          if (b.distance == null) return -1;
          return a.distance - b.distance;
        });
      }

      // 3) If Nearby list already has results, append any *new* predictions not present
      if (list.length > 0) {
        const existing = new Set(
          list.map((x) => x.place_id || x.id || x.name)
        );
        const toAppend = enrichedPreds.filter((p) => {
          const key = p.place_id || p.id || p.name;
          return !existing.has(key);
        });
        list = [...list, ...toAppend];
      } else {
        list = enrichedPreds;
      }

      console.log('Search results with coordinates:', list);
      setSearchResults(list);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectPlace = (place) => {
    // Dismiss keyboard first
    Keyboard.dismiss();
    
    setSelectedLocation(place);
    const newRegion = {
      latitude: place.latitude,
      longitude: place.longitude,
      latitudeDelta: 0.01,
      longitudeDelta: 0.01,
    };
    setRegion(newRegion);
    
    // Animate map to new location after a brief delay to ensure map is ready
    setTimeout(() => {
      if (mapRef.current) {
        mapRef.current.animateToRegion(newRegion, 1000);
      }
    }, 100);
    
    setSearchResults([]);
    setSearchQuery('');
  };

  const handleMapPress = (e) => {
    const coordinate = e.nativeEvent.coordinate;
    setSelectedLocation({
      name: 'Selected Location',
      address: `${coordinate.latitude.toFixed(6)}, ${coordinate.longitude.toFixed(6)}`,
      latitude: coordinate.latitude,
      longitude: coordinate.longitude,
    });
  };

  const handleSaveLocation = async () => {
    if (!selectedLocation) {
      Alert.alert('No Location Selected', 'Please select a location on the map first.');
      return;
    }

    if (!user?.id) {
      Alert.alert('Error', 'User not found. Please log in again.');
      return;
    }

    try {
      setIsSaving(true);
      
      const payload = {};
      if (locationType === 'home') {
        payload.home_latitude = selectedLocation.latitude;
        payload.home_longitude = selectedLocation.longitude;
        payload.home_address = selectedLocation.address;
      } else {
        payload.work_latitude = selectedLocation.latitude;
        payload.work_longitude = selectedLocation.longitude;
        payload.work_address = selectedLocation.address;
      }

      // Save location to user profile
      await apiPut(`/users/${user.id}/locations`, payload);

      Alert.alert(
        'Success',
        `${locationTitle} location has been saved!`,
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (error) {
      console.error('Error saving location:', error);
      Alert.alert('Error', `Failed to save location: ${error.message}`);
    } finally {
      setIsSaving(false);
    }
  };  return (
    <View style={styles.root}>
      <MapView
        ref={mapRef}
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        initialRegion={region}
        onPress={handleMapPress}
      >
        {selectedLocation && (
          <Marker
            coordinate={{
              latitude: selectedLocation.latitude,
              longitude: selectedLocation.longitude,
            }}
            title={selectedLocation.name}
            description={selectedLocation.address}
          >
            <View style={styles.customMarker}>
              <Ionicons name={locationIcon} size={24} color="#fff" />
            </View>
          </Marker>
        )}
      </MapView>

      {/* Back Button */}
      <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
        <Ionicons name="arrow-back" size={24} color={theme.colors.text} />
      </TouchableOpacity>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color={theme.colors.muted} />
          <TextInput
            style={styles.searchInput}
            placeholder={`Search for your ${locationType} location...`}
            placeholderTextColor={theme.colors.muted}
            value={searchQuery}
            onChangeText={setSearchQuery}
            autoCorrect={false}
          />
          {isSearching ? (
            <ActivityIndicator size="small" color={theme.colors.accent} />
          ) : searchQuery.length > 0 ? (
            <TouchableOpacity onPress={() => {
              setSearchQuery('');
              setSearchResults([]);
            }}>
              <Ionicons name="close-circle" size={20} color={theme.colors.muted} />
            </TouchableOpacity>
          ) : null}
        </View>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <ScrollView 
            style={styles.resultsContainer} 
            keyboardShouldPersistTaps="handled"
            nestedScrollEnabled={true}
            showsVerticalScrollIndicator={true}
          >
            {searchResults.map((result) => (
              <TouchableOpacity
                key={result.id}
                style={styles.resultItem}
                onPress={() => handleSelectPlace(result)}
              >
                <Ionicons name="location" size={20} color={theme.colors.accent} />
                <View style={styles.resultInfo}>
                  <Text style={styles.resultName}>{result.name}</Text>
                  {result.address && (
                    <Text style={styles.resultAddress} numberOfLines={1}>
                      {result.address}
                    </Text>
                  )}
                  {result.distance !== null && result.distance !== undefined && (
                    <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 2 }}>
                      <Ionicons name="walk" size={12} color={theme.colors.muted} />
                      <Text style={styles.distanceText}>{formatDistance(result.distance)}</Text>
                    </View>
                  )}
                </View>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}
      </View>

      {/* Bottom Card */}
      <View style={styles.bottomCard}>
        <View style={styles.cardHeader}>
          <View style={styles.headerIcon}>
            <Ionicons name={locationIcon} size={24} color={theme.colors.accent} />
          </View>
          <Text style={styles.listTitle}>Set {locationTitle} Location</Text>
        </View>

        {selectedLocation ? (
          <View style={styles.selectedInfo}>
            <View style={styles.selectedIconContainer}>
              <Ionicons name="location" size={20} color={theme.colors.accent} />
            </View>
            <View style={styles.selectedDetails}>
              <Text style={styles.selectedName}>{selectedLocation.name}</Text>
              <Text style={styles.selectedAddress} numberOfLines={2}>
                {selectedLocation.address}
              </Text>
            </View>
          </View>
        ) : (
          <Text style={styles.instructions}>
            Search for a place or tap anywhere on the map to select your {locationType} location
          </Text>
        )}

        <TouchableOpacity
          style={[styles.saveButton, (!selectedLocation || isSaving) && styles.saveButtonDisabled]}
          onPress={handleSaveLocation}
          disabled={!selectedLocation || isSaving}
        >
          {isSaving ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.saveButtonText}>Save {locationTitle} Location</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    root: {
      flex: 1,
    },
    map: {
      flex: 1,
    },
    backButton: {
      position: 'absolute',
      top: 55,
      left: 20,
      backgroundColor: colors.card,
      borderRadius: 12,
      width: 44,
      height: 44,
      justifyContent: 'center',
      alignItems: 'center',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: colors.mode === 'dark' ? 0.3 : 0.15,
      shadowRadius: 6,
      elevation: 3,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    searchContainer: {
      position: 'absolute',
      top: 55,
      left: 76,
      right: 20,
    },
    searchBar: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: colors.card,
      borderRadius: 12,
      paddingHorizontal: 12,
      height: 44,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: colors.mode === 'dark' ? 0.3 : 0.15,
      shadowRadius: 6,
      elevation: 3,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    searchInput: {
      flex: 1,
      marginLeft: 8,
      fontSize: 16,
      color: colors.text,
    },
    resultsContainer: {
      marginTop: 8,
      backgroundColor: colors.card,
      borderRadius: 12,
      maxHeight: 200,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: colors.mode === 'dark' ? 0.3 : 0.15,
      shadowRadius: 6,
      elevation: 3,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    resultItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: colors.border,
    },
    resultInfo: {
      flex: 1,
      marginLeft: 12,
    },
    resultName: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 2,
    },
    resultAddress: {
      fontSize: 14,
      color: colors.muted,
    },
    distanceText: {
      fontSize: 12,
      color: colors.muted,
      marginLeft: 4,
      fontWeight: '600',
    },
    bottomCard: {
      position: 'absolute',
      left: 12,
      right: 12,
      bottom: 20,
      backgroundColor: colors.card,
      borderRadius: 16,
      padding: 16,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: colors.mode === 'dark' ? 0.3 : 0.2,
      shadowRadius: 8,
      elevation: 5,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    cardHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    headerIcon: {
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: colors.accent + '20',
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: 12,
    },
    listTitle: {
      fontSize: 18,
      fontWeight: '700',
      color: colors.text,
      flex: 1,
    },
    instructions: {
      fontSize: 14,
      color: colors.muted,
      marginBottom: 12,
      textAlign: 'center',
    },
    selectedInfo: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
      padding: 12,
      backgroundColor: colors.pillAlt,
      borderRadius: 12,
    },
    selectedIconContainer: {
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: colors.accent + '20',
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: 12,
    },
    selectedDetails: {
      flex: 1,
    },
    selectedName: {
      fontSize: 16,
      fontWeight: '700',
      color: colors.text,
      marginBottom: 4,
    },
    selectedAddress: {
      fontSize: 14,
      color: colors.muted,
    },
    saveButton: {
      backgroundColor: colors.accent,
      padding: 14,
      borderRadius: 12,
      alignItems: 'center',
    },
    saveButtonDisabled: {
      backgroundColor: colors.muted,
      opacity: 0.5,
    },
    saveButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '700',
    },
    customMarker: {
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: colors.accent,
      justifyContent: 'center',
      alignItems: 'center',
      borderWidth: 3,
      borderColor: '#fff',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.3,
      shadowRadius: 4,
      elevation: 5,
    },
  });

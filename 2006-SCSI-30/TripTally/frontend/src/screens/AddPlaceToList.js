import React, { useState, useMemo, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, TextInput, Alert, ScrollView, ActivityIndicator, Keyboard } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { useTheme } from '../context/ThemeContext';
import { apiPost } from '../services/api';
import { BASE_URL } from '../config/keys';

const API_BASE = BASE_URL;

const newSessionToken = () =>
  Math.random().toString(36).slice(2) + Date.now().toString(36);

// Input validation constants and function
const MAX_SEARCH_LENGTH = 200;
const MIN_SEARCH_LENGTH = 2;

const validateSearchInput = (text) => {
  // Check if empty or only whitespace
  if (!text || text.trim().length === 0) {
    return { isValid: false, error: 'Search cannot be empty' };
  }

  // Check minimum length
  if (text.trim().length < MIN_SEARCH_LENGTH) {
    return { isValid: false, error: `Search must be at least ${MIN_SEARCH_LENGTH} characters` };
  }

  // Check maximum length
  if (text.length > MAX_SEARCH_LENGTH) {
    return { isValid: false, error: `Search is too long (max ${MAX_SEARCH_LENGTH} characters)` };
  }

  // Check for spam patterns (10 or more repeated characters)
  const spamPattern = /(.)\1{9,}/;
  if (spamPattern.test(text)) {
    return { isValid: false, error: 'Invalid search pattern' };
  }

  return { isValid: true, error: null };
};

// Photo URL helper (same as SearchPage)
const getPhotoUrl = (photoReference, maxWidth = 400) => {
  return `${BASE_URL}/maps/photo?photo_reference=${encodeURIComponent(photoReference)}&maxwidth=${maxWidth}`;
};

export default function AddPlaceToList({ route, navigation }) {
  const { list } = route.params;
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
  const [inputError, setInputError] = useState('');
  const [backendError, setBackendError] = useState('');
  
  const searchTimeoutRef = useRef(null);
  const sessionRef = useRef(newSessionToken());
  const mapRef = useRef(null);

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

  // Debounced search effect - triggers search as user types
  useEffect(() => {
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Clear errors when query is empty
    if (!searchQuery || searchQuery.trim().length === 0) {
      setInputError('');
      setBackendError('');
      setSearchResults([]);
      return;
    }

    // Validate input
    const validation = validateSearchInput(searchQuery);
    if (!validation.isValid) {
      setInputError(validation.error);
      setSearchResults([]);
      return;
    }

    // Clear input error if validation passed
    setInputError('');

    // Set new timeout to search after user stops typing
    searchTimeoutRef.current = setTimeout(() => {
      handleSearch();
    }, 500); // Wait 500ms after user stops typing

    // Cleanup function
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  const handleSearch = async () => {
    // Validate input before making API call
    const validation = validateSearchInput(searchQuery);
    if (!validation.isValid) {
      setInputError(validation.error);
      return;
    }

    setInputError('');
    setBackendError('');
    setIsSearching(true);
    try {
      let list = [];

      // 1) Nearby Search (if we have user location) — ranked by distance (same as SearchPage)
      if (userLocation) {
        try {
          const nearbyUrl = `${API_BASE}/maps/nearby?location=${userLocation.latitude},${userLocation.longitude}&radius=10000&keyword=${encodeURIComponent(searchQuery)}&rankby=distance`;
          const nearbyRes = await fetch(nearbyUrl);
          
          if (!nearbyRes.ok) {
            // Handle HTTP errors
            if (nearbyRes.status === 429) {
              setBackendError('⚠️ Too many requests. Please wait a moment and try again.');
            } else if (nearbyRes.status >= 500) {
              setBackendError(`❌ Server error (${nearbyRes.status}). Please try again later.`);
            } else if (nearbyRes.status === 404) {
              setBackendError('❌ Search service not found (404).');
            } else {
              setBackendError(`❌ Request failed (${nearbyRes.status}). Please try again.`);
            }
            return;
          }
          
          if (nearbyRes.ok) {
            const nearbyData = await nearbyRes.json();
            const arr = Array.isArray(nearbyData?.results)
              ? nearbyData.results
              : nearbyData?.routes || [];
            if (nearbyData.status === 'OK' && arr.length > 0) {
              list = arr.map((place) => {
                const distance = calculateDistance(
                  userLocation.latitude,
                  userLocation.longitude,
                  place.lat,
                  place.lng
                );
                const photoRef = place?.photo?.photo_reference;
                const photoUrl = photoRef ? getPhotoUrl(photoRef, 120) : null;
                return {
                  id: place.place_id || place.name,
                  name: place.name,
                  address: place.address || null,
                  place_id: place.place_id,
                  latitude: place.lat,
                  longitude: place.lng,
                  distance,
                  photoUrl,
                };
              });
            }
          }
        } catch (nearbyError) {
          console.error('Nearby search error:', nearbyError);
          setBackendError(`❌ Network error: ${nearbyError.message}`);
        }
      }

      // 2) Autocomplete: fetch BOTH biased and global, then merge & de-dupe (same as SearchPage)
      const fetchPredictions = async (url) => {
        const res = await fetch(url);
        if (!res.ok) {
          if (res.status === 429) {
            setBackendError('⚠️ Too many requests (429). Please wait a moment.');
            return [];
          }
          if (res.status >= 500) {
            setBackendError(`❌ Server error (${res.status}). Please try again later.`);
            return [];
          }
          if (res.status === 422) {
            setBackendError('❌ Invalid request format (422).');
            return [];
          }
          setBackendError(`❌ Request failed (${res.status}).`);
          throw new Error(`HTTP ${res.status}`);
        }
        const data = await res.json();
        return (data?.predictions || []).map((p) => ({
          id: p.place_id || p.description,
          name: p.description,
          place_id: p.place_id,
        }));
      };

      const baseQS = `input=${encodeURIComponent(searchQuery)}&sessiontoken=${encodeURIComponent(
        sessionRef.current
      )}`;
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

      // Enrich predictions with coords + distance + small photo (if we have location)
      let enrichedPreds = mergedPreds;
      if (userLocation && mergedPreds.length > 0) {
        enrichedPreds = await Promise.all(
          mergedPreds.map(async (item) => {
            try {
              if (!item.place_id)
                return { ...item, distance: null, photoUrl: null, latitude: null, longitude: null };
              const detailsUrl = `${API_BASE}/maps/place-details?place_id=${encodeURIComponent(
                item.place_id
              )}`;
              const detailsRes = await fetch(detailsUrl);
              if (!detailsRes.ok)
                return { ...item, distance: null, photoUrl: null, latitude: null, longitude: null };
              const detailsData = await detailsRes.json();

              const lat =
                detailsData?.lat ??
                detailsData?.result?.geometry?.location?.lat;
              const lng =
                detailsData?.lng ??
                detailsData?.result?.geometry?.location?.lng;

              const photoRef =
                detailsData?.photos?.[0]?.photo_reference ?? null;
              const photoUrl = photoRef ? getPhotoUrl(photoRef, 120) : null;

              const distance = lat && lng
                ? calculateDistance(
                    userLocation.latitude,
                    userLocation.longitude,
                    parseFloat(lat),
                    parseFloat(lng)
                  )
                : null;

              return {
                ...item,
                latitude: lat ? parseFloat(lat) : null,
                longitude: lng ? parseFloat(lng) : null,
                distance,
                photoUrl,
              };
            } catch (err) {
              console.error('Error enriching place:', err);
              return { ...item, distance: null, photoUrl: null, latitude: null, longitude: null };
            }
          })
        );
      } else if (mergedPreds.length > 0) {
        // No user location, just add structure
        enrichedPreds = mergedPreds.map(item => ({
          ...item,
          distance: null,
          photoUrl: null,
          latitude: null,
          longitude: null,
        }));
      }

      // Merge nearby + autocomplete, de-dupe by place_id
      const seenPlaceIds = new Set();
      const combined = [...list, ...enrichedPreds].filter((it) => {
        const key = it.place_id || it.id;
        if (seenPlaceIds.has(key)) return false;
        seenPlaceIds.add(key);
        return true;
      });

      console.log('Search results:', combined);
      setSearchResults(combined);
    } catch (error) {
      console.error('Search error:', error);
      
      // Handle network errors
      if (error.message === 'Network request failed' || !navigator.onLine) {
        setBackendError('❌ Network error. Please check your connection.');
      } else {
        setBackendError('❌ Search failed. Please try again.');
      }
      
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectPlace = (place) => {
    // Dismiss keyboard first
    Keyboard.dismiss();
    
    if (!place.latitude || !place.longitude) {
      Alert.alert('Error', 'Could not get location coordinates');
      return;
    }
    
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

  const handleAddPlace = async () => {
    if (!selectedLocation) {
      Alert.alert('No Location Selected', 'Please select a location on the map first.');
      return;
    }

    try {
      setIsSaving(true);
      await apiPost('/saved/places', {
        list_id: list.id,
        name: selectedLocation.name,
        address: selectedLocation.address,
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude,
      });

      Alert.alert(
        'Place Added',
        `"${selectedLocation.name}" has been added to "${list.name}"`,
        [
          {
            text: 'OK',
            onPress: () => navigation.navigate('SavePlace', { list }),
          },
        ]
      );
    } catch (error) {
      console.error('Error adding place:', error);
      Alert.alert('Error', 'Failed to add place. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <View style={styles.root}>
      <MapView
        ref={mapRef}
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        initialRegion={region}
        onPress={handleMapPress}
        showsUserLocation
        showsMyLocationButton={false}
      >
        {selectedLocation && (
          <Marker
            coordinate={{
              latitude: selectedLocation.latitude,
              longitude: selectedLocation.longitude,
            }}
            title={selectedLocation.name}
            description={selectedLocation.address}
          />
        )}
      </MapView>

      {/* Back Button */}
      <TouchableOpacity style={styles.backButton} onPress={() => navigation.navigate('Saved')}>
        <Ionicons name="arrow-back" size={24} color={theme.colors.text} />
      </TouchableOpacity>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color={theme.colors.muted} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search for a place..."
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
              setInputError('');
              setBackendError('');
            }}>
              <Ionicons name="close-circle" size={20} color={theme.colors.muted} />
            </TouchableOpacity>
          ) : null}
        </View>

        {/* Input Validation Error */}
        {inputError && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{inputError}</Text>
          </View>
        )}

        {/* Backend Error */}
        {backendError && (
          <View style={styles.backendErrorContainer}>
            <Text style={styles.errorText}>{backendError}</Text>
          </View>
        )}

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
          <Text style={styles.listTitle}>Add to: {list.name}</Text>
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
            Search for a place or tap anywhere on the map to select a location
          </Text>
        )}

        <TouchableOpacity
          style={[styles.addButton, (!selectedLocation || isSaving) && styles.addButtonDisabled]}
          onPress={handleAddPlace}
          disabled={!selectedLocation || isSaving}
        >
          {isSaving ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.addButtonText}>Add Place to List</Text>
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
      left: 5,
      backgroundColor: colors.card,
      borderRadius: 20,
      padding: 10,
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
      left: 60,
      right: 20,
    },
    searchBar: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: colors.card,
      borderRadius: 12,
      paddingHorizontal: 12,
      paddingVertical: 10,
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
    errorContainer: {
      marginTop: 8,
      backgroundColor: '#fee',
      borderLeftWidth: 3,
      borderLeftColor: '#f44',
      borderRadius: 8,
      padding: 10,
    },
    backendErrorContainer: {
      marginTop: 8,
      backgroundColor: '#fff3cd',
      borderLeftWidth: 3,
      borderLeftColor: '#ff9800',
      borderRadius: 8,
      padding: 10,
    },
    errorText: {
      color: '#d32f2f',
      fontSize: 14,
      fontWeight: '500',
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
      marginBottom: 12,
    },
    listTitle: {
      fontSize: 18,
      fontWeight: '700',
      color: colors.text,
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
    addButton: {
      backgroundColor: colors.accent,
      padding: 14,
      borderRadius: 12,
      alignItems: 'center',
    },
    addButtonDisabled: {
      backgroundColor: colors.muted,
      opacity: 0.5,
    },
    addButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '700',
    },
  });

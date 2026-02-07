import React, { useMemo, useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Alert, StyleSheet, ActivityIndicator } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import HeaderBackButton from '../components/HeaderBackButton';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
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

export default function AddRecommendationPage({ navigation }) {
  const { theme } = useTheme();
  const { user } = useAuth();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  
  // User location
  const [userLocation, setUserLocation] = useState(null);
  
  // Location state - default to Singapore
  const [location, setLocation] = useState({
    latitude: 1.3521,
    longitude: 103.8198,
  });
  const [region, setRegion] = useState({
    latitude: 1.3521,
    longitude: 103.8198,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  });
  const [locationName, setLocationName] = useState('');
  const [showMap, setShowMap] = useState(false);
  const mapRef = React.useRef(null);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [inputError, setInputError] = useState('');
  const [backendError, setBackendError] = useState('');
  const sessionRef = useRef(newSessionToken());
  const searchTimeoutRef = useRef(null);

  // Get user location
  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') return;

        const loc = await Location.getCurrentPositionAsync({});
        const currentPos = {
          latitude: loc.coords.latitude,
          longitude: loc.coords.longitude,
        };
        setUserLocation(currentPos);
        setLocation(currentPos);
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

  const handleSubmit = async () => {
    if (!title.trim() || !category.trim() || !description.trim() || !locationName.trim()) {
      Alert.alert('Missing info', 'Please fill in every field including location before submitting.');
      return;
    }

    setUploading(true);

    try {
      // Get username for added_by field
      const username = user?.username || user?.display_name || user?.email || null;
      const addedBy = username ? String(username) : 'Anonymous';

      console.log('Submitting suggestion:', {
        title: title.trim(),
        category: category.trim(),
        description: description.trim(),
        added_by: addedBy,
        latitude: location.latitude,
        longitude: location.longitude,
        location_name: locationName.trim() || null,
      });

      // Send to backend API
      const response = await apiPost('/suggestions', {
        title: title.trim(),
        category: category.trim(),
        description: description.trim(),
        added_by: addedBy,
        latitude: location.latitude,
        longitude: location.longitude,
        location_name: locationName.trim() || null,
      });

      console.log('Suggestion created:', response);

      Alert.alert('Success', 'Your recommendation has been shared with the community!', [
        {
          text: 'Great!',
          onPress: () => {
            // Clear form
            setTitle('');
            setCategory('');
            setDescription('');
            setLocation({ latitude: 1.3521, longitude: 103.8198 });
            setLocationName('');
            navigation.goBack();
          },
        },
      ]);
    } catch (error) {
      console.error('Error submitting suggestion:', error);
      Alert.alert('Error', error.message || 'Failed to submit recommendation. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleMapPress = (event) => {
    const { latitude, longitude } = event.nativeEvent.coordinate;
    setLocation({ latitude, longitude });
  };

  const searchLocation = async (query) => {
    // Validate input before making API call
    const validation = validateSearchInput(query);
    if (!validation.isValid) {
      setInputError(validation.error);
      setSearchResults([]);
      return;
    }

    setInputError('');
    setBackendError('');
    setSearching(true);
    try {
      let list = [];

      // 1) Nearby Search (if we have user location) — ranked by distance (same as SearchPage)
      if (userLocation) {
        try {
          const nearbyUrl = `${API_BASE}/maps/nearby?location=${userLocation.latitude},${userLocation.longitude}&radius=10000&keyword=${encodeURIComponent(query)}&rankby=distance`;
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

      const baseQS = `input=${encodeURIComponent(query)}&sessiontoken=${encodeURIComponent(
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

      setSearchResults(combined);
    } catch (error) {
      console.error('Error searching location:', error);
      
      // Handle network errors
      if (error.message === 'Network request failed' || !navigator.onLine) {
        setBackendError('❌ Network error. Please check your connection.');
      } else {
        setBackendError('❌ Search failed. Please try again.');
      }
      
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const selectSearchResult = (result) => {
    const newLocation = {
      latitude: result.latitude,
      longitude: result.longitude,
    };
    const newRegion = {
      ...newLocation,
      latitudeDelta: 0.01,
      longitudeDelta: 0.01,
    };
    
    setLocation(newLocation);
    setRegion(newRegion);
    setLocationName(result.name);
    
    if (mapRef.current) {
      mapRef.current.animateToRegion(newRegion, 500);
    }
    
    setSearchQuery('');
    setSearchResults([]);
  };

  const zoomIn = () => {
    if (mapRef.current) {
      const newRegion = {
        ...region,
        latitudeDelta: region.latitudeDelta / 2,
        longitudeDelta: region.longitudeDelta / 2,
      };
      setRegion(newRegion);
      mapRef.current.animateToRegion(newRegion, 300);
    }
  };

  const zoomOut = () => {
    if (mapRef.current) {
      const newRegion = {
        ...region,
        latitudeDelta: region.latitudeDelta * 2,
        longitudeDelta: region.longitudeDelta * 2,
      };
      setRegion(newRegion);
      mapRef.current.animateToRegion(newRegion, 300);
    }
  };

  const handleRegionChange = (newRegion) => {
    setRegion(newRegion);
  };

  return (
    <ScrollView style={styles.root}>
      <HeaderBackButton onPress={() => navigation.goBack()} />

      <Text style={styles.title}>Share A Recommendation</Text>

      <View style={styles.form}>
        <View>
          <Text style={styles.label}>Title</Text>
          <TextInput
            value={title}
            onChangeText={setTitle}
            placeholder="e.g. Scenic Cycling Route"
            placeholderTextColor={theme.colors.muted}
            style={styles.input}
          />
        </View>

        <View>
          <Text style={styles.label}>Category</Text>
          <TextInput
            value={category}
            onChangeText={setCategory}
            placeholder="e.g. Cycling, Family, Cafés"
            placeholderTextColor={theme.colors.muted}
            style={styles.input}
          />
        </View>

        <View>
          <Text style={styles.label}>Description</Text>
          <TextInput
            value={description}
            onChangeText={setDescription}
            multiline
            placeholder="Tell others why they should try this route or activity."
            placeholderTextColor={theme.colors.muted}
            style={[styles.input, styles.textArea]}
          />
        </View>

        {/* Location Section */}
        <View>
          <Text style={styles.label}>Location *</Text>
          <TextInput
            value={locationName}
            onChangeText={setLocationName}
            placeholder="e.g. Marina Bay, Sentosa Beach"
            placeholderTextColor={theme.colors.muted}
            style={styles.input}
          />
          
          <TouchableOpacity 
            onPress={() => setShowMap(!showMap)} 
            style={styles.mapToggleButton}
          >
            <Ionicons name={showMap ? "chevron-up" : "location"} size={20} color={theme.colors.accent} />
            <Text style={styles.mapToggleText}>
              {showMap ? "Hide Map" : "Pin Location on Map"}
            </Text>
          </TouchableOpacity>

          {showMap && (
            <View style={styles.mapContainer}>
              {/* Search Bar */}
              <View style={styles.searchContainer}>
                <Ionicons name="search" size={20} color={theme.colors.muted} style={styles.searchIcon} />
                <TextInput
                  value={searchQuery}
                  onChangeText={(text) => {
                    setSearchQuery(text);
                    // Clear errors when typing
                    if (!text || text.trim().length === 0) {
                      setInputError('');
                      setBackendError('');
                      setSearchResults([]);
                    } else {
                      searchLocation(text);
                    }
                  }}
                  placeholder="Search for a location..."
                  placeholderTextColor={theme.colors.muted}
                  style={styles.searchInput}
                />
                {searching && (
                  <ActivityIndicator size="small" color={theme.colors.accent} />
                )}
                {searchQuery.length > 0 && (
                  <TouchableOpacity
                    onPress={() => {
                      setSearchQuery('');
                      setSearchResults([]);
                      setInputError('');
                      setBackendError('');
                    }}
                    style={styles.clearButton}
                  >
                    <Ionicons name="close-circle" size={20} color={theme.colors.muted} />
                  </TouchableOpacity>
                )}
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
                  style={styles.searchResultsContainer}
                  nestedScrollEnabled={true}
                  showsVerticalScrollIndicator={true}
                  keyboardShouldPersistTaps="handled"
                >
                  {searchResults.map((item, index) => (
                    <TouchableOpacity
                      key={index}
                      style={styles.searchResultItem}
                      onPress={() => selectSearchResult(item)}
                    >
                      <Ionicons name="location-outline" size={20} color={theme.colors.accent} />
                      <View style={styles.searchResultTextContainer}>
                        <Text style={styles.searchResultText} numberOfLines={1}>
                          {item.name}
                        </Text>
                        {item.address && (
                          <Text style={styles.searchResultAddress} numberOfLines={1}>
                            {item.address}
                          </Text>
                        )}
                        {item.distance && (
                          <View style={styles.distanceContainer}>
                            <Ionicons name="walk" size={12} color={theme.colors.muted} />
                            <Text style={styles.distanceText}>{formatDistance(item.distance)}</Text>
                          </View>
                        )}
                      </View>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              )}

              <MapView
                provider={PROVIDER_GOOGLE}
                ref={mapRef}
                style={styles.map}
                region={region}
                onRegionChangeComplete={handleRegionChange}
                onPress={handleMapPress}
                showsUserLocation
                showsMyLocationButton={false}
              >
                <Marker
                  coordinate={location}
                  title="Selected Location"
                  description="Tap anywhere on the map to change"
                />
              </MapView>
              
              {/* Zoom Controls */}
              <View style={styles.zoomControls}>
                <TouchableOpacity style={styles.zoomButton} onPress={zoomIn}>
                  <Ionicons name="add" size={24} color={theme.colors.text} />
                </TouchableOpacity>
                <TouchableOpacity style={styles.zoomButton} onPress={zoomOut}>
                  <Ionicons name="remove" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>
              
              <Text style={styles.mapHint}>
                Tap anywhere on the map to pin your location
              </Text>
            </View>
          )}
        </View>

        <TouchableOpacity 
          onPress={handleSubmit} 
          style={[styles.submitButton, uploading && styles.submitButtonDisabled]}
          disabled={uploading}
        >
          {uploading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.submitText}>Submit Recommendation</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const createStyles = (theme) =>
  StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.colors.background,
      paddingTop: 48,
    },
    title: {
      fontWeight: '800',
      fontSize: 28,
      marginLeft: 16,
      marginBottom: 16,
      color: theme.colors.text,
    },
    form: {
      marginHorizontal: 16,
      gap: 20,
      paddingBottom: 40,
    },
    label: {
      fontWeight: '600',
      marginBottom: 8,
      color: theme.colors.text,
    },
    input: {
      borderWidth: 1,
      borderColor: theme.colors.border,
      borderRadius: 12,
      paddingHorizontal: 14,
      paddingVertical: 12,
      fontSize: 16,
      backgroundColor: theme.colors.card,
      color: theme.colors.text,
    },
    textArea: {
      minHeight: 140,
      textAlignVertical: 'top',
    },
    mapToggleButton: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      marginTop: 12,
      paddingVertical: 10,
    },
    mapToggleText: {
      color: theme.colors.accent,
      fontSize: 16,
      fontWeight: '600',
    },
    mapContainer: {
      marginTop: 12,
      borderRadius: 12,
      overflow: 'hidden',
      borderWidth: 1,
      borderColor: theme.colors.border,
      position: 'relative',
    },
    searchContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: theme.colors.card,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
      paddingHorizontal: 12,
      paddingVertical: 10,
      gap: 8,
    },
    searchIcon: {
      marginRight: 4,
    },
    searchInput: {
      flex: 1,
      fontSize: 15,
      color: theme.colors.text,
      paddingVertical: 4,
    },
    clearButton: {
      padding: 2,
    },
    errorContainer: {
      marginHorizontal: 16,
      marginTop: 8,
      backgroundColor: '#fee',
      borderLeftWidth: 3,
      borderLeftColor: '#f44',
      borderRadius: 8,
      padding: 10,
    },
    backendErrorContainer: {
      marginHorizontal: 16,
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
    searchResultsContainer: {
      backgroundColor: theme.colors.card,
      maxHeight: 180,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    searchResultItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      gap: 10,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border + '30',
    },
    searchResultTextContainer: {
      flex: 1,
    },
    searchResultText: {
      fontSize: 14,
      color: theme.colors.text,
      fontWeight: '600',
    },
    searchResultAddress: {
      fontSize: 13,
      color: theme.colors.muted,
      marginTop: 2,
    },
    distanceContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginTop: 4,
    },
    distanceText: {
      fontSize: 12,
      color: theme.colors.muted,
      marginLeft: 4,
      fontWeight: '600',
    },
    map: {
      width: '100%',
      height: 300,
    },
    zoomControls: {
      position: 'absolute',
      right: 10,
      bottom: 60,
      flexDirection: 'row',
      gap: 8,
    },
    zoomButton: {
      backgroundColor: theme.colors.card,
      width: 40,
      height: 40,
      borderRadius: 8,
      justifyContent: 'center',
      alignItems: 'center',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 4,
      elevation: 5,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    mapHint: {
      padding: 12,
      backgroundColor: theme.colors.card,
      color: theme.colors.muted,
      fontSize: 14,
      textAlign: 'center',
    },
    submitButton: {
      backgroundColor: theme.colors.accent,
      borderRadius: 999,
      paddingVertical: 14,
      alignItems: 'center',
      marginTop: 10,
    },
    submitButtonDisabled: {
      opacity: 0.6,
    },
    submitText: {
      color: '#fff',
      fontWeight: '700',
      fontSize: 16,
    },
  });

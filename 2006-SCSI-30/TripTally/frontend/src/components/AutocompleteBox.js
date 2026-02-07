import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  StyleSheet,
  Keyboard,
  Alert,
  Dimensions,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { BASE_URL } from '../config/keys';
import useThemedStyles from '../hooks/useThemedStyles';

const { height } = Dimensions.get('window');
const API_BASE = BASE_URL;

const newToken = () => Math.random().toString(36).slice(2) + Date.now().toString(36);

// Haversine formula to calculate distance between two coordinates (returns km)
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371; // Earth's radius in kilometers
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

// Format distance for display
const formatDistance = (distanceKm) => {
  if (distanceKm < 1) return `${Math.round(distanceKm * 1000)}m`;
  return `${distanceKm.toFixed(1)}km`;
};

export default function AutocompleteBox({
  placeholder,
  value,
  onChangeText,
  onPickLocation,
  userLocation,
  isDestination = false,
  showSeparator = false,
}) {
  const { styles, theme } = useThemedStyles(createStyles);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [isFocused, setIsFocused] = useState(false);
  const timer = useRef(null);
  const session = useRef(newToken());

  const query = (text) => {
    if (timer.current) clearTimeout(timer.current);
    onChangeText(text);
    if (!text || text.length < 2) {
      setResults([]);
      setLoading(false);
      return;
    }
    timer.current = setTimeout(async () => {
      try {
        setLoading(true);
        let list = [];

        // 1) Nearby Search (if we have user location) — ranked by distance
        if (userLocation) {
          try {
            const nearbyUrl = `${API_BASE}/maps/nearby?location=${userLocation.latitude},${userLocation.longitude}&radius=10000&keyword=${encodeURIComponent(
              text
            )}&rankby=distance`;
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
                    place_id: place.place_id,
                    distance,
                    latitude: place.lat,
                    longitude: place.lng,
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

        const baseQS = `input=${encodeURIComponent(text)}&sessiontoken=${encodeURIComponent(
          session.current
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

        setResults(list);
      } catch (e) {
        console.log('Autocomplete error:', e);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 260);
  };

  const resolvePick = async (item) => {
    // Clear results immediately and dismiss keyboard
    setResults([]);
    setIsFocused(false);
    Keyboard.dismiss();

    try {
      // Handle "Current Location" selection
      if (item.id === 'current-location') {
        if (userLocation) {
          session.current = newToken();
          onPickLocation({ 
            name: 'Current Location', 
            latitude: userLocation.latitude, 
            longitude: userLocation.longitude 
          });
        }
        return;
      }

      // If we already have coordinates from Nearby Search, use them directly
      if (item.latitude && item.longitude) {
        session.current = newToken();
        onPickLocation({ name: item.name, latitude: item.latitude, longitude: item.longitude });
        return;
      }

      // Otherwise, fetch place details
      const d1 = await fetch(
        `${API_BASE}/maps/place-details?place_id=${encodeURIComponent(item.place_id)}&fields=geometry`
      );
      let lat = null,
        lng = null;
      if (d1.ok) {
        const j = await d1.json();
        lat = j?.lat ?? j?.result?.geometry?.location?.lat ?? null;
        lng = j?.lng ?? j?.result?.geometry?.location?.lng ?? null;
      }
      if (lat == null || lng == null) {
        const d2 = await fetch(`${API_BASE}/maps/geocode?address=${encodeURIComponent(item.name)}`);
        const j2 = await d2.json();
        const first = Array.isArray(j2?.results) ? j2.results[0] : j2;
        lat = first?.lat ?? first?.geometry?.location?.lat;
        lng = first?.lng ?? first?.geometry?.location?.lng;
      }
      if (lat == null || lng == null) throw new Error('Unable to resolve location.');
      session.current = newToken();
      onPickLocation({ name: item.name, latitude: lat, longitude: lng });
    } catch (e) {
      Alert.alert('Search', e.message);
    }
  };

  return (
    <View style={{ width: '100%' }}>
      <View style={styles.inputWrap}>
        <View style={[styles.iconCircle, isDestination && styles.iconCircleDestination]}>
          <Ionicons name="location" size={20} color={isDestination ? '#EA4335' : '#4285F4'} />
        </View>
        <TextInput
          value={value}
          onChangeText={query}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.muted}
          style={[styles.input, { color: theme.colors.text }]}
          autoCapitalize="none"
          autoCorrect={false}
          returnKeyType="search"
          onFocus={() => setIsFocused(true)}
          onBlur={() => {
            // Delay clearing to allow tap on results
            setTimeout(() => {
              setIsFocused(false);
              setResults([]);
            }, 200);
          }}
        />
        {loading ? (
          <ActivityIndicator size="small" color={theme.colors.muted} />
        ) : isFocused && value ? (
          <TouchableOpacity
            onPress={() => onChangeText('')}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Ionicons name="close" size={20} color={theme.colors.muted} />
          </TouchableOpacity>
        ) : null}
      </View>
      {showSeparator && <View style={styles.separator} />}

      {isFocused && (results.length > 0 || (!value && userLocation)) && (
        <View style={styles.dropdown}>
          <FlatList
            keyboardShouldPersistTaps="handled"
            nestedScrollEnabled={true}
            showsVerticalScrollIndicator={true}
            data={!value && userLocation ? [{ id: 'current-location', name: 'Current Location', address: 'Use my current location', isCurrentLocation: true }] : results}
            keyExtractor={(it) => it.id}
            renderItem={({ item }) => (
              <TouchableOpacity style={styles.row} onPress={() => resolvePick(item)}>
                <Ionicons 
                  name={item.isCurrentLocation ? "navigate" : "location"} 
                  size={18} 
                  color={item.isCurrentLocation ? "#4285F4" : theme.colors.muted} 
                />
                <View style={{ flex: 1 }}>
                  <Text numberOfLines={1} style={[styles.resultName, item.isCurrentLocation && { color: '#4285F4' }]}>
                    {item.name}
                  </Text>
                  {item.address && (
                    <Text numberOfLines={1} style={styles.resultAddress}>
                      {item.distance !== null && item.distance !== undefined
                        ? `${formatDistance(item.distance)} · ${item.address}`
                        : item.address}
                    </Text>
                  )}
                  {!item.address && item.distance !== null && item.distance !== undefined && (
                    <Text numberOfLines={1} style={styles.resultAddress}>
                      {formatDistance(item.distance)}
                    </Text>
                  )}
                </View>
              </TouchableOpacity>
            )}
          />
        </View>
      )}
    </View>
  );
}

const createStyles = ({ colors }) => ({
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 6,
    minHeight: 50,
  },
  separator: {
    height: 1,
    backgroundColor: colors.border,
    marginLeft: 60,
    marginRight: 14,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#E8F0FE',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  iconCircleDestination: {
    backgroundColor: '#FCE8E6',
  },
  input: {
    flex: 1,
    paddingVertical: 6,
    fontSize: 15,
    fontWeight: '400',
    letterSpacing: 0.2,
  },
  dropdown: {
    marginTop: 6,
    maxHeight: height * 0.28,
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: StyleSheet.hairlineWidth,
    backgroundColor: colors.card,
    borderColor: colors.border,
  },
  row: {
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  resultName: {
    fontSize: 15,
    fontWeight: '500',
    color: colors.text,
    letterSpacing: 0.1,
  },
  resultAddress: {
    fontSize: 13,
    color: colors.muted,
    marginTop: 2,
  },
});

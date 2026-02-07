
import React,{useState, useRef, useEffect} from 'react';
import { View, Text, TextInput, TouchableOpacity, SafeAreaView, Alert, ScrollView, ActivityIndicator } from 'react-native';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from 'react-native-maps';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import Card from '../components/Card';
import HeaderBackButton from '../components/HeaderBackButton';
import useThemedStyles from '../hooks/useThemedStyles';
import { apiPost } from '../services/api';
import { useAuth } from '../context/AuthContext';

// Mock GPS data for testing (simulates a ~2km walking route around NTU campus)
// This represents a 20-minute walk with GPS points recorded every 30 seconds
const MOCK_ROUTE_DATA = [
  // Starting near North Spine Plaza
  { latitude: 1.3483, longitude: 103.6831, timestamp: Date.now() - 1200000 },
  { latitude: 1.3485, longitude: 103.6833, timestamp: Date.now() - 1170000 },
  { latitude: 1.3487, longitude: 103.6836, timestamp: Date.now() - 1140000 },
  { latitude: 1.3490, longitude: 103.6839, timestamp: Date.now() - 1110000 },
  
  // Walking towards Hive
  { latitude: 1.3493, longitude: 103.6842, timestamp: Date.now() - 1080000 },
  { latitude: 1.3496, longitude: 103.6845, timestamp: Date.now() - 1050000 },
  { latitude: 1.3499, longitude: 103.6848, timestamp: Date.now() - 1020000 },
  { latitude: 1.3502, longitude: 103.6851, timestamp: Date.now() - 990000 },
  
  // Around the Learning Hub area
  { latitude: 1.3505, longitude: 103.6854, timestamp: Date.now() - 960000 },
  { latitude: 1.3508, longitude: 103.6857, timestamp: Date.now() - 930000 },
  { latitude: 1.3511, longitude: 103.6860, timestamp: Date.now() - 900000 },
  { latitude: 1.3513, longitude: 103.6863, timestamp: Date.now() - 870000 },
  
  // Heading towards School of Art, Design and Media
  { latitude: 1.3515, longitude: 103.6866, timestamp: Date.now() - 840000 },
  { latitude: 1.3517, longitude: 103.6869, timestamp: Date.now() - 810000 },
  { latitude: 1.3519, longitude: 103.6872, timestamp: Date.now() - 780000 },
  { latitude: 1.3521, longitude: 103.6875, timestamp: Date.now() - 750000 },
  
  // Walking along the main road
  { latitude: 1.3523, longitude: 103.6878, timestamp: Date.now() - 720000 },
  { latitude: 1.3525, longitude: 103.6881, timestamp: Date.now() - 690000 },
  { latitude: 1.3527, longitude: 103.6884, timestamp: Date.now() - 660000 },
  { latitude: 1.3529, longitude: 103.6887, timestamp: Date.now() - 630000 },
  
  // Near Sports and Recreation Centre
  { latitude: 1.3531, longitude: 103.6890, timestamp: Date.now() - 600000 },
  { latitude: 1.3533, longitude: 103.6893, timestamp: Date.now() - 570000 },
  { latitude: 1.3535, longitude: 103.6896, timestamp: Date.now() - 540000 },
  { latitude: 1.3536, longitude: 103.6899, timestamp: Date.now() - 510000 },
  
  // Turning back towards campus
  { latitude: 1.3537, longitude: 103.6902, timestamp: Date.now() - 480000 },
  { latitude: 1.3538, longitude: 103.6905, timestamp: Date.now() - 450000 },
  { latitude: 1.3539, longitude: 103.6908, timestamp: Date.now() - 420000 },
  { latitude: 1.3540, longitude: 103.6911, timestamp: Date.now() - 390000 },
  
  // Walking through the central area
  { latitude: 1.3538, longitude: 103.6914, timestamp: Date.now() - 360000 },
  { latitude: 1.3536, longitude: 103.6917, timestamp: Date.now() - 330000 },
  { latitude: 1.3534, longitude: 103.6920, timestamp: Date.now() - 300000 },
  { latitude: 1.3532, longitude: 103.6923, timestamp: Date.now() - 270000 },
  
  // Heading towards Nanyang Auditorium area
  { latitude: 1.3530, longitude: 103.6926, timestamp: Date.now() - 240000 },
  { latitude: 1.3528, longitude: 103.6929, timestamp: Date.now() - 210000 },
  { latitude: 1.3526, longitude: 103.6932, timestamp: Date.now() - 180000 },
  { latitude: 1.3524, longitude: 103.6935, timestamp: Date.now() - 150000 },
  
  // Walking back towards North Spine
  { latitude: 1.3522, longitude: 103.6933, timestamp: Date.now() - 120000 },
  { latitude: 1.3520, longitude: 103.6930, timestamp: Date.now() - 90000 },
  { latitude: 1.3518, longitude: 103.6927, timestamp: Date.now() - 60000 },
  { latitude: 1.3516, longitude: 103.6924, timestamp: Date.now() - 30000 },
  
  // Final stretch back to starting area
  { latitude: 1.3514, longitude: 103.6921, timestamp: Date.now() }
];


export default function CreateRoute({ navigation }){
  const { user } = useAuth();
  const [name,setName]=useState('');
  const [desc,setDesc]=useState('');
  const [selectedTag, setSelectedTag] = useState(null); // Track single selected tag
  const [mapMode, setMapMode] = useState('draw'); // 'draw' or 'track'
  const [routePath, setRoutePath] = useState([]); // Store route coordinates
  const [uploading, setUploading] = useState(false);
  const [isTracking, setIsTracking] = useState(false);
  const [trackedHistory, setTrackedHistory] = useState([]); // Full GPS history
  const [startIndex, setStartIndex] = useState(null); // Selected start point
  const [endIndex, setEndIndex] = useState(null); // Selected end point
  const [userLocation, setUserLocation] = useState(null); // Current user location
  const locationSubscription = useRef(null);
  const mapRef = useRef(null);
  const [region, setRegion] = useState({
    latitude: 1.3483,
    longitude: 103.6831,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  });
  
  // Get user location on mount
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
  const { styles, theme } = useThemedStyles(({ colors }) => ({
    root: {
      flex:1,
      backgroundColor: colors.background,
      padding:16,
    },
    scrollContent: {
      paddingBottom: 24,
    },
    title: {
      fontWeight:'800',
      fontSize:18,
      marginBottom:12,
      marginHorizontal: 18,
      color: colors.text,
    },
    mapContainer: {
      marginHorizontal: 18,
      height: 350,
      borderRadius: 16,
      overflow: 'hidden',
      marginBottom: 16,
      borderWidth: 2,
      borderColor: colors.accent,
      position: 'relative',
    },
    map: {
      flex: 1,
    },
    mapModeButtons: {
      position: 'absolute',
      top: 10,
      left: 10,
      right: 10,
      flexDirection: 'row',
      gap: 8,
    },
    mapModeButton: {
      flex: 1,
      backgroundColor: colors.card,
      paddingVertical: 8,
      paddingHorizontal: 12,
      borderRadius: 8,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 6,
      borderWidth: 1,
      borderColor: colors.border,
    },
    mapModeButtonActive: {
      backgroundColor: colors.accent,
      borderColor: colors.accent,
    },
    mapModeButtonText: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.text,
    },
    mapModeButtonTextActive: {
      color: '#fff',
    },
    mapZoomButtons: {
      position: 'absolute',
      right: 10,
      bottom: 10,
      flexDirection: 'row',
      gap: 8,
    },
    mapZoomButton: {
      backgroundColor: colors.card,
      width: 36,
      height: 36,
      borderRadius: 18,
      justifyContent: 'center',
      alignItems: 'center',
      borderWidth: 1,
      borderColor: colors.border,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 3.84,
      elevation: 5,
    },
    mapZoomButtonText: {
      fontSize: 20,
      fontWeight: '700',
      color: colors.text,
    },
    mapInfo: {
      marginHorizontal: 18,
      marginBottom: 12,
      fontSize: 13,
      color: colors.muted,
      fontStyle: 'italic',
    },
    label: {
      marginBottom:6,
      color: colors.muted,
      fontWeight:'600',
    },
    tagRow: {
      flexDirection:'row',
      gap:8,
      marginBottom:8,
    },
    tag: {
      backgroundColor: colors.pill,
      paddingVertical:6,
      paddingHorizontal:10,
      borderRadius:14,
      fontWeight:'600',
      borderWidth: 1,
      borderColor: colors.border,
    },
    tagSelected: {
      backgroundColor: colors.accent,
      borderColor: colors.accent,
    },
    tagText: {
      color: colors.text,
      fontWeight:'600',
    },
    tagTextSelected: {
      color: '#fff',
    },
    input: {
      backgroundColor: colors.card,
      padding:10,
      borderRadius:8,
      marginBottom:8,
      borderWidth:1,
      borderColor: colors.border,
      color: colors.text,
    },
    textArea: {
      height:100,
      textAlignVertical:'top',
    },
    submitBtn: {
      backgroundColor: colors.accent,
      padding:12,
      borderRadius:10,
      alignItems:'center',
      marginTop:10,
    },
    submitText: {
      color:'#fff',
      fontWeight:'700',
    },
    trackButton: {
      flex: 1,
      backgroundColor: colors.accent,
      padding: 12,
      borderRadius: 10,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 6,
    },
    trackButtonText: {
      color: '#fff',
      fontWeight: '600',
      fontSize: 14,
    },
    mockButton: {
      flex: 1,
      backgroundColor: colors.card,
      padding: 12,
      borderRadius: 10,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 6,
      borderWidth: 1,
      borderColor: colors.border,
    },
    mockButtonText: {
      fontWeight: '600',
      fontSize: 14,
    },
  }));

  const toggleTag = (tag) => {
    setSelectedTag(selectedTag === tag ? null : tag);
  };

  // Calculate distance between two coordinates using Haversine formula
  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  // Calculate total distance of route in meters
  const calculateTotalDistance = () => {
    if (routePath.length < 2) return 0;
    
    let totalDistance = 0;
    for (let i = 0; i < routePath.length - 1; i++) {
      const distance = calculateDistance(
        routePath[i].latitude,
        routePath[i].longitude,
        routePath[i + 1].latitude,
        routePath[i + 1].longitude
      );
      totalDistance += distance;
    }
    return totalDistance * 1000; // Convert km to meters
  };

  // Estimate duration based on transport mode and distance in seconds
  const estimateDuration = (distanceMeters, mode) => {
    // Average speeds: Walking ~5 km/h, Cycling ~15 km/h
    const speed = mode === 'walking' ? 5 : 15;
    const distanceKm = distanceMeters / 1000;
    const hours = distanceKm / speed;
    return Math.round(hours * 3600); // Return duration in seconds
  };

  // Convert UI transport mode to backend format
  const getTransportModeForBackend = (tag) => {
    return tag === 'Cycling' ? 'bicycling' : 'walking';
  };

  const handleUpload = async () => {
    // Validate all fields
    if (!selectedTag) {
      Alert.alert(
        "Tag Required",
        "Please select a tag (Walking or Cycling) for your route.",
        [{ text: "OK" }]
      );
      return;
    }

    if (routePath.length === 0) {
      Alert.alert(
        "Route Required",
        "Please draw or track a route on the map.",
        [{ text: "OK" }]
      );
      return;
    }

    if (!name.trim()) {
      Alert.alert(
        "Route Name Required",
        "Please enter a name for your route.",
        [{ text: "OK" }]
      );
      return;
    }

    if (!desc.trim()) {
      Alert.alert(
        "Description Required",
        "Please provide a description for your route.",
        [{ text: "OK" }]
      );
      return;
    }

    // Calculate route metrics
    const totalDistance = calculateTotalDistance(); // in meters
    const transportMode = getTransportModeForBackend(selectedTag);
    const durationSeconds = estimateDuration(totalDistance, transportMode);

    // Format route points for backend
    const routePoints = routePath.map((point, index) => ({
      latitude: point.latitude,
      longitude: point.longitude,
      order: index
    }));

    // Prepare route data
    const routeData = {
      user_id: user?.id,
      title: name.trim(),
      description: desc.trim(),
      transport_mode: transportMode, // "walking" or "bicycling"
      distance: Math.round(totalDistance), // in meters
      duration: durationSeconds, // in seconds
      route_points: routePoints,
      is_public: true,
      created_by: user?.username || user?.display_name || 'Anonymous'
    };

    try {
      setUploading(true);
      await apiPost('/user-routes', routeData);
      
      // Convert to km and minutes for display
      const distanceKm = totalDistance / 1000;
      const durationMin = Math.round(durationSeconds / 60);
      
      Alert.alert(
        "Success",
        `Route created successfully!\nDistance: ${distanceKm.toFixed(2)} km\nEstimated Duration: ${durationMin} min`,
        [
          {
            text: "OK",
            onPress: () => navigation.navigate('UserSuggestedRoutePage')
          }
        ]
      );
    } catch (error) {
      console.error('Error creating route:', error);
      Alert.alert(
        "Error",
        "Failed to create route. Please try again.",
        [{ text: "OK" }]
      );
    } finally {
      setUploading(false);
    }
  };

  const handleMapPress = (event) => {
    if (mapMode === 'draw') {
      const { coordinate } = event.nativeEvent;
      setRoutePath([...routePath, coordinate]);
    } else if (mapMode === 'track' && trackedHistory.length > 0) {
      // Select start/end points from tracked history
      const { coordinate } = event.nativeEvent;
      
      // Find closest point on the polyline (not just closest GPS point)
      let closestIndex = 0;
      let minDistance = Number.MAX_VALUE;
      
      // Check distance to each point AND to line segments between points
      trackedHistory.forEach((point, index) => {
        // Distance to point itself
        const pointDistance = calculateDistance(
          coordinate.latitude,
          coordinate.longitude,
          point.latitude,
          point.longitude
        );
        
        if (pointDistance < minDistance) {
          minDistance = pointDistance;
          closestIndex = index;
        }
        
        // Also check distance to line segment (if not the last point)
        if (index < trackedHistory.length - 1) {
          const nextPoint = trackedHistory[index + 1];
          const segmentDistance = distanceToLineSegment(
            coordinate,
            point,
            nextPoint
          );
          
          // If closer to this segment, use the start point of the segment
          if (segmentDistance < minDistance) {
            minDistance = segmentDistance;
            closestIndex = index;
          }
        }
      });

      // Set start point first, then end point
      if (startIndex === null) {
        setStartIndex(closestIndex);
        Alert.alert('Start Point Set', 'Now tap on the map to select the end point of your route.');
      } else if (endIndex === null) {
        if (closestIndex === startIndex) {
          Alert.alert('Invalid Selection', 'End point must be different from start point.');
          return;
        }
        setEndIndex(closestIndex);
        
        // Extract route segment
        const start = Math.min(startIndex, closestIndex);
        const end = Math.max(startIndex, closestIndex);
        const segment = trackedHistory.slice(start, end + 1);
        setRoutePath(segment);
        
        Alert.alert('Route Selected', `Route segment with ${segment.length} points created!`);
      } else {
        // Reset and start over
        Alert.alert('Reset Selection', 'Tap on the map to select a new start point.');
        setStartIndex(null);
        setEndIndex(null);
        setRoutePath([]);
      }
    }
  };

  // Helper function to calculate distance from point to line segment
  const distanceToLineSegment = (point, lineStart, lineEnd) => {
    const A = point.latitude - lineStart.latitude;
    const B = point.longitude - lineStart.longitude;
    const C = lineEnd.latitude - lineStart.latitude;
    const D = lineEnd.longitude - lineStart.longitude;

    const dot = A * C + B * D;
    const lenSq = C * C + D * D;
    let param = -1;

    if (lenSq !== 0) param = dot / lenSq;

    let xx, yy;

    if (param < 0) {
      xx = lineStart.latitude;
      yy = lineStart.longitude;
    } else if (param > 1) {
      xx = lineEnd.latitude;
      yy = lineEnd.longitude;
    } else {
      xx = lineStart.latitude + param * C;
      yy = lineStart.longitude + param * D;
    }

    return calculateDistance(point.latitude, point.longitude, xx, yy);
  };

  const clearRoute = () => {
    setRoutePath([]);
    setStartIndex(null);
    setEndIndex(null);
  };

  // Handle marker drag to reposition start/end points
  const handleMarkerDrag = (markerType, coordinate) => {
    // Find closest point in history to the new position
    let closestIndex = 0;
    let minDistance = Number.MAX_VALUE;
    
    trackedHistory.forEach((point, index) => {
      const distance = Math.sqrt(
        Math.pow(point.latitude - coordinate.latitude, 2) +
        Math.pow(point.longitude - coordinate.longitude, 2)
      );
      if (distance < minDistance) {
        minDistance = distance;
        closestIndex = index;
      }
    });

    // Update the appropriate marker
    if (markerType === 'start') {
      if (closestIndex === endIndex) {
        Alert.alert('Invalid Position', 'Start point cannot be the same as end point.');
        return;
      }
      setStartIndex(closestIndex);
    } else if (markerType === 'end') {
      if (closestIndex === startIndex) {
        Alert.alert('Invalid Position', 'End point cannot be the same as start point.');
        return;
      }
      setEndIndex(closestIndex);
    }

    // Update route segment if both points are selected
    if (startIndex !== null && endIndex !== null) {
      const newStartIndex = markerType === 'start' ? closestIndex : startIndex;
      const newEndIndex = markerType === 'end' ? closestIndex : endIndex;
      const start = Math.min(newStartIndex, newEndIndex);
      const end = Math.max(newStartIndex, newEndIndex);
      const segment = trackedHistory.slice(start, end + 1);
      setRoutePath(segment);
    }
  };

  // Load mock data for testing
  const loadMockData = () => {
    setTrackedHistory(MOCK_ROUTE_DATA);
    Alert.alert(
      'Mock Data Loaded',
      `Loaded ${MOCK_ROUTE_DATA.length} GPS points. Switch to Track mode and tap on the polyline to select start and end points.`
    );
  };

  // Start/Stop GPS tracking
  const toggleTracking = async () => {
    if (isTracking) {
      // Stop tracking
      if (locationSubscription.current) {
        locationSubscription.current.remove();
        locationSubscription.current = null;
      }
      setIsTracking(false);
      Alert.alert('Tracking Stopped', `Recorded ${trackedHistory.length} GPS points.`);
    } else {
      // Start tracking
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Permission Denied', 'Location permission is required for tracking.');
          return;
        }

        setIsTracking(true);
        setTrackedHistory([]);
        setStartIndex(null);
        setEndIndex(null);
        setRoutePath([]);

        locationSubscription.current = await Location.watchPositionAsync(
          {
            accuracy: Location.Accuracy.High,
            timeInterval: 5000, // Update every 5 seconds
            distanceInterval: 10, // Update every 10 meters
          },
          (location) => {
            const newPoint = {
              latitude: location.coords.latitude,
              longitude: location.coords.longitude,
              timestamp: location.timestamp,
            };
            setTrackedHistory((prev) => [...prev, newPoint]);
            
            // Center map on current location
            if (mapRef.current) {
              mapRef.current.animateToRegion({
                latitude: newPoint.latitude,
                longitude: newPoint.longitude,
                latitudeDelta: 0.01,
                longitudeDelta: 0.01,
              }, 500);
            }
          }
        );

        Alert.alert('Tracking Started', 'Your route is being recorded. Move around and then stop tracking.');
      } catch (error) {
        console.error('Error starting tracking:', error);
        Alert.alert('Error', 'Failed to start GPS tracking.');
      }
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (locationSubscription.current) {
        locationSubscription.current.remove();
      }
    };
  }, []);

  // Region change handler and zoom functions
  const handleRegionChangeComplete = (newRegion) => {
    setRegion(newRegion);
  };

  const zoomIn = () => {
    const newRegion = {
      ...region,
      latitudeDelta: region.latitudeDelta / 2,
      longitudeDelta: region.longitudeDelta / 2,
    };
    setRegion(newRegion);
    if (mapRef.current && mapRef.current.animateToRegion) {
      mapRef.current.animateToRegion(newRegion, 300);
    }
  };

  const zoomOut = () => {
    const newRegion = {
      ...region,
      latitudeDelta: region.latitudeDelta * 2,
      longitudeDelta: region.longitudeDelta * 2,
    };
    setRegion(newRegion);
    if (mapRef.current && mapRef.current.animateToRegion) {
      mapRef.current.animateToRegion(newRegion, 300);
    }
  };

  return (
    <SafeAreaView style={styles.root}>
      <HeaderBackButton onPress={() => navigation?.goBack()} />
      <ScrollView style={{ flex: 1 }} contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>Create New Custom Route</Text>

        {/* Map Container */}
        <View style={styles.mapContainer}>
          <MapView
            provider={PROVIDER_GOOGLE}
            ref={mapRef}
            style={styles.map}
            region={region}
            onRegionChangeComplete={handleRegionChangeComplete}
            onPress={handleMapPress}
            showsUserLocation
            showsMyLocationButton={false}
          >
            {/* Show tracked history in gray */}
            {mapMode === 'track' && trackedHistory.length > 0 && (
              <>
                <Polyline
                  coordinates={trackedHistory}
                  strokeColor="#999"
                  strokeWidth={3}
                />
                {/* Show start/end markers if selected - DRAGGABLE */}
                {startIndex !== null && (
                  <Marker
                    coordinate={trackedHistory[startIndex]}
                    pinColor="blue"
                    title="Start Point"
                    description="Drag to adjust start position"
                    draggable
                    onDragEnd={(e) => handleMarkerDrag('start', e.nativeEvent.coordinate)}
                  />
                )}
                {endIndex !== null && (
                  <Marker
                    coordinate={trackedHistory[endIndex]}
                    pinColor="purple"
                    title="End Point"
                    description="Drag to adjust end position"
                    draggable
                    onDragEnd={(e) => handleMarkerDrag('end', e.nativeEvent.coordinate)}
                  />
                )}
              </>
            )}

            {/* Show selected route segment */}
            {routePath.length > 0 && (
              <>
                <Polyline
                  coordinates={routePath}
                  strokeColor={theme.colors.accent}
                  strokeWidth={4}
                />
                {/* Start pin marker */}
                <Marker
                  coordinate={routePath[0]}
                  pinColor="#22C55E"
                  title="Route Start"
                  description="Starting point of your route"
                />
                {/* End pin marker */}
                <Marker
                  coordinate={routePath[routePath.length - 1]}
                  pinColor="#EF4444"
                  title="Route End"
                  description="Ending point of your route"
                />
              </>
            )}
          </MapView>

          {/* Zoom Controls */}
          <View style={styles.mapZoomButtons} pointerEvents="box-none">
            <TouchableOpacity style={styles.mapZoomButton} onPress={zoomIn} activeOpacity={0.7}>
              <Text style={styles.mapZoomButtonText}>+</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.mapZoomButton} onPress={zoomOut} activeOpacity={0.7}>
              <Text style={styles.mapZoomButtonText}>−</Text>
            </TouchableOpacity>
          </View>

          {/* Map Mode Buttons */}
          <View style={styles.mapModeButtons}>
            <TouchableOpacity
              style={[
                styles.mapModeButton,
                mapMode === 'draw' && styles.mapModeButtonActive
              ]}
              onPress={() => setMapMode('draw')}
              activeOpacity={0.7}
            >
              <Ionicons 
                name="create-outline" 
                size={16} 
                color={mapMode === 'draw' ? '#fff' : theme.colors.text} 
              />
              <Text style={[
                styles.mapModeButtonText,
                mapMode === 'draw' && styles.mapModeButtonTextActive
              ]}>
                Draw Route
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.mapModeButton,
                mapMode === 'track' && styles.mapModeButtonActive
              ]}
              onPress={() => setMapMode('track')}
              activeOpacity={0.7}
            >
              <Ionicons 
                name="navigate-outline" 
                size={16} 
                color={mapMode === 'track' ? '#fff' : theme.colors.text} 
              />
              <Text style={[
                styles.mapModeButtonText,
                mapMode === 'track' && styles.mapModeButtonTextActive
              ]}>
                Track Route
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        <Text style={styles.mapInfo}>
          {mapMode === 'draw' 
            ? `Tap on the map to draw your route. Points: ${routePath.length}`
            : trackedHistory.length > 0
              ? `Tracked history: ${trackedHistory.length} points. ${startIndex === null ? 'Tap to select start point' : endIndex === null ? 'Tap to select end point' : 'Route selected!'}`
              : 'Start tracking or load mock data to see GPS history'}
        </Text>

        {/* Track Mode Controls */}
        {mapMode === 'track' && (
          <View style={{ flexDirection: 'row', gap: 8, marginHorizontal: 18, marginBottom: 12 }}>
            <TouchableOpacity 
              onPress={toggleTracking}
              style={[styles.trackButton, isTracking && { backgroundColor: '#ff4444' }]}
            >
              <Ionicons name={isTracking ? "stop" : "play"} size={16} color="#fff" />
              <Text style={styles.trackButtonText}>
                {isTracking ? 'Stop Tracking' : 'Start Tracking'}
              </Text>
            </TouchableOpacity>
            
            {!isTracking && (
              <TouchableOpacity 
                onPress={loadMockData}
                style={styles.mockButton}
              >
                <Ionicons name="analytics" size={16} color={theme.colors.text} />
                <Text style={[styles.mockButtonText, { color: theme.colors.text }]}>
                  Load Mock Data
                </Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {routePath.length > 0 && (
          <TouchableOpacity 
            onPress={clearRoute}
            style={{ alignSelf: 'center', marginBottom: 12 }}
          >
            <Text style={{ color: theme.colors.accent, fontWeight: '600' }}>
              Clear Route
            </Text>
          </TouchableOpacity>
        )}

        <Card style={{ marginHorizontal: 18 }}>
        <Text style={styles.label}>Mode of Transport</Text>
        <View style={styles.tagRow}>
          {['Walking','Cycling'].map(tag => {
            const isSelected = selectedTag === tag;
            return (
              <TouchableOpacity
                key={tag}
                style={[styles.tag, isSelected && styles.tagSelected]}
                onPress={() => toggleTag(tag)}
                activeOpacity={0.7}
              >
                <Text style={[styles.tagText, isSelected && styles.tagTextSelected]}>
                  {tag}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
        <TextInput placeholder="Route Name" placeholderTextColor={theme.colors.muted} value={name} onChangeText={setName} style={styles.input} />
        <TextInput placeholder="Route Description" placeholderTextColor={theme.colors.muted} value={desc} onChangeText={setDesc} style={[styles.input, styles.textArea]} multiline />
        <TouchableOpacity 
          style={[styles.submitBtn, uploading && { opacity: 0.6 }]} 
          onPress={handleUpload}
          disabled={uploading}
        >
          {uploading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.submitText}>Upload</Text>
          )}
        </TouchableOpacity>
      </Card>
      </ScrollView>
    </SafeAreaView>
  );
}

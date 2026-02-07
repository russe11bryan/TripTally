// src/screens/HomePage.js
import React, { useEffect, useState, useRef } from "react";
import { View, Text, TouchableOpacity, Dimensions, Modal, Alert, ActivityIndicator, Animated } from "react-native";
import MapView, { PROVIDER_GOOGLE, Marker, Polyline } from "react-native-maps";
import * as Location from "expo-location";
import Ionicons from "@expo/vector-icons/Ionicons";
import polyline from "@mapbox/polyline";
import { useRoute, useFocusEffect, useIsFocused } from "@react-navigation/native";
import useThemedStyles from "../hooks/useThemedStyles";
import { BASE_URL } from "../config/keys";
import { apiGet, apiDelete } from "../services/api";
import { useAuth } from "../context/AuthContext";

const { height } = Dimensions.get("window");
const API_BASE = BASE_URL;

const isValidLatLng = (lat, lng) =>
  Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;

const SG_DEFAULT = { latitude: 1.3521, longitude: 103.8198, latitudeDelta: 0.02, longitudeDelta: 0.02 };
const safeIcon = (name) => (Ionicons.glyphMap?.[name] ? name : "alert-circle-outline");

export default function HomePage({ navigation }) {
  const route = useRoute();
  const isFocused = useIsFocused();
  const { user } = useAuth();
  const mapRef = useRef(null);

  // Traffic alert state
  const [trafficAlerts, setTrafficAlerts] = useState([]);
  const [tomtomIncidents, setTomtomIncidents] = useState([]);
  const [mapRegion, setMapRegion] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [userLocations, setUserLocations] = useState({ home: null, work: null });

  // Maps state
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [routeCoords, setRouteCoords] = useState([]);
  const [distance, setDistance] = useState(null);
  const [duration, setDuration] = useState(null);
  const [loadingRoute, setLoadingRoute] = useState(false);
  const [mapReady, setMapReady] = useState(false);

  // throttling / fit + last good center
  const pendingFitRef = useRef(null);
  const lastFetchRef = useRef(0);
  const inFlightRef = useRef(false);
  const lastGoodCenterRef = useRef({ latitude: SG_DEFAULT.latitude, longitude: SG_DEFAULT.longitude });
  const regionChangeTimerRef = useRef(null);
  const lastFetchedRegionRef = useRef(null);
  
  // Animation for markers - keep track of marker animations
  const markerAnimations = useRef({});

  const { styles, theme } = useThemedStyles(({ colors }) => ({
    root: { flex: 1 },
    locationBtn: {
      position: "absolute",
      top: 60,
      left: 16,
      backgroundColor: colors.card,
      borderRadius: 12,
      width: 48,
      height: 48,
      justifyContent: "center",
      alignItems: "center",
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 4,
      elevation: 5,
      borderWidth: 1,
      borderColor: colors.border,
    },
    warningBtn: {
      position: "absolute",
      right: 28,
      backgroundColor: colors.card,
      borderRadius: 28,
      width: 56,
      height: 56,
      justifyContent: "center",
      alignItems: "center",
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 4,
      elevation: 5,
      borderWidth: 2,
      borderColor: "#ffe600ff",
    },
    bottomSheet: {
      position: "absolute",
      bottom: 10,
      left: 12,
      right: 12,
      backgroundColor: colors.card,
      padding: 12,
      borderRadius: 18,
      borderWidth: 0.5,
      borderColor: colors.border,
    },
    search: { backgroundColor: colors.pillAlt, padding: 14, borderRadius: 12 },
    searchText: { color: colors.muted, fontWeight: "600" },
    quickRow: { flexDirection: "row", gap: 10, marginTop: 10 },
    quickBtn: {
      flexDirection: "row",
      gap: 6,
      backgroundColor: colors.pill,
      paddingVertical: 8,
      paddingHorizontal: 12,
      borderRadius: 10,
      alignItems: "center",
    },
    quickTxt: { fontWeight: "600", color: colors.text },
    markerContainer: {
      width: 40,
      height: 40,
      borderRadius: 20,
      justifyContent: "center",
      alignItems: "center",
      borderWidth: 3,
      borderColor: "#FFD700",
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.3,
      shadowRadius: 4,
      elevation: 5,
    },
    modalContainer: {
      flex: 1,
      backgroundColor: "rgba(0, 0, 0, 0.5)",
      justifyContent: "center",
      alignItems: "center",
    },
    modalContent: {
      backgroundColor: colors.card,
      borderRadius: 20,
      padding: 24,
      width: "85%",
      maxWidth: 400,
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 8,
      elevation: 10,
    },
    modalHeader: { flexDirection: "row", alignItems: "center", marginBottom: 16 },
    modalIconContainer: { width: 50, height: 50, borderRadius: 25, justifyContent: "center", alignItems: "center", marginRight: 12 },
    modalTitle: { fontSize: 20, fontWeight: "700", color: colors.text, flex: 1 },
    modalInfo: { marginBottom: 20 },
    modalLabel: { fontSize: 14, color: colors.muted, marginBottom: 4, fontWeight: "600" },
    modalValue: { fontSize: 16, color: colors.text, marginBottom: 12 },
    modalButtons: { flexDirection: "row", gap: 12 },
    modalButton: { flex: 1, padding: 14, borderRadius: 12, alignItems: "center" },
    resolveButton: { backgroundColor: "#10B981" },
    cancelButton: { backgroundColor: colors.muted },
    buttonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  }));

  const safeAnimateToCenter = (center, duration = 500) => {
    if (!center) return;
    const { latitude, longitude } = center;
    if (!isValidLatLng(latitude, longitude)) return;
    lastGoodCenterRef.current = { latitude, longitude };
    mapRef.current?.animateToRegion(
      { latitude, longitude, latitudeDelta: 0.02, longitudeDelta: 0.02 },
      duration
    );
  };

  // ----- API: Traffic alerts -----
  const fetchTrafficAlerts = async () => {
    try {
      const data = await apiGet("/traffic-alerts?status=active");
      setTrafficAlerts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error fetching traffic alerts:", error);
    }
  };

  const fetchTomTomIncidents = async (region) => {
    if (!region) return;
    
    // Check if region has significantly changed (more than 30% of the view)
    if (lastFetchedRegionRef.current) {
      const last = lastFetchedRegionRef.current;
      const latDiff = Math.abs(region.latitude - last.latitude);
      const lngDiff = Math.abs(region.longitude - last.longitude);
      const latThreshold = last.latitudeDelta * 0.3;
      const lngThreshold = last.longitudeDelta * 0.3;
      
      // If we haven't moved much, don't refetch
      if (latDiff < latThreshold && lngDiff < lngThreshold) {
        return;
      }
    }
    
    try {
      // Calculate bounding box from current map region
      const { latitude, longitude, latitudeDelta, longitudeDelta } = region;
      const west = longitude - longitudeDelta / 2;
      const south = latitude - latitudeDelta / 2;
      const east = longitude + longitudeDelta / 2;
      const north = latitude + latitudeDelta / 2;
      const bbox = `${west.toFixed(4)},${south.toFixed(4)},${east.toFixed(4)},${north.toFixed(4)}`;
      
      // Store the fetched region
      lastFetchedRegionRef.current = region;
      
      const url = `${API_BASE}/maps/traffic-incidents?bbox=${encodeURIComponent(bbox)}&time_validity=present`;
      console.log('Fetching TomTom incidents for visible region:', bbox);
      
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        const incidents = Array.isArray(data?.incidents) ? data.incidents : [];
        console.log('TomTom incidents in view:', incidents.length);
        setTomtomIncidents(incidents);
      } else {
        console.log('TomTom incidents fetch failed:', res.status);
        setTomtomIncidents([]);
      }
    } catch (error) {
      console.error("Error fetching TomTom incidents:", error);
      setTomtomIncidents([]);
    }
  };

  const fetchUserLocations = async () => {
    if (!user?.id) return;
    try {
      const userData = await apiGet(`/users/${user.id}`);
      setUserLocations({
        home:
          userData.home_latitude && userData.home_longitude
            ? {
                latitude: Number(userData.home_latitude),
                longitude: Number(userData.home_longitude),
                address: userData.home_address,
              }
            : null,
        work:
          userData.work_latitude && userData.work_longitude
            ? {
                latitude: Number(userData.work_latitude),
                longitude: Number(userData.work_longitude),
                address: userData.work_address,
              }
            : null,
      });
    } catch (error) {
      console.error("Error fetching user locations:", error);
    }
  };

  const handleHomePress = () => {
    if (userLocations.home) {
      navigation.navigate("Directions", {
        destination: {
          name: "Home",
          latitude: userLocations.home.latitude,
          longitude: userLocations.home.longitude,
        },
      });
    } else {
      Alert.alert("Home Location Not Set", "Set your home location?", [
        { text: "Cancel", style: "cancel" },
        { text: "Set Location", onPress: () => navigation.navigate("SetLocation", { locationType: "home" }) },
      ]);
    }
  };

  const handleWorkPress = () => {
    if (userLocations.work) {
      navigation.navigate("Directions", {
        destination: {
          name: "Work",
          latitude: userLocations.work.latitude,
          longitude: userLocations.work.longitude,
        },
      });
    } else {
      Alert.alert("Work Location Not Set", "Set your work location?", [
        { text: "Cancel", style: "cancel" },
        { text: "Set Location", onPress: () => navigation.navigate("SetLocation", { locationType: "work" }) },
      ]);
    }
  };

  const handleRecenterMap = () => {
    if (origin) safeAnimateToCenter(origin, 800);
  };

  const getIncidentIcon = (t) =>
    t === "Traffic" ? "car-outline" : t === "Accident" ? "warning-outline" : t === "Road Closure" ? "close-circle-outline" : t === "Police" ? "shield-checkmark-outline" : "alert-circle-outline";
  const getIncidentColor = (t) =>
    t === "Traffic" ? "#FF6B35" : t === "Accident" ? "#E63946" : t === "Road Closure" ? "#9D4EDD" : t === "Police" ? "#0077B6" : "#808080";

  // Calculate marker size based on zoom level (latitudeDelta)
  const getMarkerSize = (latitudeDelta) => {
    // When zoomed out (large latitudeDelta > 0.1), use smaller markers
    // When zoomed in (small latitudeDelta < 0.02), use full size markers
    if (!latitudeDelta) return { size: 40, iconSize: 20, borderWidth: 3 }; // default
    
    if (latitudeDelta > 0.1) {
      // Very zoomed out - tiny markers
      return { size: 20, iconSize: 10, borderWidth: 2 };
    } else if (latitudeDelta > 0.05) {
      // Zoomed out - small markers
      return { size: 28, iconSize: 14, borderWidth: 2 };
    } else if (latitudeDelta > 0.02) {
      // Medium zoom - medium markers
      return { size: 34, iconSize: 17, borderWidth: 3 };
    } else {
      // Zoomed in - full size markers
      return { size: 40, iconSize: 20, borderWidth: 3 };
    }
  };

  // Get or create animated value for a marker (smooth fade in/out)
  const getMarkerAnimation = (markerId) => {
    if (!markerAnimations.current[markerId]) {
      const animatedValue = new Animated.Value(0);
      markerAnimations.current[markerId] = animatedValue;
      // Fade in animation
      Animated.timing(animatedValue, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    }
    return markerAnimations.current[markerId];
  };

  // Convert TomTom feature to point and type
  const tomtomFeatureToPointAndType = (feat) => {
    if (!feat?.geometry) return null;
    const props = feat.properties || {};
    const g = feat.geometry;

    const iconCat = Number(props.iconCategory);
    let type = "Traffic";
    if (iconCat === 8) type = "Road Closure";
    else if ([9, 10, 26].includes(iconCat)) type = "Accident";
    else if ([6, 7].includes(iconCat)) type = "Traffic";
    else if ([14].includes(iconCat)) type = "Police";

    let coord = null;
    if (g.type === "Point" && Array.isArray(g.coordinates) && g.coordinates.length >= 2) {
      const [lng, lat] = g.coordinates;
      coord = { latitude: lat, longitude: lng };
    } else if (g.type === "LineString" && Array.isArray(g.coordinates) && g.coordinates.length >= 2) {
      const mid = g.coordinates[Math.floor(g.coordinates.length / 2)];
      coord = { latitude: mid[1], longitude: mid[0] };
    }
    if (!coord) return null;

    const title = props?.events?.[0]?.description || props?.description || type;
    const probabilityOfOccurrence = props?.probabilityOfOccurrence;

    return { coord, type, title, probabilityOfOccurrence };
  };

  const handleMarkerPress = (alert) => {
    setSelectedAlert(alert);
    setShowModal(true);
  };

  const handleResolveIncident = async () => {
    if (!selectedAlert) return;
    try {
      await apiDelete(`/traffic-alerts/${selectedAlert.id}`);
      setTrafficAlerts((prev) => prev.filter((a) => a.id !== selectedAlert.id));
      setShowModal(false);
      setSelectedAlert(null);
      Alert.alert("Success", "Incident resolved and removed from the map.");
    } catch (error) {
      console.error("Error resolving incident:", error);
      Alert.alert("Error", "Failed to resolve incident. Please try again.");
    }
  };

  // ----- Directions -----
  const fetchDirections = async (o, d) => {
    if (!o || !d || inFlightRef.current) return;
    if (!isValidLatLng(o.latitude, o.longitude) || !isValidLatLng(d.latitude, d.longitude)) return;

    const now = Date.now();
    if (now - lastFetchRef.current < 2000) return;

    inFlightRef.current = true;
    setLoadingRoute(true);

    try {
      if (!API_BASE) throw new Error("BASE_URL not set");
      const qs = new URLSearchParams({
        origin: `${o.latitude},${o.longitude}`,
        destination: `${d.latitude},${d.longitude}`,
        mode: "driving",
        alternatives: "false",
      });
      const url = `${API_BASE}/maps/directions?${qs.toString()}`;
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      let coords = [];
      if (Array.isArray(data.coordinates)) {
        coords = data.coordinates
          .map((c) => ({ latitude: Number(c.latitude), longitude: Number(c.longitude) }))
          .filter((c) => isValidLatLng(c.latitude, c.longitude));
      } else {
        const encoded = data.overview_polyline?.points || data.overview_polyline || data.polyline;
        if (!encoded) throw new Error("No route polyline in response.");
        const pts = polyline.decode(encoded);
        coords = pts
          .map(([lat, lng]) => ({ latitude: Number(lat), longitude: Number(lng) }))
          .filter((c) => isValidLatLng(c.latitude, c.longitude));
      }

      setRouteCoords(coords);
      setDistance(data.distance_meters ?? data.distance ?? null);
      setDuration(data.duration_seconds ?? data.duration ?? null);

      if (coords.length >= 1) {
        safeAnimateToCenter(coords[0], 300); // keep camera sane even before fit
      }

      const doFit = () => {
        if (!showModal && coords.length > 1 && mapRef.current?.fitToCoordinates) {
          mapRef.current.fitToCoordinates(coords, {
            edgePadding: { top: 80, right: 80, bottom: 220, left: 80 },
            animated: true,
          });
        }
      };
      if (mapReady) setTimeout(doFit, 0);
      else pendingFitRef.current = coords;

      lastFetchRef.current = now;
    } catch (err) {
      Alert.alert("Route", String(err.message || err));
    } finally {
      inFlightRef.current = false;
      setLoadingRoute(false);
    }
  };

  // ---- Location + watchers ----
  useEffect(() => {
    let watcher = null;
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") return;

      const last = await Location.getLastKnownPositionAsync();
      if (last?.coords) {
        const quick = { latitude: last.coords.latitude, longitude: last.coords.longitude };
        setOrigin(quick);
      }

      const loc = await Location.getCurrentPositionAsync({});
      const currentPos = { latitude: loc.coords.latitude, longitude: loc.coords.longitude };
      setOrigin(currentPos);

      watcher = await Location.watchPositionAsync(
        { accuracy: Location.Accuracy.Balanced, distanceInterval: 5, timeInterval: 3000 },
        (pos) => {
          const next = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
          if (isValidLatLng(next.latitude, next.longitude)) setOrigin(next);
        }
      );
    })();
    return () => watcher?.remove?.();
  }, []);

  // Read destination from navigation params
  useFocusEffect(
    React.useCallback(() => {
      const dest = route.params?.destination;
      if (dest?.latitude && dest?.longitude && isValidLatLng(Number(dest.latitude), Number(dest.longitude))) {
        setDestination({ latitude: Number(dest.latitude), longitude: Number(dest.longitude), name: dest.name });
      }
    }, [route.params?.destination])
  );

  // Single throttled directions effect
  useEffect(() => {
    if (destination && origin) fetchDirections(origin, destination);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [destination, origin]);

  // Traffic alerts
  useEffect(() => {
    fetchTrafficAlerts();
    if (user?.id) fetchUserLocations();
    const intervalId = setInterval(fetchTrafficAlerts, 5 * 60 * 1000);
    return () => clearInterval(intervalId);
  }, [user?.id]);

  // Fetch TomTom incidents when map region changes (debounced)
  useEffect(() => {
    if (mapRegion) {
      // Clear existing timer
      if (regionChangeTimerRef.current) {
        clearTimeout(regionChangeTimerRef.current);
      }
      
      // Debounce: wait 1 second after user stops moving the map
      regionChangeTimerRef.current = setTimeout(() => {
        fetchTomTomIncidents(mapRegion);
      }, 1000);
      
      // Refresh every 2 minutes for real-time updates
      const intervalId = setInterval(() => {
        // Force fetch by clearing the last region
        lastFetchedRegionRef.current = null;
        fetchTomTomIncidents(mapRegion);
      }, 2 * 60 * 1000);
      
      return () => {
        clearInterval(intervalId);
        if (regionChangeTimerRef.current) {
          clearTimeout(regionChangeTimerRef.current);
        }
      };
    }
  }, [mapRegion]);

  // Cleanup old marker animations when markers change
  useEffect(() => {
    const currentMarkerIds = new Set([
      ...trafficAlerts.map(alert => `alert-${alert.id}`),
      ...tomtomIncidents.map((feat, idx) => feat?.id || `tomtom-${idx}`)
    ]);
    
    // Remove animations for markers that no longer exist
    Object.keys(markerAnimations.current).forEach(markerId => {
      if (!currentMarkerIds.has(markerId)) {
        delete markerAnimations.current[markerId];
      }
    });
  }, [trafficAlerts, tomtomIncidents]);

  useEffect(() => {
    if (route.params?.refresh) fetchTrafficAlerts();
  }, [route.params?.refresh]);

  // Refetch user locations when screen comes into focus (e.g., after setting home/work)
  useFocusEffect(
    React.useCallback(() => {
      if (user?.id) fetchUserLocations();
    }, [user?.id])
  );

  // On focus, restore a safe camera center (and force remount via isFocused below)
  useFocusEffect(
    React.useCallback(() => {
      const center =
        (origin && isValidLatLng(origin.latitude, origin.longitude) && origin) ||
        lastGoodCenterRef.current ||
        { latitude: SG_DEFAULT.latitude, longitude: SG_DEFAULT.longitude };
      // Delay a tick so MapView is mounted after focus:
      setTimeout(() => safeAnimateToCenter(center, 0), 0);
    }, [origin])
  );

  // Show loading indicator while getting location
  if (!origin) {
    return (
      <View style={[styles.root, { justifyContent: "center", alignItems: "center", backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.accent} />
        <Text style={{ color: theme.colors.text, marginTop: 12 }}>Getting your location...</Text>
      </View>
    );
  }

  return (
    <View style={styles.root}>
      {isFocused && ( // unmount map when not focused -> prevents stale camera/blue screen
        <MapView
          ref={mapRef}
          key={`map-${isFocused}`} // force clean mount on every focus
          provider={PROVIDER_GOOGLE}
          style={{ flex: 1 }}
          initialRegion={SG_DEFAULT}
          showsUserLocation
          showsMyLocationButton={false}
          onMapReady={() => {
            setMapReady(true);
            const center =
              (origin && isValidLatLng(origin.latitude, origin.longitude) && origin) ||
              lastGoodCenterRef.current ||
              { latitude: SG_DEFAULT.latitude, longitude: SG_DEFAULT.longitude };
            setTimeout(() => safeAnimateToCenter(center, 300), 200);

            if (pendingFitRef.current && mapRef.current?.fitToCoordinates) {
              const coords = pendingFitRef.current;
              pendingFitRef.current = null;
              setTimeout(() => {
                if (!showModal && coords?.length > 1) {
                  mapRef.current.fitToCoordinates(coords, {
                    edgePadding: { top: 80, right: 80, bottom: 220, left: 80 },
                    animated: true,
                  });
                }
              }, 0);
            }
          }}
          onRegionChangeComplete={(r) => {
            if (isValidLatLng(r?.latitude, r?.longitude)) {
              lastGoodCenterRef.current = { latitude: r.latitude, longitude: r.longitude };
              setMapRegion(r); // Update region to fetch TomTom incidents for visible area
            }
          }}
        >
          {trafficAlerts.map((alert) => {
            const lat = Number(alert.latitude);
            const lng = Number(alert.longitude);
            if (!isValidLatLng(lat, lng)) return null;
            const isUserReported = alert.reported_by != null;
            const displayTitle = isUserReported ? `Potential ${alert.obstruction_type}` : alert.obstruction_type;
            
            // Get marker size based on zoom level
            const markerSize = getMarkerSize(mapRegion?.latitudeDelta);
            const opacity = getMarkerAnimation(`alert-${alert.id}`);
            
            return (
              <Marker
                key={alert.id}
                coordinate={{ latitude: lat, longitude: lng }}
                title={displayTitle}
                description={alert.location_name || "Reported incident"}
                onPress={() => handleMarkerPress(alert)}
              >
                <Animated.View style={[
                  styles.markerContainer, 
                  { 
                    backgroundColor: getIncidentColor(alert.obstruction_type),
                    borderColor: '#FFD400', // Yellow for user reports
                    borderWidth: markerSize.borderWidth,
                    width: markerSize.size,
                    height: markerSize.size,
                    borderRadius: markerSize.size / 2,
                    opacity: opacity
                  }
                ]}>
                  <Ionicons name={safeIcon(getIncidentIcon(alert.obstruction_type))} size={markerSize.iconSize} color="white" />
                </Animated.View>
              </Marker>
            );
          })}

          {/* TomTom real-time traffic incidents */}
          {tomtomIncidents.map((feat, idx) => {
            const mapped = tomtomFeatureToPointAndType(feat);
            if (!mapped) return null;
            const { coord, type, title, probabilityOfOccurrence } = mapped;
            if (!isValidLatLng(coord.latitude, coord.longitude)) return null;
            
            // Get marker size based on zoom level
            const markerSize = getMarkerSize(mapRegion?.latitudeDelta);
            // Use feat id if available, otherwise use index
            const markerId = feat?.id || `tomtom-${idx}`;
            const opacity = getMarkerAnimation(markerId);
            
            return (
              <Marker
                key={markerId}
                coordinate={coord}
                title={title}
                description={`Real-time ${type}`}
              >
                <Animated.View style={[
                  styles.markerContainer,
                  { 
                    backgroundColor: getIncidentColor(type),
                    borderColor: '#EF4444', // Red for real-time incidents
                    borderWidth: markerSize.borderWidth,
                    width: markerSize.size,
                    height: markerSize.size,
                    borderRadius: markerSize.size / 2,
                    opacity: opacity
                  }
                ]}>
                  <Ionicons name={safeIcon(getIncidentIcon(type))} size={markerSize.iconSize} color="white" />
                </Animated.View>
              </Marker>
            );
          })}

          {userLocations.home &&
            isValidLatLng(userLocations.home.latitude, userLocations.home.longitude) && (
              <Marker
                coordinate={{ latitude: userLocations.home.latitude, longitude: userLocations.home.longitude }}
                title="Home"
                description={userLocations.home.address}
                onPress={handleHomePress}
              >
                <View style={[styles.markerContainer, { backgroundColor: "#3B82F6", borderColor: "#60A5FA" }]}>
                  <Ionicons name={safeIcon("home")} size={20} color="white" />
                </View>
              </Marker>
            )}

          {userLocations.work &&
            isValidLatLng(userLocations.work.latitude, userLocations.work.longitude) && (
              <Marker
                coordinate={{ latitude: userLocations.work.latitude, longitude: userLocations.work.longitude }}
                title="Work"
                description={userLocations.work.address}
                onPress={handleWorkPress}
              >
                <View style={[styles.markerContainer, { backgroundColor: "#8B5CF6", borderColor: "#A78BFA" }]}>
                  <Ionicons name={safeIcon("briefcase")} size={20} color="white" />
                </View>
              </Marker>
            )}

          {destination && isValidLatLng(destination.latitude, destination.longitude) && (
            <Marker
              coordinate={{ latitude: destination.latitude, longitude: destination.longitude }}
              title={destination.name || "Destination"}
            />
          )}

          {routeCoords.length > 1 && (
            <Polyline coordinates={routeCoords} strokeWidth={5} strokeColor="#4A90E2" />
          )}
        </MapView>
      )}

      {/* Location Recenter Button */}
      <TouchableOpacity style={styles.locationBtn} onPress={handleRecenterMap}>
        <Ionicons name={safeIcon("locate")} size={24} color={theme.colors.accent} />
      </TouchableOpacity>

      {/* Report Incident */}
      <TouchableOpacity
        style={[styles.warningBtn, { bottom: height * 0.14 + 10 }]}
        onPress={() => navigation.navigate("ReportRoadIncident")}
      >
        <Ionicons name={safeIcon("warning")} size={26} color="#ffe600ff" />
      </TouchableOpacity>

      {/* Bottom sheet */}
      <View style={styles.bottomSheet}>
        <TouchableOpacity onPress={() => navigation.navigate("Search")}>
          <View style={styles.search}>
            <Text style={styles.searchText}>{loadingRoute ? "Finding route…" : destination?.name || "Where to?"}</Text>
          </View>
        </TouchableOpacity>
        <View style={styles.quickRow}>
          <TouchableOpacity style={styles.quickBtn} onPress={handleHomePress}>
            <Ionicons name={safeIcon("home")} size={18} color={theme.colors.text} />
            <Text style={styles.quickTxt}>Home</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickBtn} onPress={handleWorkPress}>
            <Ionicons name={safeIcon("briefcase")} size={18} color={theme.colors.text} />
            <Text style={styles.quickTxt}>Work</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Incident Modal (fixed: style, not className) */}
      <Modal visible={showModal} transparent animationType="fade" onRequestClose={() => setShowModal(false)}>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            {selectedAlert && (
              <>
                <View style={styles.modalHeader}>
                  <View
                    style={[
                      styles.modalIconContainer,
                      { backgroundColor: getIncidentColor(selectedAlert.obstruction_type) },
                    ]}
                  >
                    <Ionicons name={safeIcon(getIncidentIcon(selectedAlert.obstruction_type))} size={26} color="white" />
                  </View>
                  <Text style={styles.modalTitle}>
                    {selectedAlert.reported_by != null ? `Potential ${selectedAlert.obstruction_type}` : selectedAlert.obstruction_type}
                  </Text>
                </View>

                <View style={styles.modalInfo}>
                  {selectedAlert.location_name && (
                    <>
                      <Text style={styles.modalLabel}>Location</Text>
                      <Text style={styles.modalValue}>{selectedAlert.location_name}</Text>
                    </>
                  )}
                  <Text style={styles.modalLabel}>Coordinates</Text>
                  <Text style={styles.modalValue}>
                    {Number(selectedAlert.latitude).toFixed(6)}, {Number(selectedAlert.longitude).toFixed(6)}
                  </Text>
                  {selectedAlert.created_at && (
                    <>
                      <Text style={styles.modalLabel}>Reported</Text>
                      <Text style={styles.modalValue}>{new Date(selectedAlert.created_at).toLocaleString()}</Text>
                    </>
                  )}
                </View>

                <View style={styles.modalButtons}>
                  <TouchableOpacity style={[styles.modalButton, styles.resolveButton]} onPress={handleResolveIncident}>
                    <Text style={styles.buttonText}>Resolve</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.modalButton, styles.cancelButton]}
                    onPress={() => setShowModal(false)}
                  >
                    <Text style={styles.buttonText}>Cancel</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

// src/screens/DirectionsPage.js
import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Dimensions,
  StyleSheet,
  Keyboard,
  Alert,
  Platform,
  Animated,
  PanResponder,
  Pressable,
  ScrollView,
} from "react-native";
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from "react-native-maps";
import * as Location from "expo-location";
import Ionicons from "@expo/vector-icons/Ionicons";
import polyline from "@mapbox/polyline";
import { useRoute, useNavigation } from "@react-navigation/native";
import useThemedStyles from "../hooks/useThemedStyles";
import { BASE_URL } from "../config/keys";
import { apiGet } from "../services/api";
import { useAuth } from "../context/AuthContext";
import AutocompleteBox from "../components/AutocompleteBox";
import NearestCarparkButton from "../components/NearestCarparkButton";
import DepartureRecommendationCard from "../components/DepartureRecommendationCard";
import DepartureOptimizationService from "../services/departureOptimizationService";

const { height } = Dimensions.get("window");

const BORDER_YELLOW = '#FFD400';
const BORDER_RED = '#EF4444';

const tomTomBorderForProbability = (prob) => {
  if (!prob) return BORDER_YELLOW;
  return String(prob).toLowerCase() === 'certain' ? BORDER_RED : BORDER_YELLOW;
};

/* ----------------------------- MRT Line Colors --------------------------- */
const MRT_LINE_COLORS = {
  NS: "#D42E12",
  EW: "#009645",
  NE: "#9900AA",
  CC: "#FA9E0D",
  DT: "#005EC4",
  TE: "#9D5B25",
  BP: "#748477",
  SW: "#748477",
  SE: "#748477",
  PW: "#748477",
  PE: "#748477",
  CR: "#97C616",
  JR: "#0099AA",
};


/* ----------------------------- API base URL ------------------------------ */
const API_BASE =
  BASE_URL ||
  (__DEV__
    ? Platform.select({ android: "http://10.0.2.2:8080", ios: "http://localhost:8080" })
    : "https://your-prod-domain.com");

/* ------------------------------ Mode metadata ---------------------------- */
const MODE_META = {
  driving: { label: "Drive", icon: "car", color: "#4C8BF5" },
  walking: { label: "Walk", icon: "walk", color: "#22C55E" },  // Green for walking
  bicycling: { label: "Bike", icon: "bicycle", color: "#F59E0B" },  // Yellow for biking
  transit: { label: "Public", icon: "train", color: "#A16EF1" },
};

/* ----------------------------- Helpers ----------------------------------- */
const newToken = () => Math.random().toString(36).slice(2) + Date.now().toString(36);
const decodePolyline = (enc) =>
  enc ? polyline.decode(enc).map(([lat, lng]) => ({ latitude: lat, longitude: lng })) : [];

const normalizeRoutes = (data) => {
  const rs = Array.isArray(data?.routes) && data.routes.length ? data.routes : [data].filter(Boolean);

  return rs
    .map((r, i) => {
      const leg = r?.legs?.[0] || {};
      const distText =
        r?.distance_text ??
        leg?.distance?.text ??
        (typeof leg?.distance?.value === "number" ? `${(leg.distance.value / 1000).toFixed(1)} km` : null);
      const durText =
        r?.duration_text ??
        leg?.duration?.text ??
        (typeof leg?.duration?.value === "number" ? `${Math.round(leg.duration.value / 60)} min` : null);

      const enc = r?.overview_polyline?.points || r?.overview_polyline || r?.encoded_polyline || r?.polyline;

      let coords = [];
      if (enc) {
        try { coords = decodePolyline(enc); } catch { coords = []; }
      } else if (Array.isArray(r?.coordinates)) {
        coords = r.coordinates;
      }

      const steps = r?.steps_detail || r?.steps || [];

      return {
        id: String(i),
        summary: r?.summary || leg?.summary || `Route ${i + 1}`,
        distanceText: distText || "--",
        durationText: durText || "--",
        coords,
        steps,
      };
    })
    .filter((x) => x.coords && x.coords.length > 0);
};

/* -------------------------- Transit timeline UI -------------------------- */
function TransitTimeline({ steps, theme }) {
  if (!Array.isArray(steps) || steps.length === 0) return null;

  const iconFor = (s) => {
    const mode = (s.travel_mode || "").toUpperCase();
    if (mode === "WALKING") return { name: "walk", tint: "#6B7280", tag: "Walk" };
    if (mode === "BICYCLING") return { name: "bicycle", tint: "#F59E0B", tag: "Bike" };
    if (mode === "TRANSIT") {
      const vt = s?.transit_details?.vehicle_type || "";
      if (vt === "BUS") return { name: "bus", tint: "#0EA5E9", tag: s?.transit_details?.line_short_name || "Bus" };
      return { name: "train", tint: "#8B5CF6", tag: s?.transit_details?.line_short_name || "MRT" };
    }
    return { name: "car", tint: "#3B82F6", tag: "Drive" };
  };

  const line = (s) => {
    const td = s?.transit_details;
    if (!td) return s.instruction || "";
    const carrier = td.line_short_name || td.line_name || "Transit";
    if (td.vehicle_type === "BUS") {
      const head = td.headsign ? ` → ${td.headsign}` : "";
      const stops = Number.isFinite(td.num_stops) ? ` (${td.num_stops} stops)` : "";
      return `${carrier}${head}${stops}`;
    }
    const head = td.headsign ? ` → ${td.headsign}` : "";
    const stops = Number.isFinite(td.num_stops) ? ` (${td.num_stops} stops)` : "";
    return `${carrier}${head}${stops}`;
  };

  return (
    <View style={{ marginTop: 8 }}>
      {steps.map((s, idx) => {
        const { name, tint, tag } = iconFor(s);
        const dTxt = s.distance_text || s.duration_text ? ` · ${s.distance_text || s.duration_text}` : "";
        return (
          <View key={idx} style={{ flexDirection: "row", alignItems: "flex-start", marginBottom: 10 }}>
            <View style={{ alignItems: "center", width: 20 }}>
              <Ionicons name={name} size={16} color={tint} />
              {idx < steps.length - 1 && (
                <View style={{ width: 2, flex: 1, backgroundColor: "#e5e7eb", marginTop: 4, marginBottom: -4 }} />
              )}
            </View>
            <View style={{ flex: 1, marginLeft: 6 }}>
              <Text style={{ color: theme.colors.text, fontWeight: "700" }}>
                {tag}
                <Text style={{ color: theme.colors.muted, fontWeight: "600" }}>{dTxt}</Text>
              </Text>
              <Text style={{ color: theme.colors.text, marginTop: 2 }}>
                {line(s) || s.instruction || "Proceed to next step"}
              </Text>
              {s?.transit_details && (
                <Text style={{ color: theme.colors.muted, marginTop: 2 }}>
                  {s.transit_details.departure_stop ? `From ${s.transit_details.departure_stop}` : ""}
                  {s.transit_details.departure_time_text ? ` at ${s.transit_details.departure_time_text}` : ""}
                  {(s.transit_details.departure_stop || s.transit_details.departure_time_text) &&
                  (s.transit_details.arrival_stop || s.transit_details.arrival_time_text) ? " → " : ""}
                  {s.transit_details.arrival_stop ? `${s.transit_details.arrival_stop}` : ""}
                  {s.transit_details.arrival_time_text ? ` (${s.transit_details.arrival_time_text})` : ""}
                </Text>
              )}
            </View>
          </View>
        );
      })}
    </View>
  );
}

/* ----------------------- Incident marker helpers (icons) ------------------ */
const getIncidentIcon = (obstructionType) => {
  switch (obstructionType) {
    case "Traffic":
      return "car-outline";
    case "Accident":
      return "warning-outline";
    case "Road Closure":
      return "close-circle-outline";
    case "Police":
      return "shield-checkmark-outline";
    default:
      return "alert-circle-outline";
  }
};
const getIncidentColor = (obstructionType, themeAccent = "#7c5cff") => {
  switch (obstructionType) {
    case "Traffic":
      return "#FF6B35";
    case "Accident":
      return "#E63946";
    case "Road Closure":
      return "#9D4EDD";
    case "Police":
      return "#0077B6";
    default:
      return themeAccent;
  }
};

// Convert TomTom feature → single point + best-guess type string used above
function tomtomFeatureToPointAndType(feat) {
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

  const title =
    props?.events?.[0]?.description ||
    props?.description ||
    type;

  return { coord, type, title, probabilityOfOccurrence: props?.probabilityOfOccurrence };
}

/* ----------------- Geometry helpers for "near path" filtering ------------- */
function __haversineMeters(a, b) {
  const R = 6371000;
  const dLat = (b.latitude - a.latitude) * Math.PI / 180;
  const dLon = (b.longitude - a.longitude) * Math.PI / 180;
  const lat1 = a.latitude * Math.PI / 180;
  const lat2 = b.latitude * Math.PI / 180;
  const sinDLat = Math.sin(dLat / 2);
  const sinDLon = Math.sin(dLon / 2);
  const c = 2 * Math.asin(Math.sqrt(sinDLat * sinDLat + Math.cos(lat1) * Math.cos(lat2) * sinDLon * sinDLon));
  return R * c;
}

function __pointToSegmentDistanceMeters(P, A, B) {
  const toRad = (x) => (x * Math.PI) / 180;
  const lenAB = __haversineMeters(A, B);
  if (lenAB === 0) return __haversineMeters(P, A);

  const latAvg = toRad((A.latitude + B.latitude) / 2);
  const mPerDegLat = 111132.92 - 559.82 * Math.cos(2 * latAvg) + 1.175 * Math.cos(4 * latAvg);
  const mPerDegLon = 111412.84 * Math.cos(latAvg) - 93.5 * Math.cos(3 * latAvg);

  const Ax = (B.longitude - A.longitude) * mPerDegLon;
  const Ay = (B.latitude - A.latitude) * mPerDegLat;
  const APx = (P.longitude - A.longitude) * mPerDegLon;
  const APy = (P.latitude - A.latitude) * mPerDegLat;

  const ab2 = Ax * Ax + Ay * Ay;
  let t = (APx * Ax + APy * Ay) / ab2;
  t = Math.max(0, Math.min(1, t));

  const closest = {
    latitude: A.latitude + (B.latitude - A.latitude) * t,
    longitude: A.longitude + (B.longitude - A.longitude) * t,
  };
  return __haversineMeters(P, closest);
}

function __isCoordNearPath(coord, path, thresholdM = 300) {
  if (!Array.isArray(path) || path.length < 2) return false;
  for (let i = 0; i < path.length - 1; i++) {
    const d = __pointToSegmentDistanceMeters(coord, path[i], path[i + 1]);
    if (d <= thresholdM) return true;
  }
  return false;
}

function __toLatLngPathTomTom(lineString) {
  return (lineString || []).map(([lng, lat]) => ({ latitude: lat, longitude: lng }));
}

/* ------------------------------- Screen ---------------------------------- */
export default function DirectionsPage() {
  const navigation = useNavigation();
  const routeNav = useRoute();
  const mapRef = useRef(null);

  // ---- Half-screen bottom sheet ----
  const COLLAPSED = 120;
  const EXPANDED  = Math.round(height * 0.5) + 100;

  const sheetHeight = useRef(new Animated.Value(COLLAPSED)).current;
  const opened = useRef(false);

  const backOpacity = sheetHeight.interpolate({
    inputRange: [COLLAPSED, EXPANDED],
    outputRange: [0, 0.35],
    extrapolate: "clamp",
  });

  const dragStartRef = useRef(COLLAPSED);
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dy) > 3,
      onPanResponderGrant: () => sheetHeight.stopAnimation(v => (dragStartRef.current = v)),
      onPanResponderMove: (_, g) => {
        const next = Math.max(COLLAPSED, Math.min(EXPANDED, dragStartRef.current - g.dy));
        sheetHeight.setValue(next);
      },
      onPanResponderRelease: (_, g) => {
        sheetHeight.stopAnimation((currentValue) => {
          const MOMENTUM = 80;
          const projected = currentValue - g.vy * MOMENTUM;
          const finalY = Math.max(COLLAPSED, Math.min(EXPANDED, projected));
          opened.current = finalY > (COLLAPSED + EXPANDED) / 2;
          Animated.timing(sheetHeight, {
            toValue: finalY,
            duration: 160,
            useNativeDriver: false,
          }).start(() => {
            dragStartRef.current = finalY;
          });
        });
      },
    })
  ).current;

  const { styles, theme } = useThemedStyles(({ colors }) => ({
    root: { flex: 1, backgroundColor: colors.background },
    sheet: {
      position: "absolute",
      left: 0, right: 0, bottom: 0,
      backgroundColor: colors.card,
      borderTopLeftRadius: 22, borderTopRightRadius: 22,
      borderTopWidth: StyleSheet.hairlineWidth, borderColor: colors.border,
      shadowColor: "#000", shadowOffset: { width: 0, height: -6 }, shadowOpacity: 0.18, shadowRadius: 18, elevation: 24,
      overflow: "hidden",
    },
    dragArea: { paddingTop: 10, paddingBottom: 14, paddingHorizontal: 16 },
    handle: { alignSelf: "center", width: 44, height: 5, borderRadius: 999, backgroundColor: colors.border, marginBottom: 12 },
    headerRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
    title: { fontWeight: "900", fontSize: 18, color: colors.text },
    closeBtn: {
      width: 30, height: 30, borderRadius: 15, alignItems: "center", justifyContent: "center",
      backgroundColor: colors.pill, borderColor: colors.border, borderWidth: StyleSheet.hairlineWidth,
    },
    chipsScroller: { paddingHorizontal: 16, paddingBottom: 10 },
    chipsRowContent: { flexDirection: "row", alignItems: "center" },
    chip: {
      flexDirection: "row", alignItems: "center",
      paddingVertical: 8, paddingHorizontal: 12, borderRadius: 999,
      backgroundColor: colors.pill, borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border, marginRight: 10,
    },
    chipTxt: { marginLeft: 6, fontWeight: "800", color: colors.text },
    listWrap: { flex: 1, paddingHorizontal: 16, paddingBottom: 16 },
    sectionTitle: { fontSize: 12, fontWeight: "700", color: colors.muted, marginBottom: 8 },
    routeCard: {
      paddingVertical: 12, paddingHorizontal: 14, borderRadius: 14,
      borderWidth: StyleSheet.hairlineWidth, backgroundColor: colors.card,
      marginBottom: 12, borderColor: colors.border,
    },
    routeTitle: { color: colors.text, fontWeight: "900", fontSize: 14 },
    routeSub: { color: colors.muted, marginTop: 4, fontWeight: "600" },

    // NEW small Start button styles (used inline with dynamic colors, but spacing here)
    startBtnWrap: { flexDirection: "row", alignItems: "center", gap: 8 },

    userRouteCard: {
      flexDirection: "row", alignItems: "center",
      paddingVertical: 10, paddingHorizontal: 12,
      borderRadius: 12, backgroundColor: colors.card,
      borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border, marginBottom: 8,
    },
    userRouteIcon: {
      width: 36, height: 36, borderRadius: 18,
      backgroundColor: MODE_META.walking.color + "22",
      alignItems: "center", justifyContent: "center", marginRight: 10,
    },
    userRouteInfo: { flex: 1 },
    userRouteTitle: { color: colors.text, fontWeight: "700", fontSize: 13 },
    userRouteStats: { flexDirection: "row", alignItems: "center", marginTop: 2 },
    userRouteStat: { color: colors.muted, fontSize: 11, fontWeight: "600" },
    viewMoreButton: {
      flexDirection: "row", alignItems: "center", justifyContent: "center",
      paddingVertical: 10, paddingHorizontal: 16, borderRadius: 12,
      backgroundColor: colors.pill, borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border,
    },
    viewMoreText: { color: colors.text, fontWeight: "700", fontSize: 13, marginRight: 4 },
  }));

  const paramOrigin = routeNav.params?.origin;
  const paramDest   = routeNav.params?.destination;
  const initialMode = routeNav.params?.initialMode || "driving";

  const [originText, setOriginText] = useState(paramOrigin?.name || "Your Location");
  const [origin, setOrigin] = useState(paramOrigin?.latitude ? { latitude: paramOrigin.latitude, longitude: paramOrigin.longitude } : null);
  const [destText, setDestText] = useState(paramDest?.name ?? "");
  const [destination, setDestination] = useState(paramDest?.latitude ? { latitude: paramDest.latitude, longitude: paramDest.longitude } : null);
  const [userLocation, setUserLocation] = useState(null);

  const [mode, setMode] = useState(initialMode);
  const [routes, setRoutes] = useState([]);
  const [activeIndex, setActiveIndex] = useState(0);
  
  // Departure optimization state
  const [departureOptimization, setDepartureOptimization] = useState(null);
  const [departureLoading, setDepartureLoading] = useState(false);
  const [departureError, setDepartureError] = useState(null);
  const active = routes[activeIndex];

  const [userRoutes, setUserRoutes] = useState([]);
  const [loadingUserRoutes, setLoadingUserRoutes] = useState(false);
  const [selectedUserRoute, setSelectedUserRoute] = useState(null);
  const { user } = useAuth();

  /* ---------------------- Incidents (icons) state ----------------------- */
  const [showIncidents, setShowIncidents] = useState(false);
  const [incidentsLoading, setIncidentsLoading] = useState(false);
  const [communityIncidents, setCommunityIncidents] = useState([]); // /traffic-alerts
  const [tomtomIncidents, setTomtomIncidents] = useState([]);       // /maps/traffic-incidents
  const [mapRegion, setMapRegion] = useState(null); // Track map zoom level

  const getMarkerSize = useCallback((latitudeDelta) => {
    if (!latitudeDelta) return { size: 36, iconSize: 20, borderWidth: 3 };
    if (latitudeDelta > 0.1) return { size: 20, iconSize: 10, borderWidth: 2 };
    else if (latitudeDelta > 0.05) return { size: 28, iconSize: 14, borderWidth: 2 };
    else if (latitudeDelta > 0.02) return { size: 32, iconSize: 16, borderWidth: 3 };
    return { size: 36, iconSize: 20, borderWidth: 3 };
  }, []);

  const markerSize = useMemo(() => getMarkerSize(mapRegion?.latitudeDelta), [mapRegion?.latitudeDelta, getMarkerSize]);

  const fetchIncidents = useCallback(async () => {
    try {
      setIncidentsLoading(true);
      const community = await apiGet('/traffic-alerts?status=active').catch(() => []);
      setCommunityIncidents(Array.isArray(community) ? community : []);

      const bbox = "103.6,1.20,104.1,1.50";
      const url = `${API_BASE}/maps/traffic-incidents?bbox=${encodeURIComponent(bbox)}&time_validity=present`;
      const res = await fetch(url);
      if (res.ok) {
        const j = await res.json();
        const incidents = Array.isArray(j?.incidents) ? j.incidents : [];
        setTomtomIncidents(incidents);
      } else {
        setTomtomIncidents([]);
      }
    } catch {
      setTomtomIncidents([]);
      setCommunityIncidents([]);
    } finally {
      setIncidentsLoading(false);
    }
  }, []);

  const coloredSegments = useMemo(() => {
    if (mode !== "transit" || !active || !Array.isArray(active.steps)) {
      console.log("❌ Not building segments:", { mode, hasActive: !!active, hasSteps: Array.isArray(active?.steps) });
      return [];
    }
    
    console.log("🚇 Building colored segments for transit route");
    console.log("Active route:", JSON.stringify(active, null, 2));
    console.log("Active route steps:", active.steps?.length);
    
    const segments = [];
    for (let i = 0; i < active.steps.length; i++) {
      const step = active.steps[i];
      const polylineData =
        step?.polyline?.points ||
        step?.polyline ||
        step?.encoded_polyline ||
        step?.points;

      if (!polylineData) {
        console.log(`⚠️ Step ${i}: No polyline data found`);
        continue;
      }
      
      const coords = decodePolyline(polylineData);
      if (!coords || coords.length < 2) {
        console.log(`⚠️ Step ${i}: Invalid coords after decode`);
        continue;
      }
      
      const travelMode = (step.travel_mode || "").toUpperCase();
      let color;
      let lineName = "";
      
      if (travelMode === "TRANSIT") {
        lineName = step?.transit_details?.line_short_name || step?.transit_details?.line_name || "";
        
        console.log(`🔍 Step ${i} TRANSIT Details:`, {
          lineName,
          line_short_name: step?.transit_details?.line_short_name,
          line_name: step?.transit_details?.line_name,
          line_color: step?.transit_details?.line_color,
          vehicle_type: step?.transit_details?.vehicle_type
        });
        
        // Extract line prefix FIRST - prioritize custom MRT colors over API
        let linePrefix = null;
        const match = lineName.match(/^([A-Z]{2})/);
        if (match) {
          linePrefix = match[1];
        }
        
        console.log(`🔍 Extracted linePrefix: "${linePrefix}" from lineName: "${lineName}"`);
        
        // PRIORITIZE our custom MRT colors over API colors
        if (linePrefix && MRT_LINE_COLORS[linePrefix]) {
          color = MRT_LINE_COLORS[linePrefix];
          console.log(`✅ Using custom MRT color for ${linePrefix}: ${color}`);
        } else if (step?.transit_details?.line_color) {
          // Fallback to API color only if we don't have a custom color
          color = step.transit_details.line_color.startsWith("#")
            ? step.transit_details.line_color
            : `#${step.transit_details.line_color}`;
          console.log(`🎨 Using API color: ${color} (no custom color for "${lineName}")`);
        } else {
          // Final fallback to default transit color
          color = MODE_META.transit.color;
          console.log(`⚠️ No color found, using default: ${color}`);
        }
      } else if (travelMode === "WALKING") {
        color = MODE_META.walking.color;
        console.log(`🚶 Step ${i} WALKING: color=${color}`);
      } else if (travelMode === "BICYCLING") {
        color = MODE_META.bicycling.color;
      } else {
        color = MODE_META.driving.color;
      }
      
      segments.push({ coords, color, travelMode, lineName });
      console.log(`✅ Added segment ${i}: mode=${travelMode}, lineName=${lineName}, color=${color}, coords=${coords.length}`);
    }
    
    console.log(`📊 Total segments created: ${segments.length}`);
    return segments;
  }, [active, mode, activeIndex]);

  const handleSwapLocations = () => {
    const tempCoord = origin;
    setOrigin(destination);
    setDestination(tempCoord);
    const tempText = originText;
    setOriginText(destText);
    setDestText(tempText);
  };

  const strokeColor = MODE_META[mode]?.color || "#3367FF";

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") return;
      const loc = await Location.getCurrentPositionAsync({});
      const currentPos = { latitude: loc.coords.latitude, longitude: loc.coords.longitude };
      setUserLocation(currentPos);
      if (!origin) {
        setOrigin(currentPos);
        if (!originText || originText === "Your Location") setOriginText("Your Location");
      }
    })();
  }, []);

  useEffect(() => {
    if (paramDest?.latitude && paramDest?.longitude) {
      setDestination({ latitude: paramDest.latitude, longitude: paramDest.longitude });
      setDestText(paramDest.name || "");
    }
    if (paramOrigin?.latitude && paramOrigin?.longitude) {
      setOrigin({ latitude: paramOrigin.latitude, longitude: paramOrigin.longitude });
      setOriginText(paramOrigin.name || "Your Location");
    }
    if (initialMode && initialMode !== mode) {
      setMode(initialMode);
    }
  }, [paramOrigin, paramDest, initialMode]);

  const queryString = useMemo(() => {
    if (!origin || !destination) return "";
    const p = new URLSearchParams({
      origin: `${origin.latitude},${origin.longitude}`,
      destination: `${destination.latitude},${destination.longitude}`,
      mode,
      alternatives: "true",
    });
    if (mode === "transit" || mode === "driving") {
      p.set("departure_time", Math.floor(Date.now() / 1000).toString());
    }
    return p.toString();
  }, [origin, destination, mode]);

  const fetchDirections = useCallback(async () => {
    if (!origin || !destination || !queryString) return;
    try {
      const res = await fetch(`${API_BASE}/maps/directions?${queryString}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const normalized = normalizeRoutes(data);
      setRoutes(normalized);
      setActiveIndex(0);
      if (normalized[0]?.coords?.length > 1) {
        mapRef.current?.fitToCoordinates(normalized[0].coords, {
          edgePadding: { top: 120, right: 80, bottom: 220, left: 80 },
          animated: true,
        });
      }
      
      // Fetch departure optimization for driving mode
      if (mode === 'driving' && normalized[0]) {
        fetchDepartureOptimization(normalized[0]);
      } else {
        // Clear optimization for non-driving modes
        setDepartureOptimization(null);
        setDepartureError(null);
      }
    } catch (e) {
      Alert.alert("Directions", e.message || String(e));
      setRoutes([]);
    }
  }, [origin, destination, queryString, mode]);

  const fetchDepartureOptimization = useCallback(async (route) => {
    // Only optimize for driving mode
    if (mode !== 'driving') {
      setDepartureOptimization(null);
      return;
    }

    try {
      setDepartureLoading(true);
      setDepartureError(null);

      // Extract route coordinates
      const routeCoords = DepartureOptimizationService.extractRouteCoordinates(route);
      
      if (routeCoords.length < 2) {
        setDepartureError('Route too short for optimization');
        return;
      }

      // Parse ETA from duration text
      const etaMinutes = DepartureOptimizationService.parseEtaMinutes(route.durationText);
      
      if (etaMinutes === 0) {
        setDepartureError('Unable to determine travel time');
        return;
      }

      // Call optimization service
      const result = await DepartureOptimizationService.findOptimalDeparture(
        routeCoords,
        etaMinutes,
        0.5,  // 500m radius
        120   // 2 hour forecast
      );

      setDepartureOptimization(result);
    } catch (error) {
      console.error('Departure optimization error:', error);
      setDepartureError(error.message || 'Failed to optimize departure time');
    } finally {
      setDepartureLoading(false);
    }
  }, [mode]);

  const fetchNearbyUserRoutes = useCallback(async () => {
    if (!origin || !destination || (mode !== "walking" && mode !== "bicycling")) {
      setUserRoutes([]);
      return;
    }
    setLoadingUserRoutes(true);
    try {
      const userId = user?.id || "";
      const response = await apiGet(`/user-routes?user_id=${userId}`);
      
      // Filter routes where start point is within 1km of origin AND end point is within 1km of destination
      const nearbyRoutes = response.filter(route => {
        if (!route.route_points || route.route_points.length < 2) return false;
        
        const startPoint = route.route_points[0];
        const endPoint = route.route_points[route.route_points.length - 1];
        
        const distFromOriginToStart = calculateDistance(
          origin.latitude, 
          origin.longitude, 
          startPoint.latitude, 
          startPoint.longitude
        );
        
        const distFromDestinationToEnd = calculateDistance(
          destination.latitude, 
          destination.longitude, 
          endPoint.latitude, 
          endPoint.longitude
        );
        
        // Both start and end must be within 1km
        return distFromOriginToStart <= 1 && distFromDestinationToEnd <= 1;
      });
      
      const modeFiltered = nearbyRoutes.filter(route => {
        if (mode === "walking") return route.transport_mode === "walking";
        if (mode === "bicycling") return route.transport_mode === "bicycling";
        return true;
      });
      
      const sorted = modeFiltered
        .map(route => {
          const startPoint = route.route_points[0];
          const endPoint = route.route_points[route.route_points.length - 1];
          
          // Calculate combined distance score (average of both distances)
          const distToStart = calculateDistance(origin.latitude, origin.longitude, startPoint.latitude, startPoint.longitude);
          const distToEnd = calculateDistance(destination.latitude, destination.longitude, endPoint.latitude, endPoint.longitude);
          const combinedDist = (distToStart + distToEnd) / 2;
          
          return { ...route, distanceScore: combinedDist };
        })
        .sort((a, b) => a.distanceScore - b.distanceScore)
        .slice(0, 3);
      setUserRoutes(sorted);
    } catch {
      setUserRoutes([]);
    } finally {
      setLoadingUserRoutes(false);
    }
  }, [origin, destination, mode, user]);

  const calculateDistance = useCallback((lat1, lon1, lat2, lon2) => {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }, []);

  useEffect(() => { fetchDirections(); }, [fetchDirections]);
  useEffect(() => { fetchNearbyUserRoutes(); }, [fetchNearbyUserRoutes]);
  useEffect(() => { if (showIncidents) fetchIncidents(); }, [showIncidents, fetchIncidents]);

  const selectRoute = useCallback((idx) => {
    setActiveIndex(idx);
    setSelectedUserRoute(null);
    const r = routes[idx];
    if (r?.coords?.length > 1) {
      mapRef.current?.fitToCoordinates(r.coords, {
        edgePadding: { top: 120, right: 80, bottom: 220, left: 80 },
        animated: true,
      });
    }
  }, [routes]);

  const combinedRoutes = useMemo(() => {
    const items = [];
    
    // Add departure optimization card for driving mode at the top
    if (mode === 'driving') {
      items.push({ type: 'departure' });
    }
    
    items.push({ type: 'section', title: 'Recommended routes' });
    routes.forEach((route, index) => items.push({ type: 'google', data: route, index }));
    if (routes.length === 0) items.push({ type: 'empty', message: 'No alternative routes' });
    if (mode === "walking" || mode === "bicycling") {
      items.push({ type: 'section', title: 'Community Suggested Routes' });
      if (loadingUserRoutes) items.push({ type: 'loading' });
      else if (userRoutes.length > 0) {
        userRoutes.forEach((route) => items.push({ type: 'user', data: route }));
        items.push({ type: 'viewMore' });
      } else items.push({ type: 'empty', message: 'No community routes found near this destination' });
    }
    if (mode === "driving" && destination) {
      items.push({ type: 'carpark' });
    }
    return items;
  }, [routes, userRoutes, mode, loadingUserRoutes, destination]);

  const getModeIcon = useCallback((transportMode) => {
    switch (transportMode) {
      case "walking": return "walk";
      case "bicycling": return "bicycle";
      case "driving": return "car";
      case "transit": return "train";
      default: return "location";
    }
  }, []);
  
  const getModeColor = useCallback((transportMode) => {
    switch (transportMode) {
      case "walking": return "#22C55E";  // Green for walking
      case "bicycling": return "#F59E0B";  // Yellow for biking
      case "driving": return MODE_META.driving.color;
      case "transit": return MODE_META.transit.color;
      default: return "#6B7280";
    }
  }, []);
  
  const formatDistance = useCallback((meters) => (!meters ? "--" : meters < 1000 ? `${Math.round(meters)}m` : `${(meters/1000).toFixed(1)}km`), []);
  
  const formatDuration = useCallback((minutes) => {
    if (!minutes || minutes === 0) return "--";
    if (minutes < 60) return `${Math.round(minutes)}min`;
    const h = Math.floor(minutes / 60); const m = Math.round(minutes % 60);
    return m > 0 ? `${h}h ${m}min` : `${h}h`;
  }, []);
  
  // Calculate realistic duration based on distance and transport mode
  const calculateRealisticDuration = useCallback((distanceMeters, transportMode) => {
    if (!distanceMeters || distanceMeters === 0) return 0;
    const distanceKm = distanceMeters / 1000;
    
    // Average speeds in km/h
    const speeds = {
      walking: 5,     // 5 km/h
      bicycling: 15,  // 15 km/h
      driving: 40,    // 40 km/h (accounting for city traffic)
      transit: 30,    // 30 km/h
    };
    
    const speed = speeds[transportMode] || speeds.walking;
    const hours = distanceKm / speed;
    return Math.round(hours * 60); // Convert to minutes
  }, []);
  
  const handleViewUserRoute = useCallback((route) => {
    setSelectedUserRoute(route);
    if (route.route_points && route.route_points.length > 1) {
      const coords = route.route_points.map(p => ({ latitude: p.latitude, longitude: p.longitude }));
      mapRef.current?.fitToCoordinates(coords, { edgePadding: { top: 120, right: 80, bottom: 220, left: 80 }, animated: true });
    }
  }, []);
  
  const handleViewMoreUserRoutes = useCallback(() => navigation.navigate("UserSuggestedRoutePage", { filterLocation: destination, filterMode: mode }), [navigation, destination, mode]);

  const filteredCommunityIncidents = useMemo(() => {
    if (!showIncidents) return [];
    if (!active || !Array.isArray(active.coords) || active.coords.length < 2) {
      return Array.isArray(communityIncidents) ? communityIncidents : [];
    }
    const path = active.coords;
    const THRESHOLD_M = 500;
    return (communityIncidents || []).filter((it) => {
      if (typeof it.latitude !== "number" || typeof it.longitude !== "number") return false;
      return __isCoordNearPath({ latitude: it.latitude, longitude: it.longitude }, path, THRESHOLD_M);
    });
  }, [communityIncidents, active, activeIndex, mode, showIncidents]);

  const filteredTomtomIncidents = useMemo(() => {
    if (!showIncidents) return [];
    if (!active || !Array.isArray(active.coords) || active.coords.length < 2) {
      const incidents = Array.isArray(tomtomIncidents) ? tomtomIncidents : [];
      return incidents;
    }
    const path = active.coords;
    const THRESHOLD_M = 500;
    const filtered = (tomtomIncidents || []).filter((feat) => {
      const g = feat?.geometry;
      if (!g) return false;
      if (g.type === "Point" && Array.isArray(g.coordinates) && g.coordinates.length >= 2) {
        const [lng, lat] = g.coordinates;
        return __isCoordNearPath({ latitude: lat, longitude: lng }, path, THRESHOLD_M);
      }
      if (g.type === "LineString" && Array.isArray(g.coordinates) && g.coordinates.length >= 2) {
        const pts = __toLatLngPathTomTom(g.coordinates);
        for (let i = 0; i < pts.length; i++) {
          if (__isCoordNearPath(pts[i], path, THRESHOLD_M)) return true;
        }
        return false;
      }
      return false;
    });
    return filtered;
  }, [tomtomIncidents, active, activeIndex, mode, showIncidents]);

  if (!destination) {
    return (
      <View style={[styles.root, { justifyContent: "center", alignItems: "center" }]}>
        <Text>No destination selected</Text>
      </View>
    );
  }

  return (
    <View style={styles.root}>
      {/* Map */}
      <MapView
        ref={mapRef}
        provider={PROVIDER_GOOGLE}
        style={{ flex: 1 }}
        initialRegion={{
          latitude: destination.latitude || origin?.latitude || 1.3521,
          longitude: destination.longitude || origin?.longitude || 103.8198,
          latitudeDelta: 0.06, longitudeDelta: 0.06,
        }}
        showsUserLocation
        showsMyLocationButton
        onRegionChangeComplete={(region) => setMapRegion(region)}
      >
        {/* Origin / Destination */}
        {origin && <Marker coordinate={origin} title="You" pinColor="dodgerblue" />}
        {destination && <Marker coordinate={destination} title={destText || "Destination"} pinColor="red" />}

        {/* Transit polyline (optimized) */}
        {mode === "transit" && coloredSegments.length > 0 ? (
          <>
            {coloredSegments.map((seg, i) => {
              console.log(`🎨 Rendering Polyline ${i}: color=${seg.color}, mode=${seg.travelMode}, coords=${seg.coords.length}`);
              return (
                <Polyline
                  key={`transit-${seg.travelMode}-${i}`}
                  coordinates={seg.coords}
                  strokeWidth={6}
                  strokeColors={[seg.color]}
                  lineDashPattern={seg.travelMode === "WALKING" ? [8, 8] : undefined}
                  lineCap="round"
                />
              );
            })}
            {coloredSegments.map((seg, i) => {
              if (seg.travelMode !== "TRANSIT" || !seg.coords[0] || !seg.lineName) return null;
              // Check if this is a transition point (start of route or line change)
              const prevSeg = i > 0 ? coloredSegments[i - 1] : null;
              const isTransition = i === 0 || prevSeg?.travelMode !== "TRANSIT" || prevSeg?.lineName !== seg.lineName;
              if (!isTransition) return null;
              
              return (
                <Marker key={`line-${i}`} coordinate={seg.coords[0]} anchor={{ x: 0.5, y: 0.5 }}>
                  <View style={{
                    backgroundColor: seg.color,
                    paddingHorizontal: 8,
                    paddingVertical: 4,
                    borderRadius: 12,
                    borderWidth: 2,
                    borderColor: '#FFF',
                    shadowColor: '#000',
                    shadowOffset: { width: 0, height: 2 },
                    shadowOpacity: 0.25,
                    shadowRadius: 3.84,
                    elevation: 5,
                  }}>
                    <Text style={{ color: '#FFF', fontWeight: 'bold', fontSize: 11 }}>{seg.lineName}</Text>
                  </View>
                </Marker>
              );
            })}
          </>
        ) : null}
        
        {/* User Suggested Route Polyline - Always Green for Walking/Biking */}
        {selectedUserRoute && selectedUserRoute.route_points && selectedUserRoute.route_points.length > 1 && (
          <>
            <Polyline
              coordinates={selectedUserRoute.route_points.map(p => ({ latitude: p.latitude, longitude: p.longitude }))}
              strokeWidth={6}
              strokeColor="#22C55E"
              lineCap="round"
              lineJoin="round"
            />
            {/* Start pin for user route */}
            <Marker
              coordinate={{
                latitude: selectedUserRoute.route_points[0].latitude,
                longitude: selectedUserRoute.route_points[0].longitude
              }}
              title="Route Start"
              pinColor="#22C55E"
            />
            {/* End pin for user route */}
            <Marker
              coordinate={{
                latitude: selectedUserRoute.route_points[selectedUserRoute.route_points.length - 1].latitude,
                longitude: selectedUserRoute.route_points[selectedUserRoute.route_points.length - 1].longitude
              }}
              title="Route End"
              pinColor="#EF4444"
            />
          </>
        )}
        
        {/* Google Route Polyline - Only show if no user route selected */}
        {!selectedUserRoute && active?.coords?.length > 0 && mode !== "transit" && (
          <Polyline
            coordinates={active.coords}
            strokeWidth={6}
            strokeColor={mode === "walking" || mode === "bicycling" ? "#22C55E" : strokeColor}
            lineCap="round"
            lineJoin="round"
          />
        )}
        
        {/* Fallback Transit Polyline - Show overall route if colored segments failed */}
        {mode === "transit" && coloredSegments.length === 0 && active?.coords?.length > 0 && (
          <Polyline
            coordinates={active.coords}
            strokeWidth={6}
            strokeColor={MODE_META.transit.color}
            lineCap="round"
            lineJoin="round"
          />
        )}

        {/* ---------------- Incident Markers (Icons, FILTERED) ---------------- */}
        {showIncidents && (
          <>
            {filteredCommunityIncidents.map((it) => {
              const iconName = getIncidentIcon(it.obstruction_type);
              const bg = getIncidentColor(it.obstruction_type);
              if (typeof it.latitude !== "number" || typeof it.longitude !== "number") return null;
              return (
                <Marker
                  key={`comm-${it.id}`}
                  coordinate={{ latitude: it.latitude, longitude: it.longitude }}
                  title={it.obstruction_type}
                  description={it.location_name || "Reported incident"}
                >
                  <Animated.View
                    style={{
                      width: markerSize.size,
                      height: markerSize.size,
                      borderRadius: markerSize.size / 2,
                      justifyContent: "center",
                      alignItems: "center",
                      backgroundColor: bg,
                      borderColor: "#FFD400",
                      borderWidth: markerSize.borderWidth,
                      shadowColor: "#000",
                      shadowOffset: { width: 0, height: 2 },
                      shadowOpacity: 0.3,
                      shadowRadius: 4,
                      elevation: 5,
                    }}
                  >
                    <Ionicons name={iconName} size={markerSize.iconSize} color="white" />
                  </Animated.View>
                </Marker>
              );
            })}

            {filteredTomtomIncidents.map((feat, idx) => {
              const mapped = tomtomFeatureToPointAndType(feat);
              if (!mapped) return null;
              const { coord, type, title } = mapped;
              const iconName = getIncidentIcon(type);
              const bg = getIncidentColor(type);
              return (
                <Marker key={`tt-${idx}`} coordinate={coord} title={title}>
                  <Animated.View style={{
                    width: markerSize.size,
                    height: markerSize.size,
                    borderRadius: markerSize.size / 2,
                    justifyContent: 'center',
                    alignItems: 'center',
                    backgroundColor: bg,
                    shadowColor: '#000',
                    shadowOffset: { width: 0, height: 1 },
                    shadowOpacity: 0.25,
                    shadowRadius: 3,
                    elevation: 3,
                    borderColor: '#EF4444',
                    borderWidth: markerSize.borderWidth,
                  }}>
                    <Ionicons name={iconName} size={markerSize.iconSize} color="white" />
                  </Animated.View>
                </Marker>
              );
            })}
          </>
        )}
      </MapView>

      {/* Search Bars */}
      <View style={stylesAbs(theme).searchWrapper}>
        <View style={stylesAbs(theme).searchContainer}>
          <AutocompleteBox
            placeholder="Your location"
            value={originText}
            onChangeText={setOriginText}
            userLocation={userLocation}
            isDestination={false}
            showSeparator={true}
            onPickLocation={(loc) => {
              setOrigin({ latitude: loc.latitude, longitude: loc.longitude });
              setOriginText(loc.name);
            }}
          />
          <AutocompleteBox
            placeholder="Destination"
            value={destText}
            onChangeText={setDestText}
            userLocation={userLocation}
            isDestination={true}
            showSeparator={false}
            onPickLocation={(loc) => {
              setDestination({ latitude: loc.latitude, longitude: loc.longitude });
              setDestText(loc.name);
            }}
          />
        </View>

        {/* Swap Button */}
        <TouchableOpacity 
          style={stylesAbs(theme).swapButton}
          onPress={handleSwapLocations}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Ionicons name="swap-vertical" size={20} color={theme.colors.muted} />
        </TouchableOpacity>

        {/* Incidents toggle pill */}
        <TouchableOpacity
          onPress={() => setShowIncidents(v => !v)}
          style={stylesAbs(theme).incidentsToggle}
        >
          <Ionicons name="warning-outline" size={16} color={showIncidents ? "#B91C1C" : theme.colors.muted} />
          <Text style={[stylesAbs(theme).incidentsText, { color: showIncidents ? theme.colors.text : theme.colors.muted }]}>
            {showIncidents ? "Hide" : "Show"} Incidents
          </Text>
          {incidentsLoading && <ActivityIndicator size="small" style={{ marginLeft: 6 }} />}
        </TouchableOpacity>
      </View>

      {/* Dim backdrop & tap-to-collapse */}
      <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, { backgroundColor: "#000", opacity: backOpacity }]} />
      <Animated.View pointerEvents="auto" style={[StyleSheet.absoluteFill, { opacity: backOpacity }]}>
        <Pressable
          style={{ flex: 1 }}
          onPress={() => {
            opened.current = false;
            Animated.spring(sheetHeight, { toValue: 120, useNativeDriver: false, tension: 160, friction: 22 }).start();
          }}
        />
      </Animated.View>

      {/* Half-screen Bottom Sheet */}
      <Animated.View style={[styles.sheet, { height: sheetHeight }]}>
        <View style={styles.dragArea} {...panResponder.panHandlers}>
          <View style={styles.handle} />
          <View style={styles.headerRow}>
            <Text numberOfLines={1} style={styles.title}>Directions</Text>
            <TouchableOpacity
              style={styles.closeBtn}
              onPress={() => (navigation.canGoBack() ? navigation.goBack() : navigation.navigate("Home"))}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="close" size={20} color={theme.colors.text} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Mode chips */}
        <View style={styles.chipsScroller}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            bounces={false}
            contentContainerStyle={styles.chipsRowContent}
          >
            {Object.entries(MODE_META).map(([key, meta]) => {
              const selected = key === mode;
              const tint = selected ? "#111827" : "#6B7280";
              return (
                <TouchableOpacity
                  key={key}
                  style={[
                    styles.chip,
                    selected && { backgroundColor: meta.color + "22", borderColor: meta.color },
                  ]}
                  onPress={() => setMode(key)}
                  activeOpacity={0.9}
                >
                  <View style={{ width: 8, height: 8, borderRadius: 999, marginRight: 6, backgroundColor: meta.color }} />
                  <Ionicons name={meta.icon} size={13} color={tint} />
                  <Text style={[styles.chipTxt, { color: tint }]}>{meta.label}</Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {/* Departure Recommendation Card (only for driving mode) */}
        {/* REMOVED - Now part of FlatList */}

        {/* Routes list */}
        <View style={styles.listWrap}>
          <FlatList
            data={combinedRoutes}
            keyExtractor={(item, index) => `${item.type}-${index}`}
            showsVerticalScrollIndicator={false}
            renderItem={({ item, index }) => {
              // Departure optimization card
              if (item.type === 'departure') {
                return (
                  <View style={{ marginBottom: 12 }}>
                    <DepartureRecommendationCard
                      result={departureOptimization}
                      loading={departureLoading}
                      error={departureError}
                    />
                  </View>
                );
              }
              
              if (item.type === 'section') {
                return (
                  <Text style={[styles.sectionTitle, index > 0 && { marginTop: 16 }]}>
                    {item.title}
                  </Text>
                );
              }
              if (item.type === 'google') {
                const selected = item.index === activeIndex && !selectedUserRoute;
                return (
                  <TouchableOpacity
                    activeOpacity={0.95}
                    onPress={() => selectRoute(item.index)}
                    style={[
                      styles.routeCard,
                      { borderColor: selected ? (MODE_META[mode]?.color || "#4C8BF5") : "#e5e7eb" },
                    ]}
                  >
                    <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                      {/* Left: title */}
                      <Text style={styles.routeTitle}>{item.data.summary || `Route ${item.index + 1}`}</Text>

                      {/* Right: selected icon + conditional Start */}
                      <View style={styles.startBtnWrap}>
                        {selected ? (
                          <Ionicons name="checkmark-circle" size={18} color={MODE_META[mode]?.color || "#4C8BF5"} />
                        ) : (
                          <Ionicons name="ellipse-outline" size={18} color="#9CA3AF" />
                        )}

                        {/* 🔹 Show Start only when NOT transit (i.e., hide for public transport) */}
                        {mode !== "transit" && (
                          <TouchableOpacity
                            onPress={() => navigation.navigate("NavigationView", { routeData: item.data, mode })}
                            style={{
                              flexDirection: "row",
                              alignItems: "center",
                              paddingHorizontal: 10,
                              paddingVertical: 6,
                              borderRadius: 999,
                              backgroundColor: MODE_META[mode]?.color || "#4C8BF5",
                            }}
                            hitSlop={{ top: 6, bottom: 6, left: 6, right: 6 }}
                          >
                            <Ionicons name="navigate" size={14} color="#fff" />
                            <Text style={{ color: "#fff", fontWeight: "800", marginLeft: 6 }}>Start</Text>
                          </TouchableOpacity>
                        )}
                      </View>
                    </View>

                    <Text style={styles.routeSub}>
                      {item.data.durationText || "--"} · {item.data.distanceText || "--"}
                    </Text>

                    {selected && mode === "transit" && Array.isArray(item.data.steps) && item.data.steps.length > 0 && (
                      <TransitTimeline steps={item.data.steps} theme={theme} />
                    )}
                  </TouchableOpacity>
                );
              }
              if (item.type === 'user') {
                const selected = selectedUserRoute?.id === item.data.id;
                // Always calculate realistic duration based on distance and mode
                const displayDuration = calculateRealisticDuration(item.data.distance, item.data.transport_mode);
                
                return (
                  <TouchableOpacity
                    style={[
                      styles.userRouteCard,
                      selected && { borderColor: getModeColor(item.data.transport_mode), borderWidth: 2 }
                    ]}
                    onPress={() => handleViewUserRoute(item.data)}
                    activeOpacity={0.7}
                  >
                    <View style={[styles.userRouteIcon, { backgroundColor: getModeColor(item.data.transport_mode) + "22" }]}>
                      <Ionicons name={getModeIcon(item.data.transport_mode)} size={18} color={getModeColor(item.data.transport_mode)} />
                    </View>
                    <View style={styles.userRouteInfo}>
                      <Text style={styles.userRouteTitle} numberOfLines={1}>
                        {item.data.title}
                      </Text>
                      <View style={styles.userRouteStats}>
                        <Text style={styles.userRouteStat}>
                          {formatDistance(item.data.distance)} · {formatDuration(displayDuration)}
                        </Text>
                        <View style={{ flexDirection: 'row', alignItems: 'center', marginLeft: 8 }}>
                          <Text style={styles.userRouteStat}>·</Text>
                          <Ionicons name="heart" size={12} color="#EF4444" style={{ marginLeft: 4, marginRight: 2 }} />
                          <Text style={styles.userRouteStat}>{item.data.likes || 0}</Text>
                        </View>
                      </View>
                    </View>
                    <Ionicons name={selected ? "checkmark-circle" : "chevron-forward"} size={18} color={selected ? getModeColor(item.data.transport_mode) : theme.colors.muted} />
                  </TouchableOpacity>
                );
              }
              if (item.type === 'viewMore') {
                return (
                  <TouchableOpacity
                    style={styles.viewMoreButton}
                    onPress={handleViewMoreUserRoutes}
                    activeOpacity={0.7}
                  >
                    <Text style={styles.viewMoreText}>View More Suggested Routes</Text>
                    <Ionicons name="arrow-forward" size={14} color={theme.colors.text} />
                  </TouchableOpacity>
                );
              }
              if (item.type === 'loading') {
                return (
                  <View style={{ paddingVertical: 20, alignItems: "center" }}>
                    <ActivityIndicator size="small" color={MODE_META[mode]?.color || "#4C8BF5"} />
                  </View>
                );
              }
              if (item.type === 'empty') {
                return (
                  <Text style={{ color: theme.colors.muted, fontSize: 12, textAlign: "center", paddingVertical: 12 }}>
                    {item.message}
                  </Text>
                );
              }
              
              // Carpark button
              if (item.type === 'carpark') {
                return (
                  <NearestCarparkButton
                    origin={origin}
                    destination={destination}
                    destText={destText}
                    onPress={() => {
                      navigation.navigate("TransportDetails", {
                        origin,
                        destination: destText,
                        coordinates: destination,
                        mode: "Driving",
                        findCarpark: true,
                      });
                    }}
                  />
                );
              }
              
              return null;
            }}
            contentContainerStyle={{ paddingBottom: 12 }}
          />
        </View>
      </Animated.View>
    </View>
  );
}

const stylesAbs = (theme) =>
  StyleSheet.create({
    searchWrapper: {
      position: "absolute",
      top: 60,
      left: 12,
      right: 12,
      zIndex: 20,
    },
    searchContainer: {
      width: "100%",
      backgroundColor: theme.colors.card,
      borderRadius: 24,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.colors.border,
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 6 },
      shadowOpacity: 0.1,
      shadowRadius: 12,
      elevation: 6,
      overflow: "visible",
    },
    swapButton: {
      position: "absolute",
      bottom: -48,
      left: 0,
      width: 36,
      height: 36,
      borderRadius: 18,
      backgroundColor: theme.colors.card,
      alignItems: "center",
      justifyContent: "center",
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 4,
      elevation: 4,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.colors.border,
    },
    inputWrap: {
      flexDirection: "row",
      alignItems: "center",
      paddingHorizontal: 14,
      paddingVertical: 6,
      minHeight: 50,
    },
    separator: {
      height: 1,
      backgroundColor: theme.colors.border,
      marginLeft: 60,
      marginRight: 14,
    },
    iconCircle: {
      width: 36, height: 36, borderRadius: 18, backgroundColor: "#E8F0FE",
      alignItems: "center", justifyContent: "center", marginRight: 10,
    },
    input: { flex: 1, paddingVertical: 6, fontSize: 15, fontWeight: "400", letterSpacing: 0.2 },
    dropdown: {
      marginTop: 6,
      maxHeight: height * 0.28,
      borderRadius: 14,
      overflow: "hidden",
      borderWidth: StyleSheet.hairlineWidth,
    },
    row: {
      paddingHorizontal: 14,
      paddingVertical: 12,
      flexDirection: "row",
      alignItems: "center",
      gap: 8,
    },
    incidentsToggle: {
      position: "absolute",
      right: 0,
      bottom: -48,
      height: 36,
      borderRadius: 18,
      paddingHorizontal: 12,
      backgroundColor: theme.colors.card,
      alignItems: "center",
      justifyContent: "center",
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.colors.border,
      flexDirection: "row",
      gap: 6,
    },
    incidentsText: {
      fontWeight: "700",
    },
  });

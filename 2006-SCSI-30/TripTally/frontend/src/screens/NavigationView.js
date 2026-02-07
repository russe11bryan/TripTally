import React, { useEffect, useRef, useState, useCallback } from "react";
import { View, Text, TouchableOpacity, StyleSheet, Platform } from "react-native";
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from "react-native-maps";
import * as Location from "expo-location";
import Ionicons from "@expo/vector-icons/Ionicons";
import polyline from "@mapbox/polyline";
import useThemedStyles from "../hooks/useThemedStyles";

/* ---------------- Distance helpers ---------------- */
function haversineMeters(p1, p2) {
  if (!p1 || !p2 || !isFinite(p1.latitude) || !isFinite(p1.longitude) || !isFinite(p2.latitude) || !isFinite(p2.longitude)) {
    return NaN;
  }
  const R = 6371e3;
  const φ1 = (p1.latitude * Math.PI) / 180;
  const φ2 = (p2.latitude * Math.PI) / 180;
  const Δφ = ((p2.latitude - p1.latitude) * Math.PI) / 180;
  const Δλ = ((p2.longitude - p1.longitude) * Math.PI) / 180;
  const a = Math.sin(Δφ / 2) ** 2 + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function fmtDist(m) {
  if (!isFinite(m)) return "—";
  if (m >= 1000) return `${(m / 1000).toFixed(1)} km`;
  return `${Math.round(m)} m`;
}

function decodePoints(enc) {
  if (!enc || typeof enc !== "string") return [];
  try {
    return polyline.decode(enc).map(([lat, lng]) => ({ latitude: lat, longitude: lng }));
  } catch {
    return [];
  }
}

function stepEndCoord(step) {
  const end = step?.end_location || step?.end;
  if (end && isFinite(end.latitude) && isFinite(end.longitude)) return end;
  const enc = step?.polyline?.points || step?.polyline || step?.encoded_polyline || step?.points;
  const pts = decodePoints(enc);
  return pts.length > 0 ? pts[pts.length - 1] : null;
}

/* ---------------- Map constants ---------------- */
const AUTO_RECENTER_TIMEOUT = 10000;
const FOLLOW_ZOOM = 18;
const FOLLOW_PITCH = 30;

export default function NavigationView({ route, navigation }) {
  const { routeData, mode } = route.params;
  const { styles, theme } = useThemedStyles(createStyles);
  const mapRef = useRef(null);
  const [location, setLocation] = useState(null);
  const [heading, setHeading] = useState(0);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const idleTimer = useRef(null);

  const color =
    mode === "driving" ? "#4C8BF5" : mode === "walking" ? "#2BB673" : "#F4B400";

  const destination =
    routeData?.coords?.length > 0
      ? routeData.coords[routeData.coords.length - 1]
      : null;

  const steps = Array.isArray(routeData?.steps) ? routeData.steps : [];
  const currentStep = steps[currentStepIndex] || {};
  const nextStep = steps[currentStepIndex + 1];

  const animateToUser = useCallback(
    (coords) => {
      if (!coords || !mapRef.current) return;
      mapRef.current.animateCamera(
        {
          center: { latitude: coords.latitude, longitude: coords.longitude },
          pitch: FOLLOW_PITCH,
          heading: Number.isFinite(coords.heading) ? coords.heading : heading,
          zoom: FOLLOW_ZOOM,
        },
        { duration: 700 }
      );
    },
    [heading]
  );

  const resetIdleTimer = useCallback(() => {
    if (idleTimer.current) clearTimeout(idleTimer.current);
    idleTimer.current = setTimeout(() => {
      if (location) animateToUser(location);
    }, AUTO_RECENTER_TIMEOUT);
  }, [location, animateToUser]);

  /* ---------------- Live tracking ---------------- */
  useEffect(() => {
    let posWatcher = null;
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") return;

      const loc = await Location.getCurrentPositionAsync({});
      setLocation(loc.coords);
      setHeading(loc.coords.heading || 0);
      animateToUser(loc.coords);

      posWatcher = await Location.watchPositionAsync(
        { accuracy: Location.Accuracy.High, timeInterval: 2000, distanceInterval: 5 },
        (locUpdate) => {
          const coords = locUpdate.coords;
          setLocation(coords);
          setHeading(coords.heading || heading);

          if (steps.length > 0) {
            const userPt = { latitude: coords.latitude, longitude: coords.longitude };
            let bestIdx = 0;
            let best = Infinity;
            for (let i = 0; i < steps.length; i++) {
              const end = stepEndCoord(steps[i]);
              const d = end ? haversineMeters(userPt, end) : Infinity;
              if (d < best) {
                best = d;
                bestIdx = i;
              }
            }
            setCurrentStepIndex(bestIdx);
          }
        }
      );
    })();

    return () => {
      if (posWatcher) posWatcher.remove();
      if (idleTimer.current) clearTimeout(idleTimer.current);
    };
  }, [animateToUser, steps, heading]);

  /* ---------------- Distance to current instruction ---------------- */
  let liveMeters = NaN;
  if (location && currentStep) {
    const end = stepEndCoord(currentStep);
    if (end) {
      liveMeters = haversineMeters(
        { latitude: location.latitude, longitude: location.longitude },
        end
      );
    }
  }
  const liveDistanceText = fmtDist(liveMeters);

  /* ---------------- Render ---------------- */
  return (
    <View style={{ flex: 1 }}>
      <MapView
        ref={mapRef}
        provider={PROVIDER_GOOGLE}
        style={{ flex: 1 }}
        mapType="mutedStandard"
        showsUserLocation
        pitchEnabled
        showsMyLocationButton={false}
        onPanDrag={resetIdleTimer}
        onRegionChangeComplete={resetIdleTimer}
      >
        {routeData?.coords?.length > 0 && (
          <Polyline coordinates={routeData.coords} strokeColor={color} strokeWidth={6} />
        )}
        {destination && (
          <Marker coordinate={destination} title="Destination" pinColor="red" />
        )}
      </MapView>

      {/* --- Header banner --- */}
      <View style={styles.banner}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.bannerBack}>
          <Ionicons name="arrow-back" size={20} color={theme.colors.text} />
        </TouchableOpacity>

        <View style={{ flex: 1, marginLeft: 10 }}>
          <Text style={styles.bannerDistance}>{liveDistanceText}</Text>
          <Text style={styles.bannerTitle} numberOfLines={2}>
            {currentStep?.instruction || "Continue straight"}
          </Text>

          {nextStep?.instruction ? (
            <Text style={styles.thenText} numberOfLines={1}>
              Then: {nextStep.instruction}
            </Text>
          ) : null}
        </View>
      </View>

      {/* --- Bottom ETA + Re-centre --- */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={styles.recenter}
          onPress={() => location && animateToUser(location)}
        >
          <Ionicons name="locate" size={18} color={theme.colors.text} />
          <Text style={styles.recenterText}>Re-centre</Text>
        </TouchableOpacity>

        <View style={styles.stats}>
          <Text style={styles.statsText}>
            ETA {routeData?.durationText || "—"} · {routeData?.distanceText || "—"}
          </Text>
        </View>
      </View>
    </View>
  );
}

/* ---------------- Styles ---------------- */
const createStyles = ({ colors }) =>
  StyleSheet.create({
    banner: {
      position: "absolute",
      top: 0,
      left: 0,
      right: 0,
      paddingTop: Platform.select({ ios: 40, android: 18 }),
      paddingBottom: 10,
      paddingHorizontal: 14,
      backgroundColor: colors.text,
      flexDirection: "row",
      alignItems: "center",
      zIndex: 6,
    },
    bannerBack: {
      backgroundColor: colors.card,
      width: 34,
      height: 34,
      borderRadius: 17,
      alignItems: "center",
      justifyContent: "center",
    },
    bannerDistance: { 
      color: colors.muted, 
      fontWeight: "700", 
      fontSize: 13 
    },
    bannerTitle: { 
      color: colors.background, 
      fontWeight: "800", 
      fontSize: 18, 
      marginTop: 2 
    },
    thenText: { 
      color: colors.muted, 
      marginTop: 4, 
      fontSize: 12, 
      fontWeight: "600" 
    },
    bottomBar: {
      position: "absolute",
      bottom: 0,
      left: 0,
      right: 0,
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      backgroundColor: colors.card,
      paddingHorizontal: 20,
      paddingVertical: 14,
      borderTopWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    recenter: {
      flexDirection: "row",
      alignItems: "center",
      backgroundColor: colors.background,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 20,
    },
    recenterText: {
      marginLeft: 6,
      color: colors.text,
    },
    stats: { 
      alignItems: "flex-end" 
    },
    statsText: { 
      fontWeight: "700", 
      fontSize: 14, 
      color: colors.text 
    },
  });

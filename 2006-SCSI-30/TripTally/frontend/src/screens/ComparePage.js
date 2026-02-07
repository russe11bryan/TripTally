// src/screens/ComparePage.js
import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Alert,
  Dimensions,
  Platform,
  StyleSheet as RNStyleSheet,
  Keyboard,
} from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import * as Location from 'expo-location';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useRoute } from '@react-navigation/native';
import useThemedStyles from '../hooks/useThemedStyles';
import TransportCard from '../components/TransportCard';
import BottomDragTab from '../components/BottomDragTab';
import AutocompleteBox from '../components/AutocompleteBox';
import { BASE_URL } from '../config/keys';

const { height } = Dimensions.get('window');

const API_BASE =
  BASE_URL ||
  (Platform.OS === "android" ? "http://10.0.2.2:8080" : "http://localhost:8080");

/* ---------------- helpers (unchanged) ---------------- */
const fmtDuration = (secs) => {
  if (secs == null || isNaN(secs)) return null;
  const m = Math.round(secs / 60);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const r = m % 60;
  return r ? `${h} h ${r} min` : `${h} h`;
};
const fmtDistance = (m) => {
  if (m == null || isNaN(m)) return null;
  return m < 1000 ? `${Math.round(m)} m` : `${(m / 1000).toFixed(1)} km`;
};
const shortenTime = (timeStr) => {
  if (!timeStr || timeStr === "--") return timeStr;
  // Replace "hour" or "hours" with " h", "hr" with " h", "mins" with "min"
  return timeStr
    .replace(/\s*hours?\s*/gi, " h ")
    .replace(/\s*hr\s*/gi, " h ")
    .replace(/\s*mins\s*/gi, " min ")
    .replace(/(\d)h\s*/gi, "$1 h ")  // Ensure space between digit and h
    .trim();
};
const parseDirections = (data) => {
  const r0 = Array.isArray(data?.routes) ? data.routes[0] : null;
  const leg =
    (Array.isArray(r0?.legs) && r0.legs[0]) ||
    (Array.isArray(data?.legs) && data.legs[0]) ||
    null;
  const textDur =
    leg?.duration?.text ??
    data?.duration_text ??
    r0?.duration_text ??
    data?.duration ??
    null;
  const textDist =
    leg?.distance?.text ??
    data?.distance_text ??
    r0?.distance_text ??
    data?.distance ??
    null;
  const numDur =
    leg?.duration_in_traffic?.value ??
    leg?.duration?.value ??
    data?.duration_seconds ??
    r0?.duration_seconds ??
    null;
  const numDist =
    leg?.distance?.value ??
    data?.distance_meters ??
    r0?.distance_meters ??
    null;
  const duration =
    (typeof textDur === "string" && textDur) ||
    (numDur != null && fmtDuration(numDur)) ||
    "--";
  const distance =
    (typeof textDist === "string" && textDist) ||
    (numDist != null && fmtDistance(numDist)) ||
    "--";
  return { duration, distance };
};

/* -------------------- page -------------------- */

function ComparePage({ navigation }) {
  const route = useRoute();
  const passedDest = route.params?.destination; // { name, latitude, longitude }
  const { styles, theme } = useThemedStyles(({ colors }) => ({
    container: { flex: 1 },
    searchWrapper: {
      position: "absolute",
      top: 60,
      left: 12,
      right: 12,
      zIndex: 20,
    },
    searchContainer: {
      width: "100%",
      backgroundColor: "rgba(255,255,255,0.96)",
      borderRadius: 24,
      borderWidth: RNStyleSheet.hairlineWidth,
      borderColor: "#e6e6e6",
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 6 },
      shadowOpacity: 0.1,
      shadowRadius: 12,
      elevation: 6,
      overflow: "visible",
    },
    grid: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between" },
    headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 12 },
    headerTitle: { fontSize: 16, fontWeight: "700", color: colors.text },
    subheader: { fontSize: 12, color: colors.muted, marginTop: 2 },
    roundButton: {
      width: 32,
      height: 32,
      borderRadius: 16,
      backgroundColor: colors.pill,
      alignItems: "center",
      justifyContent: "center",
      borderWidth: RNStyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
  }));

  const mapRef = useRef(null);
  const didInitialZoom = useRef(false); // <-- NEW: ensure we zoom exactly once to the passed destination

  // origin
  const [origin, setOrigin] = useState(null);
  const [originText, setOriginText] = useState("Your Location");

  // destination (default from SearchPage)
  const [destination, setDestination] = useState(
    passedDest?.latitude && passedDest?.longitude
      ? { latitude: passedDest.latitude, longitude: passedDest.longitude }
      : null
  );
  const [destText, setDestText] = useState(passedDest?.name || "");

  // metrics for each mode
  const [metrics, setMetrics] = useState({
    driving: { time: "--", distance: "--" },
    transit: { time: "--", distance: "--" },
    walking: { time: "--", distance: "--" },
    bicycling: { time: "--", distance: "--" },
  });

  // get user location once
  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") return;
      const loc = await Location.getCurrentPositionAsync({});
      setOrigin({ latitude: loc.coords.latitude, longitude: loc.coords.longitude });
    })();
  }, []);

  // ---- NEW: initial zoom to destination passed from SearchPage
  useEffect(() => {
    if (!mapRef.current || !destination || didInitialZoom.current) return;
    didInitialZoom.current = true;
    mapRef.current.animateToRegion(
      {
        latitude: destination.latitude,
        longitude: destination.longitude,
        latitudeDelta: 0.03,
        longitudeDelta: 0.03,
      },
      800
    );
  }, [destination]);

  // when both points are known later, fit both nicely
  useEffect(() => {
    if (!mapRef.current || !origin || !destination) return;
    mapRef.current.fitToCoordinates([origin, destination], {
      edgePadding: { top: 100, right: 80, bottom: 340, left: 80 },
      animated: true,
    });
  }, [origin, destination]);

      // fetch metrics whenever points change
  useEffect(() => {
    const fetchAll = async () => {
      if (!origin || !destination) return;
      const modes = ["driving", "transit", "walking", "bicycling"];
      const next = {};

      try {
        await Promise.all(
          modes.map(async (m) => {
            try {
              // Get route details
              const routeUrl =
                `${API_BASE}/maps/directions?origin=${origin.latitude},${origin.longitude}` +
                `&destination=${destination.latitude},${destination.longitude}&mode=${m}`;
              const routeRes = await fetch(routeUrl, { headers: { Accept: "application/json" } });
              if (!routeRes.ok) throw new Error(`HTTP ${routeRes.status}`);
              const routeData = await routeRes.json();
              const { duration, distance } = parseDirections(routeData);
              
              if (m === "driving" || m === "transit") {
                try {
                  const distanceKm = parseFloat((distance || "").replace(/[^\d.]/g, "")) || 0;
                  const polyline = routeData?.routes?.[0]?.overview_polyline?.points || 
                                routeData?.routes?.[0]?.encoded_polyline ||
                                routeData?.overview_polyline?.points || "";
                  
                  const metricsUrl = `${API_BASE}/metrics/compare?` +
                    `distance_km=${distanceKm}&` +
                    `route_polyline=${encodeURIComponent(polyline)}&` +
                    `origin=${origin.latitude},${origin.longitude}&` +
                    `destination=${destination.latitude},${destination.longitude}&` +
                    `fare_category=adult_card_fare`;
                  
                  console.log('Fetching metrics:', metricsUrl);
                  const metricsRes = await fetch(metricsUrl);
                  const metricsText = await metricsRes.text();
                  
                  if (!metricsRes.ok) {
                    console.error('Metrics API error:', metricsText);
                    throw new Error(`HTTP ${metricsRes.status}: ${metricsText}`);
                  }
                  
                  let metricsData;
                  try {
                    metricsData = JSON.parse(metricsText);
                    console.log('Metrics response:', JSON.stringify(metricsData, null, 2));
                  } catch (e) {
                    console.error('Failed to parse metrics response:', metricsText);
                    throw new Error('Invalid JSON response from metrics API');
                  }

                  if (m === "driving" && metricsData?.driving) {
                    const driving = metricsData.driving;
                    next[m] = {
                      time: shortenTime(duration) || "--",
                      distance: distance || "--",
                      cost: driving.total_cost != null ? `$${driving.total_cost.toFixed(2)}` : "--",
                      co2: driving.co2_emissions_kg != null ? `${driving.co2_emissions_kg.toFixed(2)} kg` : "--",
                      fuel_cost: driving.fuel_cost_sgd != null ? `$${driving.fuel_cost_sgd.toFixed(2)}` : "--",
                      erp_charges: driving.erp_charges != null ? `$${driving.erp_charges.toFixed(2)}` : "--"
                    };
                  } else if (m === "transit" && metricsData?.public_transport) {
                    const pt = metricsData.public_transport;
                    const totalFare = pt.total_fare != null ? parseFloat(pt.total_fare) : null;
                    const mrtFare = pt.mrt_fare != null ? parseFloat(pt.mrt_fare) : null;
                    const busFare = pt.bus_fare != null ? parseFloat(pt.bus_fare) : null;
                    
                    next[m] = {
                      time: shortenTime(duration) || "--",
                      distance: distance || "--",
                      cost: totalFare != null ? `$${totalFare.toFixed(2)}` : "--",
                      co2: "0 kg",  // Public transport CO2 emissions considered negligible per passenger
                      mrt_fare: mrtFare != null ? `$${mrtFare.toFixed(2)}` : "--",
                      bus_fare: busFare != null ? `$${busFare.toFixed(2)}` : "--",
                      total_fare: totalFare != null ? `$${totalFare.toFixed(2)}` : "--"
                    };
                  }
                } catch (metricsError) {
                  console.error("Metrics fetch error:", metricsError);
                  next[m] = {
                    time: shortenTime(duration) || "--",
                    distance: distance || "--",
                    cost: "--",
                    co2: "--"
                  };
                }
              } else {
                // For walking and cycling, just use route data
                next[m] = {
                  time: shortenTime(duration) || "--",
                  distance: distance || "--",
                  cost: "Free",
                  co2: "0 kg"
                };
              }
            } catch (error) {
              console.error(`Error fetching ${m} route:`, error);
              next[m] = {
                time: "--",
                distance: "--",
                cost: "--",
                co2: "--"
              };
            }
          })
        );
        setMetrics(next);
      } catch (error) {
        console.error("Error in fetchAll:", error);
      }
    };
    fetchAll();
  }, [origin, destination]);

  return (
    <View style={styles.container}>
      {/* Map */}
      <MapView
        ref={mapRef}
        provider={PROVIDER_GOOGLE}
        style={RNStyleSheet.absoluteFillObject}
        showsUserLocation
        showsMyLocationButton
        initialRegion={{
          // if we already have a destination from SearchPage, start centered THERE
          latitude: destination?.latitude ?? origin?.latitude ?? 1.3521,
          longitude: destination?.longitude ?? origin?.longitude ?? 103.8198,
          latitudeDelta: destination ? 0.03 : 0.08,  // tighter zoom if dest is known
          longitudeDelta: destination ? 0.03 : 0.08,
        }}
      >
        {origin && <Marker coordinate={origin} pinColor="blue" title={originText || "Origin"} />}
        {destination && <Marker coordinate={destination} title={destText || "Destination"} />}
      </MapView>

      {/* Search bars - wrapped in container like DirectionsPage */}
      <View style={styles.searchWrapper}>
        <View style={styles.searchContainer}>
          <AutocompleteBox
            placeholder="Origin (Your Location)"
            value={originText}
            onChangeText={setOriginText}
            onPickLocation={(loc) => {
              setOrigin({ latitude: loc.latitude, longitude: loc.longitude });
              setOriginText(loc.name);
            }}
            userLocation={origin}
            isDestination={false}
            showSeparator={true}
          />
          <AutocompleteBox
            placeholder="Destination"
            value={destText}
            onChangeText={setDestText}
            onPickLocation={(loc) => {
              setDestination({ latitude: loc.latitude, longitude: loc.longitude });
              setDestText(loc.name);
              // also zoom when user changes destination here
              mapRef.current?.animateToRegion(
                { latitude: loc.latitude, longitude: loc.longitude, latitudeDelta: 0.03, longitudeDelta: 0.03 },
                700
              );
            }}
            userLocation={origin}
            isDestination={true}
            showSeparator={false}
          />
        </View>
      </View>

      {/* Bottom sheet + cards (unchanged UI) */}
      <BottomDragTab
        expanded={true}
        initialPosition={260}
        collapsedHeight={70}
        maxHeightRatio={0.62}
        maxHeight={600}
      >
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.headerTitle}>{destText || "Compare Routes"}</Text>
            <Text style={styles.subheader}>Compare travel times by mode</Text>
          </View>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.roundButton}>
            <Ionicons name="close" size={18} color={theme.colors.text} />
          </TouchableOpacity>
        </View>

        <View style={styles.grid}>
          {[
            { key: "driving", icon: "car", title: "Driving" },
            { key: "transit", icon: "train", title: "Public Transport" },
            { key: "walking", icon: "walk", title: "Walking" },
            { key: "bicycling", icon: "bicycle", title: "Cycling" },
          ].map((mode) => {
            const metric = metrics[mode.key] || {};
            return (
              <TransportCard
                key={mode.key}
                icon={mode.icon}
                title={mode.title}
                time={metric.time ?? "--"}
                distance={metric.distance ?? "--"}
                cost={metric.cost ?? "--"}
                co2={metric.co2 ?? "--"}
                onPress={() => {
                  if (!origin) {
                    Alert.alert(
                      "Location Required",
                      "Please allow access to your location or set a starting point to view detailed metrics.",
                      [{ text: "OK" }]
                    );
                    return;
                  }
                  if (!destination) {
                    Alert.alert(
                      "Destination Required",
                      "Please set a destination to view detailed metrics.",
                      [{ text: "OK" }]
                    );
                    return;
                  }
                  navigation.navigate("TransportDetails", {
                    mode: mode.title,
                    destination: destText,
                    metrics: metric,
                    coordinates: { latitude: destination.latitude, longitude: destination.longitude },
                    origin: { latitude: origin.latitude, longitude: origin.longitude }
                  });
                }}
              />
            );
          })}
        </View>
      </BottomDragTab>
    </View>
  );
}

export default ComparePage;




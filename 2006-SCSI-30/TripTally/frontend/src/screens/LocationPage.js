// src/screens/LocationPage.js
import React, { useEffect, useMemo, useState, useRef } from "react";
import {
 View,
 Text,
 TouchableOpacity,
 ActivityIndicator,
 Alert,
 StyleSheet,
 Dimensions,
 Image,       // ✅ for photos
 Platform,    // ✅ for API_BASE
 FlatList,    // ✅ horizontal strip
 Animated,
 PanResponder,
} from "react-native";
import { useRoute, useNavigation } from "@react-navigation/native";
import * as Location from "expo-location";
import MapView, { Marker, PROVIDER_GOOGLE } from "react-native-maps";
import Ionicons from "@expo/vector-icons/Ionicons";
import useThemedStyles from "../hooks/useThemedStyles";
import { BASE_URL } from "../config/keys";
import NearestCarparkButton from "../components/NearestCarparkButton";


const { height } = Dimensions.get("window");


// base URL (same pattern as SearchPage)
const DEV_ANDROID = "http://10.0.2.2:8080";
const DEV_IOS = "http://localhost:8080";
const DEV_DEVICE = "http://192.168.10.131:8080";
const USE_DEVICE = true;
const API_BASE =
 BASE_URL ||
 (__DEV__
   ? USE_DEVICE
     ? DEV_DEVICE
     : Platform.OS === "android"
       ? DEV_ANDROID
       : DEV_IOS
   : "https://your-prod-domain.com");


// build photo URL from photo_reference
function getPhotoUrl(photoRef, maxwidth = 800) {
 if (!photoRef) return null;
 return `${API_BASE}/maps/photos?photo_reference=${encodeURIComponent(photoRef)}&maxwidth=${maxwidth}`;
}


export default function LocationPage() {
 const navigation = useNavigation();
 const route = useRoute();


 const placeParam = route.params?.place || route.params || {};
 const place = {
   name: placeParam.name,
   latitude: Number(placeParam.latitude),
   longitude: Number(placeParam.longitude),
   address: placeParam.address,
   placeId: placeParam.placeId || placeParam.place_id || null,
 };

 // Extract just the main title (first part before comma) for the heading
 // Show remaining parts as address
 const getPlaceInfo = (fullName) => {
   if (!fullName) return { title: "Selected place", addressPart: "" };
   const parts = fullName.split(',');
   if (parts.length > 1) {
     return {
       title: parts[0].trim(),
       addressPart: parts.slice(1).join(',').trim()
     };
   }
   return { title: fullName, addressPart: "" };
 };

 const { title: placeTitle, addressPart } = getPlaceInfo(place.name);


 const { styles, theme } = useThemedStyles(({ colors }) => ({
   root: { flex: 1, backgroundColor: colors.background },
   header: {
     paddingTop: 56,
     paddingHorizontal: 16,
     paddingBottom: 12,
     borderBottomWidth: StyleSheet.hairlineWidth,
     borderBottomColor: colors.border,
     backgroundColor: colors.background,
     flexDirection: "row",
     alignItems: "center",
     justifyContent: "space-between",
     position: 'absolute',
     top: 0,
     left: 0,
     right: 0,
     zIndex: 10,
   },
   back: { fontSize: 18, color: colors.text },
   titleWrap: { alignItems: "center", flex: 1 },
   title: { fontWeight: "800", color: colors.text },
   map: { flex: 1 },
   sheet: {
     position: "absolute",
     left: 0,
     right: 0,
     bottom: 0,
     backgroundColor: colors.background,
     borderTopLeftRadius: 20,
     borderTopRightRadius: 20,
     borderWidth: StyleSheet.hairlineWidth,
     borderColor: colors.border,
     shadowColor: "#000",
     shadowOffset: { width: 0, height: -2 },
     shadowOpacity: 0.1,
     shadowRadius: 8,
     elevation: 5,
   },
   dragHandle: {
     width: 40,
     height: 5,
     backgroundColor: colors.muted,
     borderRadius: 3,
     alignSelf: "center",
     marginTop: 8,
     marginBottom: 12,
   },
   card: {
     marginHorizontal: 16,
     marginBottom: 16,
     padding: 14,
     borderRadius: 16,
     backgroundColor: colors.card,
     borderWidth: 1,
     borderColor: colors.border,
   },
   name: { fontWeight: "800", fontSize: 16, color: colors.text },
   coords: { marginTop: 4, color: colors.muted, fontSize: 12 },
   actionsRow: { flexDirection: "row", marginTop: 12, justifyContent: "space-between", gap: 8 },
   actionBtn: {
     flex: 1,
     backgroundColor: colors.pill,
     paddingVertical: 14,
     borderRadius: 12,
     alignItems: "center",
     justifyContent: "center",
     flexDirection: "row",
     gap: 6,
   },
   actionTxt: { color: colors.text, fontWeight: "700" },
   muted: { color: colors.muted },
   loadingWrap: { flex: 1, alignItems: "center", justifyContent: "center" },
   photoItem: {           // ✅ each strip image
     width: 260,
     height: 160,
     borderRadius: 12,
     backgroundColor: "#eee",
   },
 }));


 const [origin, setOrigin] = useState(null);
 const [gettingLoc, setGettingLoc] = useState(true);
 const [photoUrls, setPhotoUrls] = useState([]); // ✅ multiple photos
 const [fetchedAddress, setFetchedAddress] = useState(null); // ✅ address from API

 // Bottom sheet animation
 const SHEET_MIN_HEIGHT = 150; // Lower minimum to show just name and 2 buttons
 const SHEET_MAX_HEIGHT = height * 0.7;
 const sheetHeight = useRef(new Animated.Value(SHEET_MIN_HEIGHT)).current;
 const lastHeight = useRef(SHEET_MIN_HEIGHT);

 const panResponder = useRef(
   PanResponder.create({
     onStartShouldSetPanResponder: () => true,
     onPanResponderMove: (_, gesture) => {
       const newHeight = lastHeight.current - gesture.dy;
       if (newHeight >= SHEET_MIN_HEIGHT && newHeight <= SHEET_MAX_HEIGHT) {
         sheetHeight.setValue(newHeight);
       }
     },
     onPanResponderRelease: (_, gesture) => {
       const newHeight = lastHeight.current - gesture.dy;
       
       // Clamp to min/max bounds but don't snap
       if (newHeight < SHEET_MIN_HEIGHT) {
         lastHeight.current = SHEET_MIN_HEIGHT;
         Animated.spring(sheetHeight, {
           toValue: SHEET_MIN_HEIGHT,
           useNativeDriver: false,
         }).start();
       } else if (newHeight > SHEET_MAX_HEIGHT) {
         lastHeight.current = SHEET_MAX_HEIGHT;
         Animated.spring(sheetHeight, {
           toValue: SHEET_MAX_HEIGHT,
           useNativeDriver: false,
         }).start();
       } else {
         // Stay at the released position
         lastHeight.current = newHeight;
       }
     },
   })
 ).current;

 // Get current user location
 useEffect(() => {
   (async () => {
     try {
       const { status } = await Location.requestForegroundPermissionsAsync();
       if (status !== "granted") {
         Alert.alert("Location permission denied", "We need your location to start directions.");
         setGettingLoc(false);
         return;
       }
       const cur = await Location.getCurrentPositionAsync({
         accuracy: Location.Accuracy.Balanced,
       });
       setOrigin({ latitude: cur.coords.latitude, longitude: cur.coords.longitude });
     } catch (e) {
       console.warn("Location error:", e);
       Alert.alert("Location error", String(e?.message || e));
     } finally {
       setGettingLoc(false);
     }
   })();
 }, []);


 // Fetch multiple photos and address via place-details
 useEffect(() => {
   let cancelled = false;
   (async () => {
     try {
       if (!place?.placeId) return;
       const url = `${API_BASE}/maps/place-details?place_id=${encodeURIComponent(place.placeId)}`;
       const res = await fetch(url);
       if (!res.ok) return;
       const data = await res.json();
       
       // Extract photos
       const photos = Array.isArray(data?.photos) ? data.photos : [];
       const urls = photos
         .slice(0, 8) // limit to 8
         .map(p => p?.photo_reference)
         .filter(Boolean)
         .map(ref => getPhotoUrl(ref, 800));
       
       // Extract address
       const address = data?.formatted_address || data?.vicinity || null;
       
       if (!cancelled) {
         setPhotoUrls(urls);
         setFetchedAddress(address);
       }
     } catch (err) {
       console.warn("place-details (photos & address) error:", err);
     }
   })();
   return () => { cancelled = true; };
 }, [place?.placeId]);


 const region = useMemo(
   () => ({
     latitude: place?.latitude || 1.3521,
     longitude: place?.longitude || 103.8198,
     latitudeDelta: 0.01,
     longitudeDelta: 0.01,
   }),
   [place?.latitude, place?.longitude]
 );


 const goDirections = () => {
   if (!origin) {
     Alert.alert("Location not ready", "Still getting your current location.");
     return;
   }
   navigation.navigate("Directions", {
     origin,
     destination: {
       name: place.name || "Destination",
       latitude: place.latitude,
       longitude: place.longitude,
     },
     initialMode: "driving", // default mode
   });
 };


 const goCompare = () => {
   navigation.navigate("Compare", { destination: place });
 };


 const goSave = () => {
   navigation.navigate("SelectList", { place });
 };


 if (!place?.latitude || !place?.longitude) {
   return (
     <View style={styles.loadingWrap}>
       <Text style={styles.muted}>No place data was provided.</Text>
     </View>
   );
 }


 return (
   <View style={styles.root}>
     {/* Header */}
     <View style={styles.header}>
       <TouchableOpacity onPress={() => navigation.goBack()}>
         <Text style={styles.back}>← Back</Text>
       </TouchableOpacity>
       <View style={styles.titleWrap}>
         <Text style={styles.title}>Location</Text>
       </View>
       <View style={{ width: 52 }} />
     </View>


     {/* Map - Full Screen */}
     <MapView
       provider={PROVIDER_GOOGLE}
       style={styles.map}
       initialRegion={region}
       showsUserLocation
       showsMyLocationButton={false}
     >
       <Marker
         coordinate={{ latitude: place.latitude, longitude: place.longitude }}
         title={place.name || "Destination"}
       />
     </MapView>


     {/* Bottom Drag Sheet */}
     <Animated.View style={[styles.sheet, { height: sheetHeight }]}>
       {/* Drag Handle */}
       <View {...panResponder.panHandlers}>
         <View style={styles.dragHandle} />
       </View>

       {/* Compact View - Always Visible */}
       <View style={{ paddingHorizontal: 16, paddingBottom: 12 }}>
         <Text style={styles.name} numberOfLines={1}>{placeTitle}</Text>
         {(fetchedAddress || place.address || addressPart) ? (
           <Text style={styles.coords} numberOfLines={2}>
             {fetchedAddress || place.address || addressPart}
           </Text>
         ) : null}

         {/* All 3 Action Buttons Row */}
         <View style={styles.actionsRow}>
           <TouchableOpacity
             style={styles.actionBtn}
             onPress={goDirections}
             disabled={gettingLoc}
           >
             {gettingLoc ? (
               <ActivityIndicator color={theme.colors.text} size="small" />
             ) : (
               <>
                 <Ionicons name="navigate" size={16} color={theme.colors.text} />
                 <Text style={styles.actionTxt}>Directions</Text>
               </>
             )}
           </TouchableOpacity>

           <TouchableOpacity style={styles.actionBtn} onPress={goCompare}>
             <Ionicons name="swap-horizontal" size={16} color={theme.colors.text} />
             <Text style={styles.actionTxt}>Compare</Text>
           </TouchableOpacity>

           <TouchableOpacity style={styles.actionBtn} onPress={goSave}>
             <Ionicons name="bookmark" size={16} color={theme.colors.text} />
             <Text style={styles.actionTxt}>Save</Text>
           </TouchableOpacity>
         </View>
       </View>

       {/* Scrollable Extended Content */}
       <FlatList
         data={[{ key: 'content' }]}
         renderItem={() => (
           <View style={{ paddingBottom: 20 }}>
             {/* ✅ Horizontal photo strip (if any) */}
             {photoUrls.length > 0 && (
               <View style={{ paddingHorizontal: 16, marginBottom: 16 }}>
                 <FlatList
                   data={photoUrls}
                   keyExtractor={(uri, idx) => `${uri}-${idx}`}
                   horizontal
                   showsHorizontalScrollIndicator={false}
                   contentContainerStyle={{ gap: 10 }}
                   renderItem={({ item }) => (
                     <Image
                       source={{ uri: item }}
                       style={styles.photoItem}
                       resizeMode="cover"
                     />
                   )}
                 />
               </View>
             )}

             {/* Nearest Carpark Button */}
             <View style={{ paddingHorizontal: 16 }}>
               <NearestCarparkButton
                 origin={origin}
                 destination={{ latitude: place.latitude, longitude: place.longitude }}
                 destText={place.name}
                 onPress={() => {
                   if (!origin) {
                     Alert.alert("Location not ready", "Still getting your current location.");
                     return;
                   }
                   navigation.navigate("TransportDetails", {
                     origin,
                     destination: place.name,
                     coordinates: { latitude: place.latitude, longitude: place.longitude },
                     mode: "Driving",
                     findCarpark: true,
                   });
                 }}
               />
             </View>

             {gettingLoc && (
               <View style={{ paddingHorizontal: 16, marginTop: 8 }}>
                 <Text style={styles.muted}>Getting your current location…</Text>
               </View>
             )}
           </View>
         )}
         keyExtractor={(item) => item.key}
         showsVerticalScrollIndicator={true}
       />
     </Animated.View>
   </View>
 );
}





